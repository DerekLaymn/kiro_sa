#!/usr/bin/env bash
# READ-ONLY duplicate searches (gh search issues) for the ANNOTATION-ONLY-READ crash-evidence note
OUT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/s3-r2-gh1.txt
: > $OUT
q() { echo "### $*" >> $OUT; gh search issues "$@" --limit 12 --json number,title,state,url --jq '.[] | "\(.state) \(.url) \(.title)"' >> $OUT 2>&1; }
q --repo python/mypy "used-before-def annotation"
q --repo python/mypy "variable annotated but never assigned no error"
q --repo python/mypy "declared but not defined"
q --repo python/mypy "x: int print(x) NameError"
q --repo python/mypy "uninitialized variable"
q --repo astral-sh/ty "unresolved-reference annotation only declaration"
q --repo python/mypy "possibly-undefined"
