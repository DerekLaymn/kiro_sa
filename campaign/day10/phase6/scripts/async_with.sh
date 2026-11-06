#!/bin/bash
# async-with variant of draft 10 (rows of gen9_44fe19eb): mypy with possibly-undefined enabled, ty with the rule on, pyright default, CPython
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
MG=/home/derek/.config/kiro-hooks/memguard.sh
mkdir -p $P/repro2
cat > $P/repro2/w1.py <<'EOF'
import asyncio
from contextlib import AsyncExitStack


class SwallowAsync:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *args: object) -> bool:
        return True


async def get(fail: bool) -> int:
    async with SwallowAsync():
        if fail:
            raise KeyError("k")
        value = 1
    return value


print(asyncio.run(get(False)))
try:
    print(asyncio.run(get(True)))
except NameError as exc:
    print(type(exc).__name__)
EOF
f=$P/repro2/w1.py
{
echo "--- cpython"; (cd $P/repro2 && timeout 30 $K/.venv/bin/python w1.py 2>&1 | tail -5)
echo "--- ty 0.0.97 default"; timeout 90 $K/.venv/bin/ty check --python-version 3.13 $f 2>&1 | head -20
echo "--- ty 0.0.97 --warn possibly-unresolved-reference"; timeout 90 $K/.venv/bin/ty check --python-version 3.13 --warn possibly-unresolved-reference $f 2>&1 | head -20
echo "--- ty 0.0.99 --warn possibly-unresolved-reference"; timeout 90 $MG /tmp/d9v/ty99/bin/ty check --python-version 3.13 --warn possibly-unresolved-reference $f 2>&1 | head -20
echo "--- mypy 2.4.0 possibly-undefined"; timeout 120 $K/.venv/bin/mypy --python-version 3.13 --no-incremental --enable-error-code possibly-undefined $f 2>&1 | head
echo "--- mypy 2.4.1 possibly-undefined"; timeout 120 $MG /tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental --enable-error-code possibly-undefined $f 2>&1 | head
echo "--- mypy master possibly-undefined"; timeout 120 $MG /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental --enable-error-code possibly-undefined $f 2>&1 | head
echo "--- pyright 1.1.414"; timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 $f 2>&1 | head -12
} > $P/results2/w1.txt 2>&1
echo done
