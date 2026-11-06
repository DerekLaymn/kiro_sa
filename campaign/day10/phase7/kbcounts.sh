#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
OUT=/tmp/p7_kbcounts.out
: > $OUT
for pair in "Day1:7f2969d" "Day2:096a153" "Day3:7d4488d" "Day4:a403712" "Day5:622f5b7" "Day6:1f54286" "Day7:03d88a5" "Day8:1df508f" "Day9:5a16806" "Day10:c6c5a9a"; do
  day=${pair%%:*}; c=${pair##*:}
  j=$(git show $c:typediff/data/known_upstream.json 2>/dev/null)
  if [ -z "$j" ]; then echo "$day $c json=absent" >> $OUT; kbn=$(git show $c:typediff/kb.py 2>/dev/null | grep -c 'KBEntry('); echo "   kb.py KBEntry( count=$kbn" >> $OUT; continue; fi
  n=$(echo "$j" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["entries"]), len(d["prior_stances"]), sum(1 for e in d["entries"] if e.get("kind")=="crash"))')
  kbn=$(git show $c:typediff/kb.py 2>/dev/null | grep -c 'KBEntry(')
  echo "$day $c json[entries prior_stances crash_entries]=$n kb.py_KBEntry(=$kbn" >> $OUT
done
echo finished >> $OUT
