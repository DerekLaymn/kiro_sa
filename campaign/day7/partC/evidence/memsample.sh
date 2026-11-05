#!/usr/bin/env bash
# sample MemAvailable (MB) once a second until campaign/day7/judge.done has two lines (stats+triage finished)
DONE=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day7/judge.done
OUT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day7/mem-samples.tsv
echo -e "epoch\tmem_available_mb\tswap_used_mb" > "$OUT"
while true; do
  a=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  st=$(awk '/SwapTotal/ {t=$2} /SwapFree/ {f=$2} END {print int((t-f)/1024)}' /proc/meminfo)
  echo -e "$(date +%s)\t$a\t$st" >> "$OUT"
  if [ -e "$DONE" ] && [ "$(wc -l < "$DONE")" -ge 2 ]; then break; fi
  sleep 1
done
