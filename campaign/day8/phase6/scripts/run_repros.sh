K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $K/campaign/day8/phase6/repro
for f in "$@"; do
  n=${f%.py}
  bash $K/campaign/day8/phase6/scripts/runall.sh $K/campaign/day8/phase6/repro/$f > $K/campaign/day8/phase6/results/$n.txt 2>&1
  echo "$f done"
done
