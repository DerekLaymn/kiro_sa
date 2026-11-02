#!/usr/bin/env bash
H=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/seeds/harvested
C=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/tmp/chk.sh
export CHK_OUT=12
F=$(ls $H/*/ty__call__type__17.py)
bash $C $F
F=$(ls $H/*/ty__call__type__25.py)
bash $C $F
echo "######## gh ty#4536"
gh issue view 4536 --repo astral-sh/ty --json number,title,state,body,url --jq '"\(.number) \(.state) \(.title)\n\(.url)\n\(.body[0:1500])"' 2>&1
