"""Day 9 phase 1: pipeline changes (results/days/day9-report.md).

* W1  a quoted ``'Self'`` annotation is read as ``Self`` (`selfparam.mentions_self`), so TY-SELF-UPPER-BOUND and its
      spec-desugar probe cover ``def add(self, c: 'Self')`` (Day-8 weakness: 2 live findings of ``3a63c673``, a ty#4656
      duplicate).
* W2  TY-2792-READONLY also covers a statement in a function that is DEFINED after the stale-narrowing chain (Day-8
      weakness: D8-2, ``try_write(c)`` below module-level asserts around ``c.bump()``).
* Operators with their own instruction (`typediff/operators.py`) and the two new feature areas.

Every positive has near-miss controls that must stay live."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

from test_phase3 import SELF_SRC, FakeRunners, self_case
from test_upstream_day6 import ids
from test_upstream_day7 import CLASS_T, RO_MYPY
from typediff import prompts
from typediff.cli import main
from typediff.experiments import ExperimentRunner, self_call_plan
from typediff.kb import BY_ID, matching_entries
from typediff.models import DiscrepancyKind as K
from typediff.operators import OPERATORS, mutation_spec
from typediff.selfparam import has_self_typed_state, mentions_self, parse_string_annotation
from typediff.strategy import AREAS

BIN = Path(sys.executable).parent
needs_tools = pytest.mark.skipif(not ((BIN / "mypy").exists() and (BIN / "ty").exists()), reason="mypy/ty not installed")

QUOTED_SRC = SELF_SRC.replace("c: Self) -> Self", "c: 'Self') -> 'Self'")
assert QUOTED_SRC != SELF_SRC


# ------------------------------------------------------------------------------------------------ W1: quoted Self


def ann(text: str) -> ast.expr:
    return ast.parse(text, mode="eval").body


@pytest.mark.parametrize("text", [
    "'Self'", '"Self"', "'Self | None'", "list['Self']", "'list[Self]'", "dict[str, 'Self']", "typing.Self", "'typing.Self'",
    "' Self '", "Annotated['Self', 'meta']",
])
def test_quoted_and_plain_self_annotations_are_read_as_self(text):
    assert mentions_self(ann(text)), text


@pytest.mark.parametrize("text", [
    "int", "'int'", "'Selfish'", "'Self ('", "Literal['Self']", "typing.Literal['Self']", "Annotated[int, 'Self']",
    "list[Literal['Self']]", "''", "'1 +'",
])
def test_controls_that_only_look_like_self(text):
    assert not mentions_self(ann(text)), text


def test_mentions_self_handles_none_and_parse_helper():
    assert not mentions_self(None)
    assert parse_string_annotation(ann("'list[int]'")) is not None
    assert parse_string_annotation(ann("'(('")) is None  # not an expression
    assert parse_string_annotation(ann("3")) is None  # not a string


def test_self_typed_state_includes_quoted_annotations():
    pre = "from typing import Self\n"
    assert has_self_typed_state(ast.parse(pre + "class A:\n    nxt: 'Self | None' = None\n"))
    assert has_self_typed_state(ast.parse(pre + "class A:\n    def __init__(self) -> None:\n        self.kids: list['Self'] = []\n"))
    assert not has_self_typed_state(ast.parse(pre + "class A:\n    nxt: 'int | None' = None\n"))


def test_quoted_self_parameter_is_the_ty4656_pattern():
    st, d = self_case(QUOTED_SRC, runners=FakeRunners())
    plan = self_call_plan(st, d)
    assert plan is not None and (plan.method, plan.defining, plan.receiver) == ("add", "Node", "Leaf")
    assert BY_ID["TY-SELF-UPPER-BOUND"] in matching_entries(st, d)


def test_quoted_self_controls_do_not_match():
    literal = QUOTED_SRC.replace("c: 'Self'", "c: Literal['Self']").replace("from typing import Self", "from typing import Literal, Self")
    st, d = self_case(literal, runners=FakeRunners())
    assert self_call_plan(st, d) is None
    plain = QUOTED_SRC.replace("c: 'Self'", "c: 'Node'")  # a quoted class name is not Self
    st, d = self_case(plain, runners=FakeRunners())
    assert self_call_plan(st, d) is None


def test_desugar_rewrites_a_quoted_self_inside_the_string():
    st, d = self_case(QUOTED_SRC, runners=FakeRunners())
    res = ExperimentRunner(st).spec_desugar(d, {"kind": "spec_desugar"})
    assert res.ok and res.outcome["unchanged"] is True
    variant = res.outcome["variant_source"]
    assert "c: '_TdSelf_Node'" in variant and "self: _TdSelf_Node" in variant and "-> '_TdSelf_Node'" in variant
    assert "Self'" not in variant.replace("_TdSelf_Node'", "")  # no quoted Self is left over


def test_desugar_keeps_literal_strings_and_rewrites_nested_quoted_self():
    src = QUOTED_SRC.replace("c: 'Self') -> 'Self'", "c: 'list[Self]', tag: Literal['Self'] = 'Self') -> 'Self'").replace(
        "from typing import Self", "from typing import Literal, Self")
    st, d = self_case(src, runners=FakeRunners())
    res = ExperimentRunner(st).spec_desugar(d, {"kind": "spec_desugar", "class": "Node"})
    assert res.ok
    variant = res.outcome["variant_source"]
    assert "c: 'list[_TdSelf_Node]'" in variant and "Literal['Self']" in variant


def test_desugar_still_refuses_a_string_that_is_no_expression():
    src = QUOTED_SRC.replace("c: 'Self'", "c: 'Self ('")
    st, d = self_case(src, runners=FakeRunners())
    res = ExperimentRunner(st).run(d, {"kind": "spec_desugar", "class": "Node"})
    assert not res.ok and res.evidence is None


@needs_tools
def test_real_tools_quoted_self_example_is_dismissed_by_the_entry():
    from typediff.llm import CachedLLM, NullLLM
    from typediff.models import Tier
    from typediff.pipeline import Pipeline, PipelineConfig

    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
    plain = p.run_source(BY_ID["TY-SELF-UPPER-BOUND"].example, "kb-self-plain")
    quoted = p.run_source(BY_ID["TY-SELF-UPPER-BOUND"].example.replace("c: Self) -> Self", "c: 'Self') -> 'Self'"), "kb-self-quoted")
    for rep in (plain, quoted):
        assert rep.findings and all(f.tier == Tier.DISMISSED and f.decided_by == "kb:TY-SELF-UPPER-BOUND" for f in rep.findings)


# ------------------------------------------------------------------------------------------------ W2: def below the chain

CHAIN = "t = T(4)\nassert t.ro == 4\nt.bump()\nassert t.ro == 5\n"


def nested_ids(src_tail: str, stmt: str, mypy=RO_MYPY):
    return {i for i in ids(CLASS_T + src_tail, stmt, K.ONLY_MYPY, mypy=mypy) if "2792" in i}


@pytest.mark.parametrize("name,tail,stmt", [
    ("module chain, function below (the D8-2 program)", CHAIN + "def g(u: T) -> bool:\n    u.ro = 0\n    return True\n", "u.ro = 0"),
    ("function parameter has the same name as the chain's receiver", CHAIN + "def g(t: T) -> None:\n    t.ro = 0\n", "t.ro = 0"),
    ("decorated function", CHAIN + "@staticmethod\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("statement in try inside the function", CHAIN + "def g(u: T) -> None:\n    try:\n        u.ro = 0\n    except AttributeError:\n        pass\n", "u.ro = 0"),
    ("two function levels", CHAIN + "def g(u: T) -> None:\n    def h(w: T) -> None:\n        w.ro = 0\n    h(u)\n", "w.ro = 0"),
    ("chain in the outer function, inner def below",
     "def outer(t: T) -> None:\n    assert t.ro == 4\n    t.bump()\n    assert t.ro == 5\n\n    def h(w: T) -> None:\n        w.ro = 0\n    h(t)\n", "w.ro = 0"),
])
def test_readonly_property_in_a_function_defined_after_the_chain(name, tail, stmt):
    assert nested_ids(tail, stmt) == {"UPSTREAM-TY-2792-READONLY"}, name


@pytest.mark.parametrize("name,tail,stmt", [
    ("function defined BEFORE the chain", "def g(u: T) -> None:\n    u.ro = 0\n\n\n" + CHAIN, "u.ro = 0"),
    ("chain inside a sibling function", "def a(t: T) -> None:\n    assert t.ro == 4\n    t.bump()\n    assert t.ro == 5\n\n\n"
     "def g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("no method call", "t = T(4)\nassert t.ro == 4\nassert t.ro == 5\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("call placed before the narrowing", "t = T(4)\nt.bump()\nassert t.ro == 4\nassert t.ro == 5\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("no read after the call", "t = T(4)\nassert t.ro == 4\nt.bump()\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("property with a setter", CHAIN + "def g(u: T) -> None:\n    u.rw = 0\n", "u.rw = 0"),
    ("receiver rebound after the call", "t = T(4)\nassert t.ro == 4\nt.bump()\nt = T(1)\nassert t.ro == 5\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("direct store resets the narrowing", "t = T(4)\nassert t.n == 4\nt.bump()\nt.n = 7\nassert t.n == 7\ndef g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
    ("not a property", CHAIN + "def g(u: T) -> None:\n    u.zzz = 0\n", "u.zzz = 0"),
    ("statement is a method's body, chain only inside a class body of another class",
     "class Other:\n    def m(self, t: T) -> None:\n        assert t.ro == 4\n        t.bump()\n        assert t.ro == 5\n\n\n"
     "def g(u: T) -> None:\n    u.ro = 0\n", "u.ro = 0"),
])
def test_readonly_property_nested_controls_stay_live(name, tail, stmt):
    assert not nested_ids(tail, stmt), name


def test_readonly_property_nested_other_messages_stay_live():
    tail = CHAIN + "def g(u: T) -> None:\n    u.ro = 0\n"
    assert not nested_ids(tail, "u.ro = 0", mypy=[("misc", "Cannot assign to a method")])
    assert not nested_ids(tail, "u.ro = 0", mypy=[("assignment", 'Property "ro" defined in "T" is read-only')])


# ------------------------------------------------------------------------------------------------ operators and areas


def test_new_operators_have_instructions_and_old_ones_stay_bare():
    assert set(OPERATORS) == {"dunder_instance_shadow", "exit_swallow_flip"}
    for op in OPERATORS:
        spec = mutation_spec(op)
        assert spec["operator"] == op and len(spec["instruction"]) > 200
        assert op in prompts.STRATEGIST_SYSTEM
    for op in ("feature_crossover", "runtime_witness", "narrowing_construct_swap", "not_an_operator"):
        assert mutation_spec(op) == {"operator": op}
    assert mutation_spec(" exit_swallow_flip ")["operator"] == "exit_swallow_flip"


def test_new_operator_instructions_name_the_runtime_oracle():
    assert "TypeError" in OPERATORS["dunder_instance_shadow"] and "# expect-error" in OPERATORS["dunder_instance_shadow"]
    assert "__exit__" in OPERATORS["exit_swallow_flip"] and "reveal_type" in OPERATORS["exit_swallow_flip"]


def test_new_areas_are_registered_with_descriptions():
    assert {"dunder_dispatch", "context_managers"} <= set(AREAS)
    assert "special methods" in AREAS["dunder_dispatch"] and "__exit__" in AREAS["context_managers"]


def _prompts(tmp_path, ops: str, area="dunder_dispatch", n=1):
    seeds = tmp_path / "seeds"
    seeds.mkdir(exist_ok=True)
    (seeds / "s.py").write_text(f"# area: {area}\n# hypothesis: x\nx: int = 1\n")
    inbox, out = tmp_path / "inbox", tmp_path / "out"
    argv = ["--python-version", "3.13", "--llm", f"file:{inbox}", "generate", "--from-seeds", str(seeds), "--out-dir", str(out),
            "--n", str(n)]
    if ops:
        argv += ["--ops", ops]
    assert main(argv) == 0
    return [p.read_text() for p in sorted(inbox.glob("*.prompt.md"))]


def test_generate_puts_the_instruction_of_a_new_operator_into_the_prompt(tmp_path):
    (body,) = _prompts(tmp_path, "dunder_instance_shadow")
    assert "'operator': 'dunder_instance_shadow'" in body and "'instruction': " in body
    assert "CPython looks special methods up on the type" in body
    assert "Feature area: dunder_dispatch" in body


def test_generate_prompt_of_an_old_operator_is_unchanged(tmp_path):
    (body,) = _prompts(tmp_path, "feature_crossover", area="gradual_any")
    user = prompts.GENERATOR_USER.format(area="gradual_any", brief="x", mutations=[{"operator": "feature_crossover"}],
                                         previous="# area: gradual_any\n# hypothesis: x\nx: int = 1\n")
    assert user in body and "instruction" not in body


def test_generate_without_area_covers_the_new_areas(tmp_path):
    inbox, out = tmp_path / "inbox", tmp_path / "out"
    assert main(["--python-version", "3.13", "--llm", f"file:{inbox}", "generate", "--area", "context_managers", "--out-dir", str(out),
                 "--n", "2", "--ops", "exit_swallow_flip"]) == 0
    bodies = [p.read_text() for p in sorted(inbox.glob("*.prompt.md"))]
    assert len(bodies) == 2 and all("Feature area: context_managers" in b and "exit_swallow_flip" in b for b in bodies)
    for p in inbox.glob("*.prompt.md"):  # the bridge keeps working with an answer
        (inbox / f"{p.name.split('.')[0]}.answer.json").write_text(json.dumps({"source": "y: int = 1\n", "hypothesis": "h"}))
    assert main(["--python-version", "3.13", "--llm", f"file:{inbox}", "generate", "--area", "context_managers", "--out-dir", str(out),
                 "--n", "2", "--ops", "exit_swallow_flip"]) == 0
    assert len(list(out.rglob("*.py"))) == 2
