#!/usr/bin/env bash
# Day 8 phase 4: collect memory figures and journal check for the judge run window.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
D=campaign/day8/phase4
S="$(cat $D/window.start)"
E="$(cat $D/window.end)"
echo "window: $S .. $E"
echo "samples: $(wc -l < $D/memavail.tsv)"
echo "first sample (epoch kB):"; head -1 $D/memavail.tsv
echo "lowest 3 samples (epoch kB):"; sort -k2 -n $D/memavail.tsv | head -3
echo "highest sample:"; sort -k2 -n $D/memavail.tsv | tail -1
echo "--- journalctl (all units) lines matching oom|out of memory|killed process:"
journalctl --since "$S" --until "$E" --no-pager 2>&1 | grep -i -E "oom|out of memory|killed process" | wc -l
echo "--- journalctl total lines in window:"
journalctl --since "$S" --until "$E" --no-pager 2>&1 | wc -l
echo "--- journalctl first lines:"
journalctl --since "$S" --until "$E" --no-pager 2>&1 | head -3
echo "--- journalctl -k (kernel) lines matching oom|killed process:"
journalctl -k --since "$S" --until "$E" --no-pager 2>&1 | grep -i -E "oom|killed process" | wc -l
echo "--- systemd-oomd unit lines:"
journalctl -u systemd-oomd --since "$S" --until "$E" --no-pager 2>&1 | head -3
