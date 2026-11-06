K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6
# wait for the first (too-specific) batch to end so the rate limit is not shared
while [ ! -f $K/search/search.done ]; do sleep 5; done
bash $K/scripts/gh_search.sh $K/search/out3.txt $K/search/spec3.txt
bash $K/scripts/gh_search.sh $K/search/out4.txt $K/search/spec4.txt
# issues and PRs by the account that filed ty#4941 (read-only listing)
for r in astral-sh/ty astral-sh/ruff microsoft/pyright python/mypy; do
  echo "### issues $r author:DerekLaymn" >> $K/search/out_author.txt
  timeout 60 gh search issues --repo $r --author DerekLaymn --limit 30 --json number,title,state,createdAt --jq '.[] | "\(.number)\t\(.state)\t\(.createdAt[0:10])\t\(.title)"' >> $K/search/out_author.txt 2>&1
  sleep 3
  echo "### prs $r author:DerekLaymn" >> $K/search/out_author.txt
  timeout 60 gh search prs --repo $r --author DerekLaymn --limit 30 --json number,title,state,createdAt --jq '.[] | "\(.number)\t\(.state)\t\(.createdAt[0:10])\t\(.title)"' >> $K/search/out_author.txt 2>&1
  sleep 3
done
echo all-done > $K/search/search2.done
