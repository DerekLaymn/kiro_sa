#!/bin/bash
# usage: sum3.sh outfile name...  compact view of results2/<name>: cpython tail, ty 0.0.97, ty 0.0.99 (if it differs), mypy 2.4.0, pyright (from the raw file)
P=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6
out="$1"; shift
RESDIR=${RD:-results2} /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python $P/scripts/summarize.py "$@" > /dev/null
: > "$out"
for n in "$@"; do
  echo "######## $n" >> "$out"
  awk '/^--- cpython/{p=1} /^--- ty 0.0.99/{p=0} /^--- mypy 2.4.1/{p=0} /^--- mypy 2.4.0/{p=1} /^--- mypy master/{p=0} p' $P/${RD:-results2}/$n.sum.txt >> "$out"
  # ty 0.0.99 / mypy master equal to the pin?
  a=$(awk '/^--- ty 0.0.97/{p=1;next} /^--- ty 0.0.99/{p=0} p' $P/${RD:-results2}/$n.sum.txt | md5sum)
  b=$(awk '/^--- ty 0.0.99/{p=1;next} /^--- mypy 2.4.0/{p=0} p' $P/${RD:-results2}/$n.sum.txt | md5sum)
  [ "$a" = "$b" ] && echo "  [ty 0.0.99 identical to 0.0.97]" >> "$out" || echo "  [ty 0.0.99 DIFFERS from 0.0.97]" >> "$out"
  c=$(awk '/^--- mypy 2.4.0/{p=1;next} /^--- mypy 2.4.1/{p=0} p' $P/${RD:-results2}/$n.sum.txt | sed 's/mypy 2.4.0//' | md5sum)
  d=$(awk '/^--- mypy master/{p=1;next} /^--- pyright/{p=0} p' $P/${RD:-results2}/$n.sum.txt | md5sum)
  [ "$c" = "$d" ] && echo "  [mypy master identical to 2.4.0]" >> "$out" || echo "  [mypy master DIFFERS from 2.4.0]" >> "$out"
  grep -E "^\s+[A-Za-z_0-9]+\.py:[0-9]+:[0-9]+ - |errors?, " $P/${RD:-results2}/$n.txt | sed 's#/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/repro2/##' | awk '{print "  pyright: " $0}' >> "$out"
done
