#!/bin/bash
# usage: gh_view.sh <outfile> repo#num ...   (read-only gh issue view / gh pr view; retried 3x)
out="$1"; shift
: > "$out"
for ref in "$@"; do
  repo="${ref%%#*}"; num="${ref##*#}"
  echo "################ $repo#$num" >> "$out"
  ok=0
  for try in 1 2 3; do
    res=$(timeout 60 gh issue view "$num" --repo "$repo" --json number,title,state,stateReason,createdAt,closedAt,labels,author,body,comments -q '"\(.title) | \(.state) \(.stateReason // "") | created \(.createdAt[0:10]) closed \(.closedAt // "-") | labels: \([.labels[].name] | join(",")) | author \(.author.login)\n--- body\n\(.body[0:1800])\n--- comments (\(.comments | length))\n\([.comments[] | "[\(.author.login) \(.createdAt[0:10])] \(.body[0:700])"] | join("\n~~\n"))"' 2>&1)
    rc=$?
    if [ $rc -eq 0 ]; then ok=1; break; fi
    sleep $((try * 4))
  done
  if [ $ok -eq 1 ]; then echo "$res" >> "$out"; else echo "NOT VERIFIED (gh failed 3x): $res" >> "$out"; fi
done
echo finished >> "$out"
