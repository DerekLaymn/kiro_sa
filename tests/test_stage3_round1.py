"""Stage 3 round 1 (campaign/day2-p1): bytes-literal normalisation, ASSERT-TYPE-LITERAL-RETENTION,
MYPY-FIRST-ASSIGNMENT-TYPE and the multi-name ANNOTATION-ONLY-READ."""

from __future__ import annotations

from typediff.kb import BY_ID, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState
from typediff.typenorm import Relation, is_literal_retention, normalize, relation


def dg(tool, line, code, msg="m", rev=None, sev=Severity.ERROR):
    return Diagnostic(tool, line, 1, sev, code, msg, revealed_type=rev)


def state(src, diags, runtime=None):
    return CaseState("t", src, "3.13", {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [], **diags},
                     runtime or RuntimeResult(status="success"), [], {}, {})


def disc(kind, line, mypy=(), ty=(), pyright=(), end=None):
    return Discrepancy("D1", kind, line, end or line, "s", "", mypy=list(mypy), ty=list(ty), pyright=list(pyright))


def ids(st, d):
    return {e.id for e in matching_entries(st, d)}


# ---------------------------------------------------------------- typenorm: bytes literals


def test_bytes_literal_quote_style_is_cosmetic():
    a = normalize("Literal[b'abc']")
    b = normalize('Literal[b"abc"]')
    assert a.comparable and b.comparable
    assert a.text == b.text == 'Literal[b"abc"]'
    assert relation(a, b) in (Relation.EQUAL, Relation.COSMETIC)


def test_bytes_literal_union_mixed_with_int_literal():
    m = normalize("Literal[b'a'] | Literal[97]")
    t = normalize('Literal[b"a", 97]')
    assert relation(m, t) in (Relation.EQUAL, Relation.COSMETIC)


def test_different_bytes_literals_still_differ():
    assert relation(normalize("Literal[b'a']"), normalize('Literal[b"b"]')) == Relation.DIFFERENT
    assert relation(normalize("Literal[b'a']"), normalize('Literal["a"]')) == Relation.DIFFERENT


# ---------------------------------------------------------------- typenorm: literal retention


def test_literal_retention_is_one_sided_and_nested():
    ok = [("tuple[Literal[0]] | tuple[Literal['x']]", "tuple[int] | tuple[str]"),
          ("Literal[True]", "bool"), ("slice[Literal[1234], Any, Any]", "slice[int, Any, Any]"),
          ("list[tuple[Literal['', 'b']]]", "list[tuple[str]]"), ("Literal[Color.RED]", "Color")]
    for a, b in ok:
        assert is_literal_retention(normalize(a), normalize(b)), (a, b)
        assert is_literal_retention(normalize(b), normalize(a)), (b, a)


def test_literal_retention_rejects_narrowing_and_unrelated_types():
    bad = [("Literal[10, 20, 30]", "Literal[10, 30]"),  # narrowing: widens to int on both sides
           ("Literal[1]", "str"), ("Literal[1]", "bool"), ("tuple[Literal[1]]", "tuple[int, int]"),
           ("int", "int"), ("list[int]", "list[str]"), ("Literal[1] | None", "int")]
    for a, b in bad:
        assert not is_literal_retention(normalize(a), normalize(b)), (a, b)


# ---------------------------------------------------------------- ASSERT-TYPE-LITERAL-RETENTION

TY_MSG = "Type `{}` does not match asserted type `{}`"
MYPY_MSG = 'Expression is of type "{}", not "{}"'
ASSERT_SRC = "from typing import assert_type\nvalue = ((\"a\",),)[0][0]\nassert_type(value, str)\n"


def ty_assert(src, line, actual, asserted, code="type-assertion-failure"):
    t = dg(Tool.TY, line, code, TY_MSG.format(actual, asserted))
    return state(src, {Tool.TY: [t]}), disc(K.ONLY_TY, line, ty=[t])


def mypy_assert(src, line, actual, asserted):
    m = dg(Tool.MYPY, line, "assert-type", MYPY_MSG.format(actual, asserted))
    return state(src, {Tool.MYPY: [m]}), disc(K.ONLY_MYPY, line, mypy=[m])


def test_assert_type_retention_ty_side():
    assert "ASSERT-TYPE-LITERAL-RETENTION" in ids(*ty_assert(ASSERT_SRC, 3, 'Literal["a"]', "str"))
    assert "ASSERT-TYPE-LITERAL-RETENTION" in ids(*ty_assert(
        "from typing import assert_type\nx = (1, 2) < (3, 4)\nassert_type(x < x, bool)\n", 3, "Literal[True]", "bool"))


def test_assert_type_retention_mypy_side():
    src = "from typing import Literal, assert_type\nt = (1,)\nassert_type(t, tuple[Literal[1]])\n"
    assert "ASSERT-TYPE-LITERAL-RETENTION" in ids(*mypy_assert(src, 3, "tuple[int]", "tuple[Literal[1]]"))


def test_assert_type_retention_negatives():
    # different type, not literal retention
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert(ASSERT_SRC, 3, "int", "str"))
    # narrowing: neither side is the other's widening
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert(ASSERT_SRC, 3, "Literal[10, 20, 30]", "Literal[10, 30]"))
    # a diagnostic that is not an assert_type failure
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert(ASSERT_SRC, 3, 'Literal["a"]', "str", code="invalid-assignment"))
    # a declared name: a tool that ignores a declared type is a real bug, not literal retention
    src = "from typing import assert_type\ndef f(x: str) -> None:\n    assert_type(x, str)\n"
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert(src, 3, 'Literal["a"]', "str"))
    # a spec narrowing construct around the call
    src = "from typing import assert_type\ndef f(v):\n    if isinstance(v, str):\n        assert_type(v, str)\n"
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert(src, 4, 'Literal["a"]', "str"))
    # a statement that is no assert_type call at all
    assert "ASSERT-TYPE-LITERAL-RETENTION" not in ids(*ty_assert("x = 1\n", 1, "Literal[1]", "int"))


def test_assert_type_retention_runtime_exception_keeps_it_in_review():
    from typediff.kb import entry_demotion

    st, d = ty_assert(ASSERT_SRC, 3, 'Literal["a"]', "str")
    st.runtime = RuntimeResult(status="exception", exc_type="TypeError", exc_message="boom", exc_line=3, frames=[(3, "<module>")])
    e = BY_ID["ASSERT-TYPE-LITERAL-RETENTION"]
    assert e.auto and e.runtime_override
    assert entry_demotion(st, d, e) is not None


# ---------------------------------------------------------------- MYPY-FIRST-ASSIGNMENT-TYPE

ASSIGN_MSG = 'Incompatible types in assignment (expression has type "str", variable has type "int")'


def first_assign(src, line, msg=ASSIGN_MSG, pyright=False):
    m = dg(Tool.MYPY, line, "assignment", msg)
    p = [dg(Tool.PYRIGHT, line, "reportAssignmentType", "x")] if pyright else []
    return state(src, {Tool.MYPY: [m], Tool.PYRIGHT: p}), disc(K.ONLY_MYPY, line, mypy=[m])


def test_first_assignment_positive_and_verify_gated():
    for src, line in [("x = 1\nx = 's'\n", 2),
                      ("def f(flag: bool) -> None:\n    y = 1\n    if flag:\n        y = 's'\n    print(y)\n", 4),
                      ("x = 1\nx /= 2\n", 2),
                      ("for i in range(3):\n    pass\ni = 's'\n", 3)]:
        assert "MYPY-FIRST-ASSIGNMENT-TYPE" in ids(*first_assign(src, line)), src
    e = BY_ID["MYPY-FIRST-ASSIGNMENT-TYPE"]
    assert e.auto and e.verify is not None and e.verify.expects(None)["flags"] == ["--allow-redefinition"]


def test_first_assignment_negatives():
    cases = [
        ("x: int = 1\nx = 's'\n", 2),  # declared at module level
        ("def f(a: int) -> None:\n    a = 's'\n", 2),  # annotated parameter
        ("def f() -> None:\n    x: int = 1\n    x = 's'\n", 3),  # declared in function
        ("x = 1\n\n\ndef x() -> None: ...\n", 1),  # def binding of the same name is not an inferred variable
        ("class A:\n    z = 1\n\na = A()\na.z = 's'\n", 5),  # attribute target
        ("import os\nos = 's'\n", 2),  # import binding
    ]
    for src, line in cases:
        assert "MYPY-FIRST-ASSIGNMENT-TYPE" not in ids(*first_assign(src, line)), src
    # pyright objects too: not a mypy-only rule
    assert "MYPY-FIRST-ASSIGNMENT-TYPE" not in ids(*first_assign("x = 1\nx = 's'\n", 2, pyright=True))
    # a base-class assignment mismatch is a different diagnostic
    msg = 'Incompatible types in assignment (expression has type "str", base class "A" defined the type as "int")'
    assert "MYPY-FIRST-ASSIGNMENT-TYPE" not in ids(*first_assign("x = 1\nx = 's'\n", 2, msg=msg))
    # other mypy code on the statement
    m = dg(Tool.MYPY, 2, "arg-type", "Argument 1 has incompatible type")
    assert "MYPY-FIRST-ASSIGNMENT-TYPE" not in ids(state("x = 1\nx = 's'\n", {Tool.MYPY: [m]}), disc(K.ONLY_MYPY, 2, mypy=[m]))


# ---------------------------------------------------------------- ANNOTATION-ONLY-READ with several names

D_C_SRC = "from typing import Callable\nD_C: Callable[[int], int]\nA_C: Callable[[int], int]\nprint(D_C, A_C)\n"


def multi(src, line, names, pyright_names=None):
    t = [dg(Tool.TY, line, "unresolved-reference", f"Name `{n}` used when not defined") for n in names]
    p = [dg(Tool.PYRIGHT, line, "reportUnboundVariable", f'"{n}" is unbound') for n in (pyright_names or names)]
    return state(src, {Tool.TY: t, Tool.PYRIGHT: p}), disc(K.ONLY_TY, line, ty=t, pyright=p)


def test_annotation_only_read_several_names_all_declared_only():
    assert "ANNOTATION-ONLY-READ" in ids(*multi(D_C_SRC, 4, ["D_C", "A_C"]))
    assert "ANNOTATION-ONLY-READ" in ids(*multi("x: int\nprint(x, x)\n", 2, ["x", "x"]))


def test_annotation_only_read_several_names_negatives():
    # one of the names is assigned: its flagged use is a different problem
    src = "x: int\ny: int\ny = 1\nprint(x, y)\n"
    assert "ANNOTATION-ONLY-READ" not in ids(*multi(src, 4, ["x", "y"]))
    # one of the names is a forward reference to a class
    src = "x: int\nprint(x, A)\nclass A: ...\n"
    assert "ANNOTATION-ONLY-READ" not in ids(*multi(src, 2, ["x", "A"]))
    # pyright does not name every ty-flagged name
    assert "ANNOTATION-ONLY-READ" not in ids(*multi(D_C_SRC, 4, ["D_C", "A_C"], pyright_names=["D_C"]))
