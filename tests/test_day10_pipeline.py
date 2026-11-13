"""Day 10 phase 1: pipeline fix for the first weakness of results/days/day9-report.md section 7.

* W1  ty's ``warning[deprecated]`` on ``@contextmanager`` with ``-> Iterator[..]`` (and ``@asynccontextmanager`` with
      ``-> AsyncIterator[..]``) was 25 of the 224 live Day-9 findings. The stub marks the Iterator overload deprecated; the
      stubs of mypy 2.4.0 do not, so the difference is the typeshed snapshot. KB entry
      ``TY-CONTEXTMANAGER-ITERATOR-DEPRECATED`` (matcher ``m_contextmanager_iterator_deprecated``).

Every positive has near-miss controls that must stay live."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typediff.kb import BY_ID, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState

BIN = Path(sys.executable).parent
needs_tools = pytest.mark.skipif(not ((BIN / "mypy").exists() and (BIN / "ty").exists()), reason="mypy/ty not installed")

EID = "TY-CONTEXTMANAGER-ITERATOR-DEPRECATED"
CM_MSG = ("The overload of `contextmanager` is deprecated: Annotating the return type as `-> Iterator[Foo]` with "
          "`@contextmanager` is deprecated. Use `-> Generator[Foo]` instead.")
ACM_MSG = ("The overload of `asynccontextmanager` is deprecated: Annotating the return type as `-> AsyncIterator[Foo]` with "
           "`@asynccontextmanager` is deprecated. Use `-> AsyncGenerator[Foo]` instead.")


def hit(source: str, deco_line_text: str, msgs=(CM_MSG,), *, kind=K.ONLY_TY, line_offset=0, extra=(), code="deprecated") -> bool:
    """Does the entry fire? ``deco_line_text`` is the decorator line ty reports on (as in the real Day-9 rows, where the
    discrepancy is anchored at the decorator and its statement is the ``def`` below it)."""
    ln = next(i for i, x in enumerate(source.splitlines(), 1) if deco_line_text in x) + line_offset
    ty = [Diagnostic(Tool.TY, ln, 2, Severity.WARNING, code, m) for m in msgs]
    ty += [Diagnostic(Tool.TY, ln, 2, Severity.ERROR, c, m) for c, m in extra]
    d = Discrepancy("D1", kind, ln, ln + 1, "def f():", "<module>", mypy=[], ty=ty, pyright=[])
    st = CaseState("t", source, "3.13", {Tool.MYPY: [], Tool.TY: ty, Tool.PYRIGHT: []},
                   RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return EID in {e.id for e in matching_entries(st, d)}


HEAD = "import contextlib\nimport typing\nimport collections.abc\nfrom collections.abc import AsyncIterator, Generator, Iterator\n"
HEAD += "from contextlib import asynccontextmanager, contextmanager\n\n\n"


# ------------------------------------------------------------------------------------------------ positives
@pytest.mark.parametrize("name,body,deco,msg", [
    ("plain", "@contextmanager\ndef f() -> Iterator[int]:\n    yield 1\n", "@contextmanager", CM_MSG),
    ("module attribute decorator", "@contextlib.contextmanager\ndef f() -> Iterator[None]:\n    yield\n", "@contextlib.contextmanager", CM_MSG),
    ("typing.Iterator", "@contextmanager\ndef f() -> typing.Iterator[int]:\n    yield 1\n", "@contextmanager", CM_MSG),
    ("collections.abc.Iterator", "@contextmanager\ndef f() -> collections.abc.Iterator[str]:\n    yield 'a'\n", "@contextmanager", CM_MSG),
    ("quoted annotation", "@contextmanager\ndef f() -> 'Iterator[int]':\n    yield 1\n", "@contextmanager", CM_MSG),
    ("with parameters", "@contextmanager\ndef f(tag: str, n: int = 1) -> Iterator[list[str]]:\n    yield [tag] * n\n", "@contextmanager", CM_MSG),
    ("method", "class K:\n    @contextmanager\n    def f(self) -> Iterator[int]:\n        yield 1\n", "@contextmanager", CM_MSG),
    ("stacked below another decorator", "class K:\n    @staticmethod\n    @contextmanager\n    def f() -> Iterator[int]:\n        yield 1\n",
     "@contextmanager", CM_MSG),
    ("asynccontextmanager", "@asynccontextmanager\nasync def f() -> AsyncIterator[int]:\n    yield 1\n", "@asynccontextmanager", ACM_MSG),
    ("asynccontextmanager, module attribute", "@contextlib.asynccontextmanager\nasync def f() -> collections.abc.AsyncIterator[int]:\n    yield 1\n",
     "@contextlib.asynccontextmanager", ACM_MSG),
])
def test_iterator_overload_deprecation_is_closed(name, body, deco, msg):
    assert hit(HEAD + body, deco, (msg,)), name


def test_two_identical_warnings_on_one_statement_are_closed():
    body = "@contextmanager\ndef f() -> Iterator[int]:\n    yield 1\n"
    assert hit(HEAD + body, "@contextmanager", (CM_MSG, CM_MSG))


# ------------------------------------------------------------------------------------------------ controls (stay live)
ITER = HEAD + "@contextmanager\ndef f() -> Iterator[int]:\n    yield 1\n"


def test_generator_annotation_is_not_the_deprecated_overload():
    src = HEAD + "@contextmanager\ndef f() -> Generator[int]:\n    yield 1\n"
    assert not hit(src, "@contextmanager")


def test_message_naming_the_other_decorator_stays_live():
    assert not hit(ITER, "@contextmanager", (ACM_MSG,))
    src = HEAD + "@asynccontextmanager\nasync def f() -> AsyncIterator[int]:\n    yield 1\n"
    assert not hit(src, "@asynccontextmanager", (CM_MSG,))


def test_iterator_family_must_match_the_decorator():
    # contextmanager with an AsyncIterator annotation, asynccontextmanager with an Iterator one: not the stub's pairs
    assert not hit(HEAD + "@contextmanager\ndef f() -> AsyncIterator[int]:\n    yield 1\n", "@contextmanager")
    assert not hit(HEAD + "@asynccontextmanager\nasync def f() -> Iterator[int]:\n    yield 1\n", "@asynccontextmanager", (ACM_MSG,))


@pytest.mark.parametrize("msg", [
    "`old` is deprecated",
    "The function `old` is deprecated: use `new`",
    CM_MSG + " See also elsewhere.",
    CM_MSG.replace("Iterator[Foo]", "Iterable[Foo]"),
    CM_MSG.replace("Use `-> Generator[Foo]` instead.", "Use something else."),
    CM_MSG.replace("overload of", "function"),
])
def test_other_deprecation_messages_stay_live(msg):
    assert not hit(ITER, "@contextmanager", (msg,))


def test_another_ty_diagnostic_next_to_the_warning_keeps_it_live():
    assert not hit(ITER, "@contextmanager", (CM_MSG,), extra=[("invalid-return-type", "Return type does not match")])


def test_a_different_rule_code_stays_live():
    assert not hit(ITER, "@contextmanager", (CM_MSG,), code="invalid-argument-type")


def test_warning_not_on_the_decorator_line_stays_live():
    # reported on the `def` line: not the decorator ty names
    assert not hit(ITER, "@contextmanager", line_offset=1)


def test_no_decorator_or_other_decorator_stays_live():
    assert not hit(HEAD + "def f() -> Iterator[int]:\n    yield 1\n", "def f()")
    assert not hit(HEAD + "@staticmethod\ndef f() -> Iterator[int]:\n    yield 1\n", "@staticmethod")


def test_missing_or_non_subscript_annotation_stays_live():
    assert not hit(HEAD + "@contextmanager\ndef f():\n    yield 1\n", "@contextmanager")
    assert not hit(HEAD + "@contextmanager\ndef f() -> Iterator:\n    yield 1\n", "@contextmanager")
    assert not hit(HEAD + "@contextmanager\ndef f() -> 'Iterator[':\n    yield 1\n", "@contextmanager")


def test_statement_that_is_no_function_stays_live():
    src = HEAD + "@contextmanager\nclass C:\n    pass\n"
    assert not hit(src, "@contextmanager")


@pytest.mark.parametrize("kind", [K.ONLY_MYPY, K.REVEAL_MISMATCH, K.CONCERN_MISMATCH])
def test_other_discrepancy_kinds_are_not_closed(kind):
    assert not hit(ITER, "@contextmanager", kind=kind)


def test_entry_is_a_non_runtime_overriding_auto_dismissal_without_selftest_example():
    e = BY_ID[EID]
    assert e.auto and e.verify is None and e.runtime_override is False and e.kinds == (K.ONLY_TY,)
    assert e.dismissal.value == "CONFIG_ARTIFACT" and e.example == ""  # kb-selftest count stays at 20


# ------------------------------------------------------------------------------------------------ real tools
REAL_ITER = '''\
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def tagged(tag: str) -> Iterator[str]:
    print("enter", tag)
    try:
        yield tag
    finally:
        print("exit", tag)


with tagged("a") as t:
    print(t)
'''

REAL_ASYNC = '''\
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def tagged(tag: str) -> AsyncIterator[str]:
    yield tag


async def main() -> None:
    async with tagged("a") as t:
        print(t)


asyncio.run(main())
'''

# a user-level @deprecated function: another `deprecated` diagnostic, with its own wording, that this entry must not close
REAL_OTHER = '''\
from warnings import deprecated


@deprecated("use new")
def old() -> int:
    return 1


print(old())
'''


def _pipeline():
    from typediff.llm import CachedLLM, NullLLM
    from typediff.pipeline import Pipeline, PipelineConfig

    return Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))


@needs_tools
@pytest.mark.parametrize("src", [REAL_ITER, REAL_ASYNC], ids=["contextmanager", "asynccontextmanager"])
def test_real_tools_iterator_overload_warning_is_dismissed(src):
    from typediff.models import Tier

    rep = _pipeline().run_source(src, "day10-cm-iterator")
    dep = [f for f in rep.findings if f.decided_by == f"kb:{EID}"]
    assert dep and all(f.tier == Tier.DISMISSED and f.dismissal.value == "CONFIG_ARTIFACT" for f in dep)
    assert not [f for f in rep.findings if f.tier != Tier.DISMISSED], [(f.decided_by, f.tier) for f in rep.findings]


@needs_tools
def test_real_tools_other_deprecated_diagnostic_is_not_closed_by_this_entry():
    rep = _pipeline().run_source(REAL_OTHER, "day10-other-deprecated")
    assert not [f for f in rep.findings if f.decided_by == f"kb:{EID}"]
