#!/bin/bash
# usage: gh_search.sh outfile "repo1,repo2" "terms one|terms two|..."   (read-only gh search, issues and PRs)
# terms are passed as separate words (AND match), not as one quoted phrase; 3 s pause + retry on rate limit
out="$1"; repos="$2"; phrases="$3"
: > "$out"
IFS=',' read -ra R <<< "$repos"
IFS='|' read -ra P <<< "$phrases"
for repo in "${R[@]}"; do
  for ph in "${P[@]}"; do
    for ty in issues prs; do
      echo "##### [$ty] $repo :: $ph" >> "$out"
      for try in 1 2 3; do
        res=$(gh search "$ty" --repo "$repo" --limit 10 --json number,title,state -q '.[] | "\(.number)\t\(.state)\t\(.title)"' -- $ph 2>&1)
        if echo "$res" | grep -q "rate limit"; then sleep 65; else break; fi
      done
      [ -n "$res" ] && echo "$res" >> "$out"
      sleep 3
    done
  done
done
echo FINISHED >> "$out"
