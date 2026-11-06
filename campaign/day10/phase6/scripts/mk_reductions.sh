#!/bin/bash
# writes the hand reductions (round 1) into repro/
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro || exit 1
cat > c_flag1.py <<'EOF'
import enum
from typing import reveal_type


class I(enum.IntFlag):
    A = 1
    B = 2


def f(c: I) -> str:
    if c == I.A:
        return "A"
    reveal_type(c)
    return "not A"


print(f(I.A | I.B))
EOF
cat > c_flag2.py <<'EOF'
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def f(c: F) -> str:
    if c == F.R:
        return "R"
    reveal_type(c)
    return "not R"


def g(c: F) -> str:
    if c is F.R:
        return "R"
    elif c is F.W:
        return "W"
    else:
        reveal_type(c)
        return "other"


print(f(F.R | F.W), g(F.R | F.W))
EOF
cat > c_ovl1.py <<'EOF'
from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x + 1 if isinstance(x, int) else "obj"


assert describe(3) == 4
reveal_type(1)
EOF
cat > c_ovl2.py <<'EOF'
from typing import reveal_type


def g() -> str:
    return "x"


assert g() == 4
reveal_type(1)
EOF
cat > c_ovl3.py <<'EOF'
from typing import reveal_type


def f(x: str, y: int) -> None:
    assert x == y
    reveal_type(1)


def h(x: str) -> None:
    assert x == 4
    reveal_type(2)
EOF
cat > c_ovl4.py <<'EOF'
from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x + 1 if isinstance(x, int) else "obj"


reveal_type(describe(3))
assert describe(3) == 4
reveal_type(describe("a"))
EOF
cat > c_eq1.py <<'EOF'
from typing import reveal_type


class M(type):
    def __eq__(cls, other: object) -> bool:
        return True

    def __hash__(cls) -> int:
        return 0


class A(metaclass=M):
    pass


def f(v: A | str) -> str:
    if type(v) == str:
        reveal_type(v)
        return "str"
    return "other"


print(f(A()))
EOF
cat > c_eq2.py <<'EOF'
from typing import reveal_type


class A:
    pass


def f(v: A | str) -> str:
    if type(v) == str:
        reveal_type(v)
        return "str"
    return "other"


def g(v: A | str, sample: str) -> str:
    if type(v) == type(sample):
        reveal_type(v)
        return "same"
    return "other"
EOF
cat > c_eq3.py <<'EOF'
from typing import reveal_type


class M(type):
    def __eq__(cls, other: object) -> bool:
        return True

    def __hash__(cls) -> int:
        return 0


class A(metaclass=M):
    pass


def g(v: A | str, sample: str) -> str:
    if type(v) == type(sample):
        reveal_type(v)
        return "same"
    return "other"


def h(v: A | str) -> str:
    if type(v) is str:
        reveal_type(v)
        return "str"
    return "other"


print(g(A(), "q"))
EOF
cat > c_abs1.py <<'EOF'
class Shape:
    def scale(self, k: float) -> Shape:
        return self


print(Shape().scale(2.0))
EOF
cat > c_abs2.py <<'EOF'
class Node:
    parent: Node | None = None

    def link(self, other: Node) -> None:
        self.parent = other


print(Node())
EOF
cat > c_abs3.py <<'EOF'
class Node:
    def link(self, other: "Node") -> None:
        pass

    def clone(self) -> Node:
        return Node()
EOF
cat > c_pc1.py <<'EOF'
from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def with_tag(f: Callable[P, R]) -> Callable[Concatenate[str, P], R]:
    def wrapper(tag: str, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


@with_tag
def label(name: str, width: int) -> str:
    return name.ljust(width)


label("t2", 6)
EOF
cat > c_pc2.py <<'EOF'
def label(tag: str, name: str, width: int) -> str:
    return name.ljust(width)


label("t2", 6)
EOF
cat > c_pc4.py <<'EOF'
from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def with_tag(f: Callable[P, R]) -> Callable[Concatenate[str, P], R]:
    def wrapper(tag: str, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


@with_tag
def label(name: str, width: int) -> str:
    return name.ljust(width)


label("t2", "n")
label("t2")
label("t2", "n", 3, 4)
label("t2", width=3)
label("t2", name="n")
EOF
cat > c_td1.py <<'EOF'
from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


c: Config = {"name": "a"}
print(c)
EOF
cat > c_td2.py <<'EOF'
from typing import TypedDict


class Config(TypedDict, total=False, closed=True):
    name: str


print(Config)
EOF
cat > c_td3.py <<'EOF'
from typing_extensions import TypedDict


class Config(TypedDict, closed=True):
    name: str


c: Config = {"name": "a"}
print(c)
EOF
cat > c_tvt1.py <<'EOF'
from collections.abc import Callable
from typing import reveal_type


class Foo[*Ts, **P = [float, bool]]:
    def args(self) -> tuple[*Ts]:
        raise NotImplementedError

    def fn(self) -> Callable[P, None]:
        raise NotImplementedError


foo = Foo[int]()
reveal_type(foo)
reveal_type(foo.args())
reveal_type(foo.fn())
EOF
cat > c_tvt2.py <<'EOF'
from collections.abc import Callable
from typing import reveal_type


class Foo[*Ts, **P = [float, bool]]:
    def __init__(self, fn: Callable[P, tuple[*Ts]]) -> None:
        self.fn = fn


def one(a: float, b: bool) -> tuple[int]:
    return (1,)


foo = Foo[int](one)
reveal_type(foo)
EOF
ls | wc -l
