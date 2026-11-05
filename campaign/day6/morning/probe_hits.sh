#!/usr/bin/env bash
# Day 6 morning: run every runs/hits parent through ty / mypy / pyright (memguard shims) and record
# exit code + crash signature, so the plan can pick parents that still crash on the pinned versions.
# Sequential on purpose (TY-4899 programs are OOM-capped by the shim). Output: one TSV line per file.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
V=$ROOT/.venv/bin
printf 'file\tty_rc\tty_sig\tmypy_rc\tmypy_sig\tpyright_rc\tpyright_sig\n'
for f in runs/hits/*.py; do
  b=$(basename "$f")
  tyo=$(timeout 90 $V/ty check --python-version 3.13 "$f" 2>&1); tyrc=$?
  myo=$(timeout 90 $V/mypy --python-version 3.13 --no-incremental --no-error-summary "$f" 2>&1); myrc=$?
  pro=$(timeout 120 $V/pyright --pythonversion 3.13 "$f" 2>&1); prrc=$?
  sig() {  # crash signature from output (file name removed first: some names contain "panic")
    local o="${1//$b/}"
    case "$o" in
      *"overflowed its stack"*|*"stack overflow"*|*"SIGABRT"*) echo stack-overflow;;
      *"too many cycle iterations"*|*"panicked"*|*"panic"*) echo panic;;
      *"RangeError"*) echo RangeError;;
      *"Segmentation"*|*"SIGSEGV"*) echo segv;;
      *"memguard"*|*"memory"*) echo memguard;;
      *) echo -;;
    esac
  }
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$b" "$tyrc" "$(sig "$tyo")" "$myrc" "$(sig "$myo")" "$prrc" "$(sig "$pro")"
done
