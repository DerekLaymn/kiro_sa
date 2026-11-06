# read-only: gh issue view / gh pr view only
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6
out=$K/search/views2.txt
: > $out
view() {
  kind=$1; repo=$2; n=$3; body=$4
  echo "=================== $kind $repo#$n" >> $out
  timeout 60 gh $kind view $n --repo $repo --json number,title,state,createdAt,closedAt,author,labels,body,comments \
    --jq '"title: \(.title)\nstate: \(.state)  created: \(.createdAt[0:10])  closed: \(.closedAt // "-")  author: \(.author.login)\nlabels: \([.labels[].name] | join(","))\nbody: \(.body[0:'$body'])\ncomments: \(.comments | length)\n" + ([.comments[-3:][] | "  -- \(.author.login) \(.createdAt[0:10]): \(.body[0:700])"] | join("\n"))' >> $out 2>&1
  sleep 1
}
view issue python/mypy 12379 1800
view pr python/mypy 15503 1800
view issue python/mypy 16293 700
view issue astral-sh/ty 4739 1500
view issue astral-sh/ty 1971 900
view issue astral-sh/ty 4345 600
view issue astral-sh/ty 4849 900
view issue python/mypy 2113 500
echo finished >> $out
