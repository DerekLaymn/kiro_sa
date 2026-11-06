#!/bin/bash
P=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day9/phase6
bash $P/scripts/gh_search.sh $P/search/out_a.txt $P/search/spec_a.txt &
sleep 20
bash $P/scripts/gh_search.sh $P/search/out_b.txt $P/search/spec_b.txt &
wait
echo all-finished > $P/search/search.done
