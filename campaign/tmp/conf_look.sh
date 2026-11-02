#!/usr/bin/env bash
H=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/seeds/harvested
F=$(ls $H/*/conformance__generics_scoping.py | head -1)
sed -n 1,70p $F
echo "=========== enums_member_names"
F2=$(ls $H/*/conformance__enums_member_names.py | head -1)
sed -n 1,40p $F2
echo "=========== run"
export CHK_OUT=12 CHK_LINES=1
bash /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/tmp/chk.sh $F
