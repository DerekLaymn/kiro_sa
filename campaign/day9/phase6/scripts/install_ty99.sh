#!/bin/bash
# verification-only install beside the pin; the .venv pin is not touched
mkdir -p /tmp/d9v
timeout 120 uv venv /tmp/d9v/ty99 --python 3.13 2>&1 | tail -2
timeout 120 uv pip install --python /tmp/d9v/ty99/bin/python ty==0.0.99 2>&1 | tail -3
/tmp/d9v/ty99/bin/ty --version
/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/ty --version
