cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6/search
echo "== queries per file (non-comment lines) and hits=0 lines"
for n in 1 2 3 4 5 6; do
  q=$(grep -vc '^#' spec$n.txt)
  empty=$(awk '/^### /{if(h) e++; h=0; next} /^rc=/{next} /^finished/{next} {h=1} END{if(!h) e++; print e+0}' out$n.txt)
  echo "spec$n: $q queries"
done
echo "== valid batches (spec3..spec6) by repo and kind"
cat spec3.txt spec4.txt spec5.txt spec6.txt | grep -v '^#' | cut -d'|' -f1,2 | sort | uniq -c
echo "== total valid"
cat spec3.txt spec4.txt spec5.txt spec6.txt | grep -vc '^#'
echo "== discarded (spec1+spec2, long queries, zero results because GitHub ANDs all words)"
cat spec1.txt spec2.txt | grep -vc '^#'
echo "== results lines (non-header) in out1/out2 (should be ~0 for the discarded ones)"
grep -v '^###\|^rc=\|^finished' out1.txt | wc -l
grep -v '^###\|^rc=\|^finished' out2.txt | wc -l
echo "== gh view/issue count"
grep -c '^=====' views.txt views2.txt views3.txt
