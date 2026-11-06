#!/bin/bash
# round-3 probes for the ty "callee becomes Never after assert f(x) == <int literal>" finding
D=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2
mkdir -p $D && cd $D || exit 1

cat > q1.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def pos() -> None:
    if g(3) == 4:
        reveal_type(g)
        reveal_type(g(1))


def neg() -> None:
    if g(3) == 4:
        pass
    else:
        reveal_type(g)
        reveal_type(g(1))


def after() -> None:
    if g(3) == 4:
        return
    reveal_type(g)
    reveal_type(g(1))
EOF
cat > q2.py <<'EOF'
from typing import Callable, reveal_type


def run(g: Callable[[int], str]) -> None:
    assert g(3) == 4
    reveal_type(g)
    reveal_type(g(1))
EOF
cat > q3.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def a() -> None:
    assert g(3) == 4.5
    reveal_type(g)


def b() -> None:
    assert g(3) == True
    reveal_type(g)


def c() -> None:
    assert g(3) == None
    reveal_type(g)


def d() -> None:
    assert g(3) == "s"
    reveal_type(g)


def e() -> None:
    assert g(3) != 4
    reveal_type(g)


def f() -> None:
    assert g(3) == b"s"
    reveal_type(g)


def h() -> None:
    assert g(3) == 4_000
    reveal_type(g)


def i() -> None:
    assert 4 == g(3)
    reveal_type(g)
EOF
cat > q4.py <<'EOF'
from typing import reveal_type


class K:
    def m(self, x: int) -> str:
        return "s"


def run(k: K) -> None:
    assert k.m(3) == 4
    reveal_type(k.m)
    reveal_type(k.m(1))
    reveal_type(k)
EOF
cat > q5.py <<'EOF'
from typing import reveal_type


def g(x: int) -> int:
    return 1


def sz(x: object) -> int:
    return 1


def run() -> None:
    assert g(3) == 4
    reveal_type(g)
    assert sz(3) == 2
    reveal_type(sz)
    assert str(3) == 4
    reveal_type(str)
    reveal_type(int)
EOF
cat > q6.py <<'EOF'
from typing import reveal_type


def h() -> str:
    return "s"


def run() -> None:
    assert h() == 4
    reveal_type(h)
    reveal_type(h())
EOF
cat > q7.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run(y: int) -> None:
    assert g(y) == 4
    reveal_type(y)
    reveal_type(g)
EOF
cat > q8.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run() -> str:
    assert g(3) == 4
    return g(1)


def run2() -> int:
    assert g(3) == 4
    return len(g(1))


print(run2)
EOF
cat > q9.py <<'EOF'
from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run() -> None:
    assert g(3) == "a" or g(3) == 4
    reveal_type(g)
    assert g(4) in (4, 5)
    reveal_type(g)
EOF
ls | wc -l
