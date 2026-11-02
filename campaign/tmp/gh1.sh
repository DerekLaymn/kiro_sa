#!/usr/bin/env bash
# READ-ONLY gh searches (issue BODY text included)
q() { echo "##### $1 :: $2"; gh search issues "$2" --repo "$1" --limit 8 --json number,title,state,url 2>&1 | head -60; }
q python/mypy "used-before-def"
q python/mypy "reveal_type"
echo "##### issue list"; gh issue list --repo python/mypy --search "used-before-def" --state all --limit 8 2>&1 | head -20
gh api -X GET search/issues -f q='repo:python/mypy used-before-def' -f per_page=8 --jq '.total_count, (.items[] | "\(.number) \(.state) \(.title)")' 2>&1 | head -20
