#!/bin/bash
# exact programs and output for drafts 11 and 12 (console blocks are pasted from results2/draft11.txt and draft12.txt)
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
MG=/home/derek/.config/kiro-hooks/memguard.sh
D=$P/draft
mkdir -p $D $P/results2
cat > $D/test_bug.py <<'EOF'
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


def named_x(x: int) -> None: ...


def with_def() -> None:
    call_by_keyword(named_x)  # mypy: error


s1: Sink = lambda x, /: None  # mypy: no error
s2: Sink = lambda y, z=0: None  # mypy: no error
call_by_keyword(lambda x: None)  # mypy: no error
EOF
cat > $D/test_bug2.py <<'EOF'
from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


bad: Config = {"name": "a", "extra": 1}
EOF
{
echo '$ python test_bug.py'; (cd $D && timeout 30 $K/.venv/bin/python test_bug.py 2>&1 | tail -8)
echo '$ mypy --python-version 3.13 --no-incremental test_bug.py'; (cd $D && timeout 120 $K/.venv/bin/mypy --python-version 3.13 --no-incremental test_bug.py 2>&1)
echo '$ mypy 2.4.1'; (cd $D && timeout 120 $MG /tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental test_bug.py 2>&1)
echo '$ mypy master'; (cd $D && timeout 120 $MG /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental test_bug.py 2>&1)
echo '$ ty check --python-version 3.13 test_bug.py'; (cd $D && timeout 90 $K/.venv/bin/ty check --python-version 3.13 --output-format concise test_bug.py 2>&1)
echo '$ ty 0.0.99'; (cd $D && timeout 90 $MG /tmp/d9v/ty99/bin/ty check --python-version 3.13 --output-format concise test_bug.py 2>&1)
echo '$ pyright --pythonversion 3.13 test_bug.py'; (cd $D && timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 test_bug.py 2>&1)
} > $P/results2/draft11.txt 2>&1
{
echo '$ python test_bug2.py'; (cd $D && timeout 30 $K/.venv/bin/python test_bug2.py 2>&1 | tail -4)
for v in 3.12 3.13 3.14 3.15; do
echo "\$ pyright --pythonversion $v test_bug2.py"; (cd $D && timeout 120 $K/.venv/bin/pyright --pythonversion $v test_bug2.py 2>&1)
done
echo '$ pyright 1.1.414 with typing_extensions.TypedDict: see results2/td_versions.txt (t3.py)'
echo '$ mypy --python-version 3.13 test_bug2.py'; (cd $D && timeout 120 $K/.venv/bin/mypy --python-version 3.13 --no-incremental test_bug2.py 2>&1)
echo '$ ty check --python-version 3.13 test_bug2.py'; (cd $D && timeout 90 $K/.venv/bin/ty check --python-version 3.13 --output-format concise test_bug2.py 2>&1)
} > $P/results2/draft12.txt 2>&1
echo done
