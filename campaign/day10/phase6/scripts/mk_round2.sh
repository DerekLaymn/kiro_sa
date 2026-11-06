#!/bin/bash
# round-2 reductions (probes after reading round 1), written into repro2/
D=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2
mkdir -p $D && cd $D || exit 1

# ---- ty Never after assert on an overload call
cat > o1.py <<'EOF'
from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x


assert describe(3) == 4
reveal_type(describe("a"))
reveal_type(describe)
reveal_type(describe(3))
EOF
cat > o2.py <<'EOF'
from typing import reveal_type


def g(x: object) -> str:
    return "s"


assert g(3) == 4
reveal_type(g("a"))
reveal_type(g)
reveal_type(g(3))
EOF
cat > o3.py <<'EOF'
from typing import overload, reveal_type


@overload
def describe(x: int) -> int: ...
@overload
def describe(x: object) -> str: ...
def describe(x: object) -> object:
    return x


assert describe(3) == 4
reveal_type(describe("a"))
reveal_type(describe(3))
EOF
cat > o4.py <<'EOF'
from typing import reveal_type


def g(x: object) -> str:
    return "s"


def h() -> int:
    return 1


assert g(3) == "s"
reveal_type(g("a"))
assert h() == 4
reveal_type(h())
EOF
cat > o5.py <<'EOF'
from typing import reveal_type


def g(x: object) -> str:
    return "s"


v = g(3)
assert v == 4
reveal_type(v)
reveal_type(g("a"))
EOF
cat > o6.py <<'EOF'
from typing import reveal_type


def g(x: object) -> str:
    return "s"


assert g(3) == 4
print("after")
reveal_type(g("a") + "x")
reveal_type(len(g("a")))
EOF
cat > o7.py <<'EOF'
from typing import reveal_type


def g(x: object) -> str:
    return "s"


def run() -> None:
    assert g(3) == 4
    reveal_type(g("a"))
    reveal_type(1)
EOF
cat > o8.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run() -> None:
    assert g(3) == 4
    reveal_type(g(5))
    reveal_type(g(3))
EOF

# ---- mypy wrong parameter named in "Missing positional argument"
cat > m1.py <<'EOF'
def label(tag: str, name: str, width: int) -> str:
    return name.ljust(width)


label("t2", 6)
label("t2", "n")
label(1, 6)
label("t2", 6, 7, 8)
EOF
cat > m2.py <<'EOF'
def f(a: str, b: str, c: int) -> None: ...


f("x", 1)
f("x", "y")
f(1, "y")
f(1, 1)
EOF
cat > m3.py <<'EOF'
def f(a: int, b: str) -> None: ...


f("x")
f(1)
f()
EOF
cat > m4.py <<'EOF'
class K:
    def m(self, a: str, b: str, c: int) -> None: ...


K().m("x", 1)
K().m("x", "y")
EOF
cat > m5.py <<'EOF'
def f(a: str, b: str, c: int) -> None: ...


f(a="x", b=1)
f("x", b=1)
EOF

# ---- forward reference in a class body annotation (3.13)
cat > a1.py <<'EOF'
class Node:
    def clone(self) -> Node:
        return Node()
EOF
cat > a2.py <<'EOF'
class Node:
    def clone(self) -> "Node":
        return Node()
EOF
cat > a3.py <<'EOF'
from __future__ import annotations


class Node:
    def clone(self) -> Node:
        return Node()
EOF

# ---- IntFlag / Flag narrowing in mypy (== and is), versus a plain Enum control
cat > f1.py <<'EOF'
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def f(c: F) -> None:
    if c == F.R:
        return
    reveal_type(c)


def g(c: F) -> None:
    if c is F.R:
        return
    reveal_type(c)


def h(c: F) -> None:
    if c is F.R or c is F.W:
        return
    reveal_type(c)


f(F.R | F.W)
g(F.R | F.W)
h(F.R | F.W)
EOF
cat > f2.py <<'EOF'
import enum
from typing import reveal_type


class E(enum.Enum):
    R = 1
    W = 2


def f(c: E) -> None:
    if c == E.R:
        return
    reveal_type(c)


def g(c: E) -> None:
    if c is E.R:
        return
    reveal_type(c)
EOF
cat > f3.py <<'EOF'
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


both = F.R | F.W
reveal_type(both)
reveal_type(F.R | F.W)
reveal_type(~F.R)
reveal_type(F.R & F.W)
EOF
cat > f4.py <<'EOF'
import enum


class F(enum.Flag):
    R = 1
    W = 2


def g(c: F) -> str:
    if c is F.R:
        return "R"
    elif c is F.W:
        return "W"
    return "x"
EOF
ls | wc -l
