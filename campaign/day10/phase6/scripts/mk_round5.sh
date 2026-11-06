#!/bin/bash
# round-5 probes: ty rejects `lambda x: ...` for a callback protocol whose __call__ names the parameter `value`
D=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2
mkdir -p $D && cd $D || exit 1

cat > l1.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def named_value(value: int) -> None: ...
def named_x(x: int) -> None: ...
def named_positional(x: int, /) -> None: ...


a: Sink = lambda x: None
b: Sink = lambda value: None
c: Sink = named_value
d: Sink = named_x
e: Sink = named_positional
EOF
cat > l2.py <<'EOF'
from typing import Protocol


class Sink[T](Protocol):
    def __call__(self, value: T) -> None: ...


class Handler[T]:
    def __init__(self, sink: Sink[T]) -> None:
        self.sink: Sink[T] = sink


h = Handler[float](lambda x: print("float", x))
g = Handler[float](lambda value: print("float", value))
h.sink = lambda x: print(x)
g.sink = lambda value: print(value)
print(h, g)
EOF
cat > l3.py <<'EOF'
from collections.abc import Callable
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int, /) -> None: ...


def use(s: Sink) -> None: ...
def use_c(s: Callable[[int], None]) -> None: ...


use(lambda x: None)
use_c(lambda x: None)
EOF
cat > l4.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def use(s: Sink) -> None: ...


use(lambda x: None)
use(lambda *args: None)
use(lambda x, **kw: None)
use(lambda *a, **k: None)
use(lambda value=0: None)
EOF
ls | wc -l
