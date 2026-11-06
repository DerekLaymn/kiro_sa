#!/usr/bin/env bash
# Day 9 morning (Plan §3 "Every morning"): which parents in runs/hits and runs/hits-dropped still crash the pinned tools?
# Adapted from campaign/day8/phase2/scripts/probe_crash_parents.sh: Day 8 probed a named list of 21 files; Day 9 probes
# EVERY file of both directories with ty (sequential, memguard shim in .venv/bin, 90 s limit), then the mypy crash parent
# and the two pyright RangeError parents. ty 0.0.97 (pin). Output TSV on stdout: file, location, tool, rc, signature.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
V=$ROOT/.venv/bin
sig() {  # sig OUTPUT
  case "$1" in
    *"overflowed its stack"*|*"stack overflow"*|*"SIGABRT"*) echo stack-overflow;;
    *"too many cycle iterations"*|*"panicked"*|*"panic"*) echo panic;;
    *"memguard"*|*"memory"*) echo memguard;;
    *"RangeError"*|*"Maximum call stack"*) echo rangeerror;;
    *) echo -;;
  esac
}
printf 'file\tloc\ttool\trc\tsignature\n'
for loc in hits hits-dropped; do
  for f in runs/$loc/*.py; do
    [ -f "$f" ] || continue
    b=$(basename "$f" .py)
    o=$(timeout 90 $V/ty check --python-version 3.13 "$f" 2>&1); rc=$?
    o="${o//$b/}"
    printf '%s\t%s\tty\t%s\t%s\n' "$b" "$loc" "$rc" "$(sig "$o")"
  done
done
# the mypy crash parent (MYPY-22361 family)
b=d3p_crash_mypy_segv_recursive_tvt_default_alias
f=runs/hits/$b.py
o=$(timeout 90 $V/mypy --python-version 3.13 --no-incremental "$f" 2>&1); rc=$?
printf '%s\thits\tmypy\t%s\t%s\n' "$b" "$rc" "$(sig "$o")"
# the pyright RangeError parents (draft 7)
for b in d5p_descriptors_decorated_get_pyright_rangeerror d5p_descriptors_one_decorator_dunders_pyright_rangeerror; do
  f=runs/hits/$b.py
  o=$(timeout 90 $V/pyright --pythonversion 3.13 "$f" 2>&1); rc=$?
  printf '%s\thits\tpyright\t%s\t%s\n' "$b" "$rc" "$(sig "$o")"
done
