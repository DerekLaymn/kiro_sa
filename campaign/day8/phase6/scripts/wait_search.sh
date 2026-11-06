for i in $(seq 1 22); do
  if [ -f /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6/search/search2.done ]; then echo finished; exit 0; fi
  sleep 5
done
echo still-running
