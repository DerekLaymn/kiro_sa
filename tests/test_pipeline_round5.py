"""Day 5 step 1: pipeline fixes.

1a  a crash is auto-closed only by a known_upstream crash entry, and the closing reference is recorded (``closed_by``);
    a same-signature record in the dataset no longer closes a crash.
1b  see tests/test_generate_variants.py (the 'Variant k of N' prompt line).
1c  the C1 `__call__` self-reference shapes (mutual pair, chain, ClassVar, subclass, union parameter) match TY-4148 and
    MYPY-22361 consistently; look-alike programs without a cycle or a call do not.
1d  inbox accounting: see tests/test_inbox_check_round5.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from typediff.crash_upstream import match_crash
from typediff.dataset import Dataset
from typediff.llm import CachedLLM, NullLLM
from typediff.models import Crash, Dismissal, RuntimeResult, Tier, Tool, Verdict
from typediff.pipeline import Pipeline
from typediff.state import CaseState

DATA = Path(__file__).parent / "data" / "upstream_round5"
DATA4 = Path(__file__).parent / "data" / "upstream_round4"
TY_SO = "ty:signal-SIGABRT:stack-overflow"
MYPY_SEGV = "mypy:signal-SIGSEGV"


def src(name: str, data: Path = DATA) -> str:
    return (data / f"{name}.py").read_text()


def closes(tool: str, sig: str, source: str) -> str | None:
    e = match_crash(source, tool, sig)
    return e["id"] if e else None


def judge(source: str, crash: Crash, dataset: Dataset | None = None):
    pipe = Pipeline(llm=CachedLLM(NullLLM()), dataset=dataset)
    st = CaseState("t", source, "3.13", {}, RuntimeResult(status="success"), [crash], {}, {})
    return pipe._judge(st)


TY_CRASH = Crash(Tool.TY, "signal", TY_SO, "", -6)
MYPY_CRASH = Crash(Tool.MYPY, "signal", MYPY_SEGV, "", -11)


# ------------------------------------------------------------------------------------------------ 1c: C1 shapes
C1_PROGRAMS = ["c1_mutual_chain_classvar", "c1_mutual_subclass_classvar", "c1_self_union_param", "c1_mutual_node_self"]


@pytest.mark.parametrize("name", C1_PROGRAMS)
def test_c1_shapes_close_with_both_entries(name):
    s = src(name)
    assert closes("ty", TY_SO, s) == "TY-4148"
    assert closes("mypy", MYPY_SEGV, s) == "MYPY-22361"


def test_mutual_pair_from_day4_data_now_matches():
    s = src("ty4148_mutual_pair", DATA4)
    assert closes("ty", TY_SO, s) == "TY-4148"
    assert closes("mypy", MYPY_SEGV, s) == "MYPY-22361"


CYCLE_BASE = "from typing import ClassVar, Optional, Self\n\n\n{classes}\n\n\n{use}\n"


@pytest.mark.parametrize("classes,use", [
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "A"', "A()()"),
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "C"\n\n\nclass C:\n    __call__: "A"', "def f(x: C) -> None:\n    x()"),
    ('class A:\n    __call__: "B | None"\n\n\nclass B:\n    __call__: "A | None"', "def f(x: B) -> None:\n    x()"),
    ('class C:\n    __call__: ClassVar["C"]', "C()()"),
    ('class C:\n    __call__: Optional[Self] = None', "C()()"),
    ('class C:\n    __call__: "C"\n\n\nclass Sub(C):\n    pass', "Sub()()"),
    ('class C:\n    __call__: "C"\n\n\nclass Sub(C):\n    pass', "def f(x: Sub) -> None:\n    x()"),
    ('class C:\n    __call__: "C"', "def f(x: C | int) -> None:\n    x()"),
    ('class C:\n    __call__: "C"', "def f(x: Optional[C]) -> None:\n    x()"),
])
def test_cycle_shapes_match(classes, use):
    s = CYCLE_BASE.format(classes=classes, use=use)
    assert closes("ty", TY_SO, s) == "TY-4148", s
    assert closes("mypy", MYPY_SEGV, s) == "MYPY-22361", s


@pytest.mark.parametrize("classes,use", [
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: int', "A()()"),  # chain ends in a non-callable: no cycle
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    pass', "A()()"),
    ('class C:\n    __call__: list["C"]', "C()()"),
    ('class C:\n    __call__: tuple[Self, ...] = ()', "C()()"),
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "A"', "x = A()"),  # declared and built, never called
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "A"', "def f(x: int) -> None:\n    x()"),  # call on another type
    ('class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "A"\n\n\nclass Z:\n    pass', "def f(x: Z) -> None:\n    x()"),
    ('class C:\n    def __call__(self) -> "C":\n        return self', "C()()"),  # method, not the attribute form
])
def test_look_alikes_do_not_match(classes, use):
    s = CYCLE_BASE.format(classes=classes, use=use)
    assert closes("ty", TY_SO, s) is None, s
    assert closes("mypy", MYPY_SEGV, s) is None, s


def test_other_stack_overflows_still_not_swallowed_by_the_wider_c1_matcher():
    assert closes("ty", TY_SO, src("ty4148_control_protocol_flatten_new_bug", DATA4)) is None
    assert closes("ty", TY_SO, "x = 1\n") is None


# ------------------------------------------------------------------------------------------------ 1a: auditable closure
def test_closure_records_the_closing_reference():
    f = judge(src("c1_mutual_chain_classvar"), TY_CRASH).findings[0]
    assert f.tier == Tier.DISMISSED and f.dismissal == Dismissal.DUPLICATE
    assert f.closed_by is not None
    assert f.closed_by.startswith("TY-4148 https://github.com/astral-sh/ty/issues/4148 ")
    assert f"signature={TY_SO}" in f.closed_by and "requires=call_attr_own_type" in f.closed_by
    assert any("DUPLICATE of https://github.com/astral-sh/ty/issues/4148 (TY-4148)" in n for n in f.review_notes)
    g = judge(src("c1_mutual_chain_classvar"), MYPY_CRASH).findings[0]
    assert g.closed_by is not None and g.closed_by.startswith("MYPY-22361 https://github.com/python/mypy/issues/22361 ")
    json.dumps(f.closed_by)  # plain string, serialisable into the report json


def test_unmatched_crash_stays_live_without_a_closing_reference():
    unfiled = src("ty4148_control_protocol_flatten_new_bug", DATA4)
    f = judge(unfiled, TY_CRASH).findings[0]
    assert f.verdict == Verdict.BUG and f.tier == Tier.CONFIRMED and f.dismissal is None and f.closed_by is None


def test_same_signature_in_the_dataset_does_not_close_a_crash(tmp_path):
    ds = Dataset(tmp_path / "ds.jsonl")
    unfiled = src("ty4148_control_protocol_flatten_new_bug", DATA4)
    first = judge(unfiled, TY_CRASH, ds)
    ds.add_case(first)  # records the live finding with this signature
    second = judge(unfiled.replace("flatten", "flatten2"), TY_CRASH, ds)
    f = second.findings[0]
    assert f.tier == Tier.CONFIRMED and f.dismissal is None, "same-signature shortcut must not close a crash"
    assert any(n.startswith("SAME-SIGNATURE-AS ") and "NOT closed" in n for n in f.review_notes)


def test_dataset_record_keeps_the_closing_reference(tmp_path):
    ds = Dataset(tmp_path / "ds.jsonl")
    rep = judge(src("c1_mutual_chain_classvar"), TY_CRASH, ds)
    ds.add_case(rep)
    rec = json.loads((tmp_path / "ds.jsonl").read_text().splitlines()[0])
    assert rec["tier"] == "dismissed" and rec["closed_by"].startswith("TY-4148 ")


# ------------------------------------------------------------------------------------------------ ty#4656 is not a bug
def test_ty4656_is_a_design_difference_not_a_bug_entry():
    from typediff import kb
    from typediff.crash_upstream import PATH

    raw = json.loads(PATH.read_text())
    assert not [e for e in raw["entries"] if "4656" in e["id"] or e.get("url", "").endswith("/ty/issues/4656")]
    prior = next(e for e in raw["prior_stances"] if e["id"] == "TY-4656")
    assert prior["stance"] == "intended" and "not a bug" in prior["note"]
    entry = kb.BY_ID["TY-SELF-UPPER-BOUND"]
    assert entry.dismissal == Dismissal.DESIGN_DIVERGENCE
