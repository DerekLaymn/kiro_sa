# read-only: gh search issues / gh search prs only. usage: gh_search.sh <out-file> <spec-file>
# spec-file lines: kind|repo|query    (kind = issues | prs)
out="$1"
spec="$2"
: > "$out"
while IFS='|' read -r kind repo q; do
  [ -z "$kind" ] && continue
  case "$kind" in \#*) continue;; esac
  echo "### $kind $repo :: $q" >> "$out"
  timeout 60 gh search "$kind" "$q" --repo "$repo" --limit 12 --json number,title,state,updatedAt \
    --jq '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' >> "$out" 2>&1
  echo "rc=$?" >> "$out"
  sleep 2.5
done < "$spec"
echo "finished" >> "$out"
