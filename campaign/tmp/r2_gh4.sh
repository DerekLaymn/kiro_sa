#!/usr/bin/env bash
# READ-ONLY duplicate searches for the round-2 patterns (short queries: gh search ANDs every word)
OUT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/s3-r2-gh5.txt
: > $OUT
q() { echo "### $*" >> $OUT; gh search issues "$@" --limit 8 --json number,title,state,url --jq '.[] | "\(.state) \(.url) \(.title)"' >> $OUT 2>&1; }
q --repo python/mypy "aliased conditions"
q --repo python/mypy "narrowing walrus alias condition"
q --repo python/mypy "assert_type tuple comparison"
q --repo astral-sh/ty "tuple comparison"
q --repo astral-sh/ty "Unknown unresolved-reference reveal"
q --repo python/mypy "allow-redefinition"
q --repo astral-sh/ty "__lt__ tuple subclass"
q --repo astral-sh/ty "constant folding"
q --repo astral-sh/ruff "tuple comparison ty"
q --repo microsoft/pyright "tuple comparison"
