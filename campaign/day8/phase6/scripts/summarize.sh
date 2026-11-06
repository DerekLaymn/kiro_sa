cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6/results
for f in "$@"; do
  echo "######## $f"
  grep -E "^(#####|---)|rc=|error|warning|Revealed|note:|information|Type of|\^\^\^|RangeError|panic|Found|All checks|Success|errors,|Traceback|TypeError|Error:|^[0-9]+ \||^'|^<class|^runtime" "$f.txt" | grep -v "^    at " | cut -c1-230 | sed 's#/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day8/phase6/repro/##g'
done
