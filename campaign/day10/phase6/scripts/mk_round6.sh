#!/bin/bash
# round-6: mypy accepts a lambda with other parameter names for a callback protocol, rejects the equivalent def (draft 12 candidate)
D=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2
mkdir -p $D && cd $D || exit 1
cat > l5.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


def named_x(x: int) -> None:
    print("x", x)


call_by_keyword(lambda value: print("value", value))  # fine
call_by_keyword(named_x)  # def with another name
call_by_keyword(lambda x: print("x", x))  # lambda with another name
EOF
cat > l6.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


call_by_keyword(lambda x: print("x", x))
EOF
cat > l7.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


s1: Sink = lambda x: None
s2: Sink = lambda x, /: None
s3: Sink = lambda *, value: None
s4: Sink = lambda y, z=0: None


def holder(s: Sink = lambda x: None) -> None: ...
EOF
ls | wc -l
