#!/usr/bin/env bash
# READ-ONLY: GitHub search API (issue + PR body text). usage: gh2.sh  (queries inline below)
q() { echo "##### $1"; gh api -X GET search/issues -f q="$1" -f per_page=6 --jq '"total=\(.total_count)", (.items[] | "  \(.number) \(.state) \(.title[0:110])")' 2>&1 | head -12; }
q 'repo:python/mypy is:issue "used-before-def" base class'
q 'repo:python/mypy is:issue "NameError" "base class" forward reference not reported'
q 'repo:python/mypy is:issue class used before definition at module level not an error'
q 'repo:astral-sh/ty is:issue "used when not defined" mypy'
q 'repo:astral-sh/ty is:issue "possibly-unresolved-reference" empty list loop'
