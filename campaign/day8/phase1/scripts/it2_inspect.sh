#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
grep -n "^class KBEntry" -A 18 typediff/kb.py
grep -n "def _stmt_walk\|def _stmt_node" -A 12 typediff/kb.py
mkdir -p campaign/day8/phase1/search
{
for q in "self annotated Callable attribute assignment" "self: Callable attribute defined" "annotated self callable ParamSpec __init__ attribute"; do
  echo "## python/mypy: $q"
  timeout 40 gh search issues --repo python/mypy "$q" --limit 8 --json number,title,state,url
done
} > campaign/day8/phase1/search/mypy-callable-self-store-searches.txt 2>&1
cat campaign/day8/phase1/search/mypy-callable-self-store-searches.txt
