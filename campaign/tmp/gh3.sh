#!/usr/bin/env bash
# READ-ONLY: GitHub search API (issue + PR body text)
q() { echo "##### $1"; gh api -X GET search/issues -f q="$1" -f per_page=6 --jq '"total=\(.total_count)", (.items[] | "  \(.number) \(.state) \(.title[0:110]) \(.html_url)")' 2>&1 | head -10; }
q 'repo:python/mypy is:issue type() three arguments dynamic class creation'
q 'repo:python/mypy is:issue "type(" "three-argument" OR "3-argument" class'
q 'repo:astral-sh/ty is:issue assert_type literal slice typeshed'
q 'repo:astral-sh/ty is:issue assert_type "Literal" widen inferred typevar solution'
q 'repo:python/mypy is:issue allow_redefinition_new documentation first assignment'
q 'repo:astral-sh/ty is:issue "declared type" union of all assigned types inferred'
q 'repo:python/mypy is:issue forward reference base class "used-before-def" not reported'
q 'repo:python/mypy is:issue "class" "defined later" base "NameError" semantic analyzer'
