#!/usr/bin/env bash
# Keep the two small programs run during the morning read (Day-8 live items) and their output on the pins.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
D=campaign/day9/phase2/repro
mkdir -p "$D"
cat > "$D/callable_name.py" <<'PY'
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def logged(fn: F) -> F:
    print(fn.__name__)
    return fn


def plain(fn: Callable[..., Any]) -> None:
    print(fn.__name__)
PY
cat > "$D/kw_only_positional.py" <<'PY'
from dataclasses import dataclass


@dataclass(kw_only=True)
class Config:
    retries: int = 3
    name: str
    debug: bool = False


def positional() -> None:
    Config('svc')


@dataclass(kw_only=True)
class C2:
    name: str


C2('svc')
PY
for f in callable_name kw_only_positional; do
  {
    echo "== ty $(.venv/bin/ty --version)"; .venv/bin/ty check --python-version 3.13 "$D/$f.py" 2>&1
    echo "== mypy"; .venv/bin/mypy --python-version 3.13 --no-incremental "$D/$f.py" 2>&1
    echo "== pyright"; .venv/bin/pyright --pythonversion 3.13 "$D/$f.py" 2>&1
  } > "$D/$f.out"
done
ls -l "$D"
