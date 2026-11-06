#!/bin/bash
# usage: gh_search.sh <specfile> <outfile>
# spec line: kind|repo|query    kind = issues or prs   (read-only gh search; retried up to 3 times)
spec="$1"; out="$2"
: > "$out"
while IFS='|' read -r kind repo q; do
  [ -z "$kind" ] && continue
  echo "##### $kind $repo :: $q" >> "$out"
  ok=0
  for try in 1 2 3; do
    res=$(timeout 60 gh search $kind --repo "$repo" --limit 12 --json number,title,state,updatedAt -q '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' -- "$q" 2>&1)
    rc=$?
    if [ $rc -eq 0 ]; then ok=1; break; fi
    sleep $((try * 4))
  done
  if [ $ok -eq 1 ]; then echo "$res" >> "$out"; else echo "NOT VERIFIED (gh failed 3x): $res" >> "$out"; fi
  sleep 1
done < "$spec"
echo finished >> "$out"
