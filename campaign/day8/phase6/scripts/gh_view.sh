# read-only: gh issue view / gh pr view / gh release list only
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6
out=$K/search/views.txt
: > $out
view() {
  kind=$1; repo=$2; n=$3; body=$4
  echo "=================== $kind $repo#$n" >> $out
  timeout 60 gh $kind view $n --repo $repo --json number,title,state,createdAt,closedAt,author,labels,body,comments \
    --jq '"title: \(.title)\nstate: \(.state)  created: \(.createdAt[0:10])  closed: \(.closedAt // "-")  author: \(.author.login)\nlabels: \([.labels[].name] | join(","))\nbody: \(.body[0:'$body'])\ncomments: \(.comments | length)\n" + ([.comments[-3:][] | "  -- \(.author.login) \(.createdAt[0:10]): \(.body[0:700])"] | join("\n"))' >> $out 2>&1
  sleep 1
}
view issue astral-sh/ty 4656 2500
view issue astral-sh/ty 4673 900
view issue astral-sh/ty 2792 1500
view issue astral-sh/ty 4880 900
view issue astral-sh/ty 3666 600
view issue python/mypy 15515 1500
view issue microsoft/pyright 11961 1500
view pr microsoft/pyright 11965 1200
echo "=================== releases" >> $out
timeout 60 gh release list --repo microsoft/pyright --limit 5 >> $out 2>&1
timeout 60 gh release list --repo python/mypy --limit 3 >> $out 2>&1
timeout 60 gh release list --repo astral-sh/ty --limit 3 >> $out 2>&1
echo finished >> $out
