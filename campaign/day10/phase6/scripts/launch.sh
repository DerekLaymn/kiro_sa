#!/bin/bash
# usage: launch.sh <log-name> name1 name2 ...   runs run_repros.sh detached, log in results/<log-name>.log
P=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6
log="$1"; shift
nohup setsid bash -c "bash $P/scripts/run_repros.sh $* > $P/results/$log.log 2>&1; echo finished >> $P/results/$log.log" > /dev/null 2>&1 < /dev/null &
echo launched
