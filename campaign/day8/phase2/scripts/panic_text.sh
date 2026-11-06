#!/usr/bin/env bash
# the probe called d3p_crash_ty_panic_partial_or_none_in_loop "panic" with rc 1: show the matching output lines
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
timeout 90 .venv/bin/ty check --python-version 3.13 runs/hits-dropped/d3p_crash_ty_panic_partial_or_none_in_loop.py 2>&1 | grep -n -i "panic" | head
echo "rc=${PIPESTATUS[0]}"
timeout 90 .venv/bin/ty check --output-format concise --python-version 3.13 runs/hits-dropped/d3p_crash_ty_panic_partial_or_none_in_loop.py 2>&1 | head -5
