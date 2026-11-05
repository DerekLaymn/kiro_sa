#!/bin/bash
for n in 2455 11465 11463 20230 18622 19232 16550 11495 4266; do
  echo "=================== python/mypy#$n"
  gh issue view $n --repo python/mypy --json number,title,state,createdAt,closedAt,body,comments -q '"\(.title) | \(.state) | created \(.createdAt) closed \(.closedAt)\n\(.body[0:1800])\n--- comments: \(.comments|length)\n\(.comments[0:6]|map("[\(.author.login)] \(.body[0:600])")|join("\n~~\n"))"' 2>&1
done
for n in 19168 19043; do
  echo "=================== PR python/mypy#$n"
  gh pr view $n --repo python/mypy --json number,title,state,body -q '"\(.title) | \(.state)\n\(.body[0:1200])"' 2>&1
done
