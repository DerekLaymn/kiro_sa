"""Day 5 morning: upstream entries added or widened after reading the Day-5 reports (results/rounds/round-5-report.md).

* TY-4148 / MYPY-22361  the issue program with a local: ``c = C(); c()``.
* MYPY-21937-REVEAL     reveal_unpaired: mypy prints nothing in the final else of an ``is`` chain over a Flag.
* TY-876                the inversion ``~F.X`` of a Flag member (ty reveals ``~F.W`` as ``Literal[F.W]``).
* MYPY-22339            a public property whose setter takes ``Callable[[T], R]`` (named in the issue body).
* MYPY-16830 / -REVEAL  enum members that are runtime aliases (duplicate values) are treated as members by mypy.

Every positive has controls that must stay live."""
from __future__ import annotations

from typediff.crash_upstream import match_crash
from typediff.kb import matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState

TY_SO = "ty:signal-SIGABRT:stack-overflow"
MYPY_SEGV = "mypy:signal-SIGSEGV"


def crash_id(tool: str, sig: str, source: str) -> str | None:
    e = match_crash(source, tool, sig)
    return e["id"] if e else None


def dg(tool, line, code, msg, reveal=None):
    return Diagnostic(tool, line, 1, Severity.NOTE if reveal else Severity.ERROR, code, msg, revealed_type=reveal)


def ids(source: str, stmt: str, kind: K, mypy=(), ty=()) -> set[str]:
    ln = next(i for i, x in enumerate(source.splitlines(), 1) if stmt in x)
    m = [dg(Tool.MYPY, ln, *x) for x in mypy]
    t = [dg(Tool.TY, ln, *x) for x in ty]
    d = Discrepancy("D1", kind, ln, ln, stmt, "", mypy=m, ty=t, pyright=[])
    st = CaseState("t", source, "3.13", {Tool.MYPY: m, Tool.TY: t, Tool.PYRIGHT: []},
                   RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return {e.id for e in matching_entries(st, d)}


# ------------------------------------------------------------------------------------------------ crash: c = C(); c()
LOCAL = 'class C:\n    __call__: "C"\n\n\ndef run() -> None:\n    c = C()\n    c()\n\n\ntry:\n    run()\nexcept TypeError:\n    pass\n'


def test_local_bound_to_instance_and_called_closes_both_crashes():
    assert crash_id("ty", TY_SO, LOCAL) == "TY-4148"  # Day-5 seed 0bc328316b4c
    assert crash_id("mypy", MYPY_SEGV, LOCAL) == "MYPY-22361"


def test_local_binding_works_for_the_other_cycle_shapes():
    pair = 'class A:\n    __call__: "B"\n\n\nclass B:\n    __call__: "A"\n\n\nx = A()\nx()\n'
    assert crash_id("ty", TY_SO, pair) == "TY-4148"
    sub = 'class C:\n    __call__: "C"\n\n\nclass D(C):\n    pass\n\n\nd = D()\nd()\n'
    assert crash_id("ty", TY_SO, sub) == "TY-4148"


def test_local_binding_controls_stay_live():
    never_called = LOCAL.replace("    c()\n", "    print(c)\n")
    assert crash_id("ty", TY_SO, never_called) is None  # declaring and instantiating is fine
    unrelated = LOCAL.replace("c = C()", "c = D()") + "\n\nclass D:\n    pass\n"
    assert crash_id("ty", TY_SO, unrelated) is None  # the called local is not an instance of the family
    no_cycle = LOCAL.replace('__call__: "C"', "__call__: int")
    assert crash_id("ty", TY_SO, no_cycle) is None
    assert crash_id("ty", "ty:signal-SIGABRT", LOCAL) is None  # signature gate unchanged


# ------------------------------------------------------------------------------------------------ MYPY-21937-REVEAL
CHAIN = ("import enum\nfrom typing import reveal_type\n\n\nclass F(enum.Flag):\n    R = 1\n    W = 2\n\n\n"
         "def check(c: F) -> str:\n    if c is F.R:\n        return 'R'\n    elif c is F.W:\n        return 'W'\n"
         "    else:\n        reveal_type(c)\n        return 'both'\n")
TY_REVEAL = [("revealed-type", "Revealed type: `F & ~Literal[F.R] & ~Literal[F.W]`", "F & ~Literal[F.R] & ~Literal[F.W]")]


def test_flag_chain_else_unpaired_reveal_is_mypy_21937():
    assert "UPSTREAM-MYPY-21937-REVEAL" in ids(CHAIN, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)
    intflag = CHAIN.replace("enum.Flag", "enum.IntFlag")
    assert "UPSTREAM-MYPY-21937-REVEAL" in ids(intflag, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)
    eq = CHAIN.replace("c is F.R", "c == F.R").replace("c is F.W", "c == F.W")
    assert "UPSTREAM-MYPY-21937-REVEAL" in ids(eq, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)


def test_flag_chain_controls_stay_live():
    plain = CHAIN.replace("enum.Flag", "enum.Enum")
    assert "UPSTREAM-MYPY-21937-REVEAL" not in ids(plain, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)  # plain Enum
    first_branch = CHAIN.replace("        reveal_type(c)\n        return 'both'", "        return 'both'") \
        .replace("        return 'R'", "        reveal_type(c)\n        return 'R'")
    assert "UPSTREAM-MYPY-21937-REVEAL" not in ids(first_branch, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)  # not in the else
    single = CHAIN.replace("    elif c is F.W:\n        return 'W'\n", "")
    assert "UPSTREAM-MYPY-21937-REVEAL" not in ids(single, "reveal_type(c)", K.REVEAL_UNPAIRED, ty=TY_REVEAL)  # no chain


def test_flag_chain_entry_does_not_close_a_reveal_mismatch():
    both = [("revealed-type", "Revealed type: `F`", "F")]
    mypy = [(None, 'Revealed type is "case.F"', "case.F")]
    assert "UPSTREAM-MYPY-21937-REVEAL" not in ids(CHAIN, "reveal_type(c)", K.REVEAL_MISMATCH, mypy=mypy, ty=both)


# ------------------------------------------------------------------------------------------------ TY-876: ~F.X
INVERT = ("import enum\nfrom typing import reveal_type\n\n\nclass F(enum.Flag):\n    R = 1\n    W = 2\n    RW = 3\n\n\n"
          "b = ~F.W\nreveal_type(b)\n")
INV_MYPY = [(None, 'Revealed type is "case.F"', "case.F")]
INV_TY = [("revealed-type", "Revealed type: `Literal[F.W]`", "Literal[F.W]")]


def test_ty876_covers_the_inversion_of_a_flag_member():
    assert "UPSTREAM-TY-876" in ids(INVERT, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)
    direct = INVERT.replace("b = ~F.W\nreveal_type(b)", "reveal_type(~F.W)")
    assert "UPSTREAM-TY-876" in ids(direct, "reveal_type(~F.W)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)
    intflag = INVERT.replace("enum.Flag", "enum.IntFlag")
    assert "UPSTREAM-TY-876" in ids(intflag, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)


def test_ty876_inversion_controls_stay_live():
    plain_enum = INVERT.replace("enum.Flag", "enum.Enum")
    assert "UPSTREAM-TY-876" not in ids(plain_enum, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)
    not_member = INVERT.replace("b = ~F.W", "b = ~5")
    assert "UPSTREAM-TY-876" not in ids(not_member, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)
    plain_member = INVERT.replace("b = ~F.W", "b = F.W")
    assert "UPSTREAM-TY-876" not in ids(plain_member, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=INV_MYPY, ty=INV_TY)


# ------------------------------------------------------------------------------------------------ MYPY-22339: setter
SETTER = ("from typing import Callable\n\n\nclass Handler[T]:\n    def __init__(self, cb: Callable[[T], None]) -> None:\n"
          "        self._cb = cb\n\n    @property\n    def cb(self) -> Callable[[T], None]:\n        return self._cb\n\n"
          "    @cb.setter\n    def cb(self, value: Callable[[T], None]) -> None:\n        self._cb = value\n\n\n"
          "def use(h: Handler[int]) -> None:\n    h.cb = lambda v: print(v.bit_length())\n\n\n"
          "def run() -> None:\n    hf = Handler[float](lambda x: print(x.is_integer()))\n    use(hf)  # expect-error\n")
SET_TY = [("invalid-argument-type", "Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]`")]


def test_mypy22339_covers_a_public_property_setter():
    assert "UPSTREAM-MYPY-22339" in ids(SETTER, "use(hf)", K.ONLY_TY, ty=SET_TY)  # Day-5 seed a660052c7821


def test_mypy22339_setter_controls_stay_live():
    read_only = SETTER.replace("    @cb.setter\n    def cb(self, value: Callable[[T], None]) -> None:\n        self._cb = value\n\n\n", "\n")
    assert "@cb.setter" not in read_only
    assert "UPSTREAM-MYPY-22339" not in ids(read_only, "use(hf)", K.ONLY_TY, ty=SET_TY)  # read-only property: contravariant is right
    private = SETTER.replace("def cb(", "def _cb_prop(").replace("@cb.setter", "@_cb_prop.setter")
    assert "UPSTREAM-MYPY-22339" not in ids(private, "use(hf)", K.ONLY_TY, ty=SET_TY)  # underscore name is exempt
    other_param = SETTER.replace("value: Callable[[T], None]", "value: int")
    assert "UPSTREAM-MYPY-22339" not in ids(other_param, "use(hf)", K.ONLY_TY, ty=SET_TY)  # setter does not take the callable
    wrong_class = [("invalid-argument-type", "Argument to function `use` is incorrect: Expected `Other[int]`, found `Other[float]`")]
    assert "UPSTREAM-MYPY-22339" not in ids(SETTER, "use(hf)", K.ONLY_TY, ty=wrong_class)  # message names another class


# ------------------------------------------------------------------------------------------------ MYPY-16830: enum aliases
ALIAS = ("from enum import IntEnum\nfrom typing import Literal, assert_never\n\n\nclass Num(IntEnum):\n    ONE = 1\n"
         "    UNO = 1\n    TWO = 2\n\n\nx: Literal[Num.ONE] = Num.UNO\n\n\ndef f(n: Num) -> int:\n    match n:\n"
         "        case Num.ONE:\n            return 1\n        case Num.TWO:\n            return 2\n    assert_never(n)\n")
ASSIGN = [("assignment", 'Incompatible types in assignment (expression has type "Literal[Num.UNO]", variable has type "Literal[Num.ONE]")')]
NEVER = [("arg-type", 'Argument 1 to "assert_never" has incompatible type "Literal[Num.UNO]"; expected "Never"')]
ASSERT_T = [("assert-type", 'Expression is of type "Literal[Num.UNO]", not "Literal[Num.ONE]"')]


def test_enum_value_alias_closes_the_mypy_rows():
    assert "UPSTREAM-MYPY-16830" in ids(ALIAS, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=ASSIGN)
    assert "UPSTREAM-MYPY-16830" in ids(ALIAS, "assert_never(n)", K.ONLY_MYPY, mypy=NEVER)
    asrt = ALIAS + "assert_type(Num.UNO, Literal[Num.ONE])\n"
    assert "UPSTREAM-MYPY-16830" in ids(asrt, "assert_type(Num.UNO", K.ONLY_MYPY, mypy=ASSERT_T)


def test_enum_value_alias_variants():
    strenum = ("from enum import StrEnum\nfrom typing import Literal\n\n\nclass Color(StrEnum):\n    RED = 'red'\n    CRIMSON = 'red'\n\n\n"
               "x: Literal[Color.RED] = Color.CRIMSON\n")
    m = [("assignment", 'Incompatible types in assignment (expression has type "Literal[Color.CRIMSON]", variable has type "Literal[Color.RED]")')]
    assert "UPSTREAM-MYPY-16830" in ids(strenum, "x: Literal[Color.RED]", K.ONLY_MYPY, mypy=m)
    true_after_one = ("from enum import IntEnum\nfrom typing import Literal\n\n\nclass I(IntEnum):\n    ONE = 1\n    TRUE = True\n\n\n"
                      "x: Literal[I.ONE] = I.TRUE\n")
    t = [("assignment", 'Incompatible types in assignment (expression has type "Literal[I.TRUE]", variable has type "Literal[I.ONE]")')]
    assert "UPSTREAM-MYPY-16830" in ids(true_after_one, "x: Literal[I.ONE]", K.ONLY_MYPY, mypy=t)
    explicit = ("from enum import Enum\nfrom typing import Literal\n\n\nclass V(Enum):\n    V1 = 1\n    V2 = 2\n    DEFAULT = V2\n\n\n"
                "x: Literal[V.V2] = V.DEFAULT\n")
    e = [("assignment", 'Incompatible types in assignment (expression has type "Literal[V.DEFAULT]", variable has type "Literal[V.V2]")')]
    assert "UPSTREAM-MYPY-16830" in ids(explicit, "x: Literal[V.V2]", K.ONLY_MYPY, mypy=e)


def test_enum_value_alias_controls_stay_live():
    distinct = ALIAS.replace("UNO = 1", "UNO = 3")
    assert "UPSTREAM-MYPY-16830" not in ids(distinct, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=ASSIGN)  # a real member
    auto = ALIAS.replace("ONE = 1", "ONE = auto()").replace("UNO = 1", "UNO = auto()").replace("import IntEnum", "import IntEnum, auto")
    assert "UPSTREAM-MYPY-16830" not in ids(auto, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=ASSIGN)  # auto() is distinct
    first = [("assignment", 'Incompatible types in assignment (expression has type "Literal[Num.TWO]", variable has type "Literal[Num.ONE]")')]
    assert "UPSTREAM-MYPY-16830" not in ids(ALIAS, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=first)  # canonical members only
    flag = ALIAS.replace("IntEnum", "IntFlag")
    assert "UPSTREAM-MYPY-16830" not in ids(flag, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=ASSIGN)  # Flag is not judged
    custom = ALIAS.replace("    TWO = 2\n", "    TWO = 2\n\n    def __new__(cls, v):\n        return int.__new__(cls, v)\n")
    assert "UPSTREAM-MYPY-16830" not in ids(custom, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=ASSIGN)  # custom values
    other_code = [("misc", 'Incompatible types in assignment (expression has type "Literal[Num.UNO]", variable has type "Literal[Num.ONE]")')]
    assert "UPSTREAM-MYPY-16830" not in ids(ALIAS, "x: Literal[Num.ONE] = Num.UNO", K.ONLY_MYPY, mypy=other_code)  # other code


REVEAL_ALIAS = ALIAS + "reveal_type(Num.UNO)\n"
RV_MYPY = [(None, 'Revealed type is "Literal[Num.UNO]?"', "Literal[Num.UNO]?")]
RV_TY = [("revealed-type", "Revealed type: `Literal[Num.ONE]`", "Literal[Num.ONE]")]


def test_enum_value_alias_reveal_rows():
    assert "UPSTREAM-MYPY-16830-REVEAL" in ids(REVEAL_ALIAS, "reveal_type(Num.UNO)", K.REVEAL_MISMATCH, mypy=RV_MYPY, ty=RV_TY)
    value = ALIAS.replace("UNO = 1", "TRUE = True") + "reveal_type(Num.TRUE.value)\n"
    assert "UPSTREAM-MYPY-16830-REVEAL" in ids(value, "reveal_type(Num.TRUE.value)", K.REVEAL_MISMATCH, mypy=RV_MYPY, ty=RV_TY)
    canonical = ALIAS + "reveal_type(Num.TWO)\n"  # the canonical member and a non-alias read stay live
    assert "UPSTREAM-MYPY-16830-REVEAL" not in ids(canonical, "reveal_type(Num.TWO)", K.REVEAL_MISMATCH, mypy=RV_MYPY, ty=RV_TY)
    canon_one = ALIAS + "reveal_type(Num.ONE)\n"
    assert "UPSTREAM-MYPY-16830-REVEAL" not in ids(canon_one, "reveal_type(Num.ONE)", K.REVEAL_MISMATCH, mypy=RV_MYPY, ty=RV_TY)
    distinct = REVEAL_ALIAS.replace("UNO = 1", "UNO = 3")
    assert "UPSTREAM-MYPY-16830-REVEAL" not in ids(distinct, "reveal_type(Num.UNO)", K.REVEAL_MISMATCH, mypy=RV_MYPY, ty=RV_TY)
