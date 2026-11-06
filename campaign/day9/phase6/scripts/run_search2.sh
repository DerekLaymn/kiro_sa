#!/bin/bash
P=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day9/phase6
bash $P/scripts/gh_search.sh $P/search/out_c.txt $P/search/spec_c.txt
bash $P/scripts/gh_view.sh $P/search/views2.out $P/search/views2.txt
echo all-finished > $P/search/search2.done
