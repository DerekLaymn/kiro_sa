"""fixD: narrow KB entries (ANNOTATION-ONLY-READ, MYPY-15182-NEW-RETURNS, JOIN-VS-UNION-CALLABLE, MDTEST-TODO)."""

from __future__ import annotations

from typediff.kb import matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeProbe, RuntimeResult, Severity, Tool
from typediff.state import CaseState


def dg(tool, line, code, msg="m", rev=None):
    return Diagnostic(tool, line, 1, Severity.ERROR, code, msg, revealed_type=rev)


def state(src, diags, runtime=None):
    st = CaseState("t", src, "3.13", {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [], **diags},
                   runtime or RuntimeResult(status="success"), [], {}, {})
    return st


def ids(st, d):
    return {e.id for e in matching_entries(st, d)}


def disc(kind, line, mypy=(), ty=(), pyright=(), stmt="s"):
    return Discrepancy("D1", kind, line, line, stmt, "", mypy=list(mypy), ty=list(ty), pyright=list(pyright))


# ---------------------------------------------------------------- ANNOTATION-ONLY-READ

UNDEF = "Name `x` used when not defined"


def annonly(src, line, pyright=True):
    t = dg(Tool.TY, line, "unresolved-reference", UNDEF)
    p = dg(Tool.PYRIGHT, line, "reportUnboundVariable", '"x" is unbound')
    return state(src, {Tool.TY: [t], Tool.PYRIGHT: [p] if pyright else []}), disc(
        K.ONLY_TY, line, ty=[t], pyright=[p] if pyright else [])


def test_annotation_only_module_and_function_scope():
    st, d = annonly("x: int\nprint(x)\n", 2)
    assert "ANNOTATION-ONLY-READ" in ids(st, d)
    st, d = annonly("def f() -> None:\n    x: int\n    print(x)\n", 3)
    assert "ANNOTATION-ONLY-READ" in ids(st, d)


def test_annotation_only_not_matching():
    for src, line in [("x: int\nx = 1\nprint(x)\n", 3),  # assigned
                      ("def f(x: int) -> None:\n    x: int\n    print(x)\n", 3),  # parameter
                      ("print(x)\n", 1),  # truly undefined, no declaration
                      ("print(A)\nclass A: ...\nx: A\n", 1)]:  # forward reference
        st, d = annonly(src, line)
        assert "ANNOTATION-ONLY-READ" not in ids(st, d), src
    st, d = annonly("x: int\nprint(x)\n", 2, pyright=False)  # pyright must agree
    assert "ANNOTATION-ONLY-READ" not in ids(st, d)


# ---------------------------------------------------------------- MYPY-15182-NEW-RETURNS

NEW_SRC = ("class R:\n    def __new__(cls) -> int:\n        return 42\n\n\nreveal_type(R())\n")


def new_returns(ty_rev="int", pyright_rev="int", value="42", vtype="int", mypy_msg=None):
    msg = mypy_msg or 'Incompatible return type for "__new__" (returns "int", but must return a subtype of "R")'
    m = [dg(Tool.MYPY, 6, "misc", msg), dg(Tool.MYPY, 6, "misc", "Revealed", rev="R")]
    m[0].line = 2
    t, p = dg(Tool.TY, 6, "revealed-type", "x", rev=ty_rev), dg(Tool.PYRIGHT, 6, "reveal", "x", rev=pyright_rev)
    rt = RuntimeResult(status="success", probes=[RuntimeProbe(6, {"type": vtype, "mro": [vtype, "object"], "repr": value})])
    st = state(NEW_SRC, {Tool.MYPY: m, Tool.TY: [t], Tool.PYRIGHT: [p]}, rt)
    return st, disc(K.REVEAL_MISMATCH, 6, mypy=[m[1]], ty=[t], pyright=[p])


def test_new_returns_non_subtype_dismissed():
    st, d = new_returns()
    assert "MYPY-15182-NEW-RETURNS" in ids(st, d)


def test_new_returns_non_subtype_not_matching():
    for kw in ({"pyright_rev": "str"},  # pyright disagrees with ty
               {"value": "'a'", "vtype": "str"},  # CPython value does not inhabit ty's type
               {"mypy_msg": 'Incompatible return type for "foo" (returns "int", but must return a subtype of "R")'}):
        st, d = new_returns(**kw)
        assert "MYPY-15182-NEW-RETURNS" not in ids(st, d), kw


# ---------------------------------------------------------------- JOIN-VS-UNION-CALLABLE

JOIN_SRC = "class Base: ...\nclass Foo(Base): ...\nclass Bar(Base): ...\nreveal_type(j)\n"


def callable_join(mypy_rev="def () -> Base", ty_rev="<class 'Foo'> | <class 'Bar'>", py_rev="type[Foo] | type[Bar]"):
    m, t, p = (dg(Tool.MYPY, 4, "misc", "x", rev=mypy_rev), dg(Tool.TY, 4, "revealed-type", "x", rev=ty_rev),
               dg(Tool.PYRIGHT, 4, "reveal", "x", rev=py_rev))
    return state(JOIN_SRC, {Tool.MYPY: [m], Tool.TY: [t], Tool.PYRIGHT: [p]}), disc(
        K.REVEAL_MISMATCH, 4, mypy=[m], ty=[t], pyright=[p])


def test_callable_join_dismissed():
    st, d = callable_join()
    assert "JOIN-VS-UNION-CALLABLE" in ids(st, d)


def test_callable_join_not_matching():
    for kw in ({"mypy_rev": "def (x: int) -> Base"},  # not a nullary constructor join
               {"py_rev": "type[Foo] | type[Base]"},  # pyright disagrees with ty
               {"mypy_rev": "def () -> int"},  # int is not a source class / base
               {"ty_rev": "<class 'Foo'>", "py_rev": "type[Foo]"}):  # not a union
        st, d = callable_join(**kw)
        assert "JOIN-VS-UNION-CALLABLE" not in ids(st, d), kw


# ---------------------------------------------------------------- MDTEST-TODO

TODO_SRC = "def f(x: int) -> None: ...\n# TODO: should error: [missing-argument] once merged.\nf()\n"


def test_mdtest_todo():
    m = dg(Tool.MYPY, 3, "call-arg", "Missing positional argument")
    d = disc(K.ONLY_MYPY, 3, mypy=[m], stmt="f()")
    assert "MDTEST-TODO" in ids(state(TODO_SRC, {Tool.MYPY: [m]}), d)
    far = "# TODO: should error\n\n\n\n\nf()\n"
    d2 = disc(K.ONLY_MYPY, 6, mypy=[m], stmt="f()")
    assert "MDTEST-TODO" not in ids(state(far, {Tool.MYPY: [m]}), d2)  # more than 3 lines away
    plain = "# TODO: tidy up\nf()\n"
    assert "MDTEST-TODO" not in ids(state(plain, {Tool.MYPY: [m]}), disc(K.ONLY_MYPY, 2, mypy=[m], stmt="f()"))


# ---------------------------------------------------------------- the two live leads stay live

META_SRC = ("from typing import ClassVar\n\nclass Meta(type):\n    eggs: ClassVar[int] = 42\n\n"
            "class Foo(metaclass=Meta):\n    eggs: str\n\nreveal_type(Foo.eggs)\n")
FIXD = {"ANNOTATION-ONLY-READ", "MYPY-15182-NEW-RETURNS", "JOIN-VS-UNION-CALLABLE", "MDTEST-TODO"}


def test_lead_a_metaclass_classvar_not_dismissed():
    m, t, p = (dg(Tool.MYPY, 9, "misc", "x", rev="int"), dg(Tool.TY, 9, "revealed-type", "x", rev="str"),
               dg(Tool.PYRIGHT, 9, "reveal", "x", rev="str"))
    st = state(META_SRC, {Tool.MYPY: [m], Tool.TY: [t], Tool.PYRIGHT: [p]})
    assert not (ids(st, disc(K.REVEAL_MISMATCH, 9, mypy=[m], ty=[t], pyright=[p])) & FIXD)


REPLACE_SRC = ("from typing import dataclass_transform\n\n@dataclass_transform()\nclass ModelBase: ...\n\n"
               "class Model(ModelBase):\n    value: int\n\nModel.__replace__  # error: [unresolved-attribute]\n"
               "Model(value=1).__replace__  # error: [unresolved-attribute]\n")


def test_lead_b_replace_not_dismissed():
    rt = RuntimeResult(status="exception", exc_type="AttributeError", exc_message="type object 'Model' has no attribute "
                       "'__replace__'", exc_line=9, frames=[(9, "<module>")])
    st = state(REPLACE_SRC, {}, rt)
    assert not (ids(st, disc(K.RUNTIME_MISS, 9, stmt="Model.__replace__  # error: [unresolved-attribute]")) & FIXD)
