#!/bin/bash
# round-4 probes: consequences of the ty "names inside a call become Never after assert f(x) == <literal>" finding
D=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2
mkdir -p $D && cd $D || exit 1

cat > r1.py <<'EOF'
def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    assert name(n) == 4  # str is never equal to 4, so this fails at runtime
    n.no_such_attribute
    name(n, 1, 2)
    name("not an int")


try:
    run(3)
except AssertionError:
    print("assertion failed")
EOF
cat > r2.py <<'EOF'
def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    if name(n) == 4:
        n.no_such_attribute
        name(n, 1, 2)
        name("not an int")


run(3)
EOF
cat > r3.py <<'EOF'
from typing import reveal_type


def mixed(n: int) -> int | str:
    return n


def anything(n: int) -> object:
    return n


def run(n: int) -> None:
    assert mixed(n) == 4
    reveal_type(n)
    reveal_type(mixed)


def run2(n: int) -> None:
    assert anything(n) == 4
    reveal_type(n)
    reveal_type(anything)
EOF
cat > r4.py <<'EOF'
from typing import reveal_type


def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    assert name(n) == 4
    reveal_type(n)


def run_x(n: int) -> None:
    if name(n) == 4:
        reveal_type(n)
    reveal_type(n)


def run_y(n: int) -> None:
    x = name(n) == 4
    reveal_type(x)
    if x:
        reveal_type(n)
EOF
cat > r5.py <<'EOF'
from typing import reveal_type


def name(n: int) -> str:
    return str(n)


def run(n: int, m: int) -> None:
    assert name(n) + name(m) == 4
    reveal_type(n)
    reveal_type(m)


def run2(n: int, m: int) -> None:
    assert name(n * 2) == 4
    reveal_type(n)
    reveal_type(name)
EOF
cat > r6.py <<'EOF'
class Box:
    def label(self) -> str:
        return "x"


def run(b: Box) -> None:
    assert b.label() == 4
    b.no_such_attribute
    reveal_type(b)
EOF
ls | wc -l
