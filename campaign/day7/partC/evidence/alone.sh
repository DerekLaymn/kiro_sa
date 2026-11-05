cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
export TYPEDIFF_LLM=null
rm -rf /tmp/d7/alone
mkdir -p /tmp/d7/alone
i=0
for f in \
  runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_1a265ba6.py \
  runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_a5e7d2e6.py \
  runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_662f76ab.py \
  runs/day7/gen/descriptors_properties/d3p_descriptors_decorated_get__mut1_040cc0db.py \
  runs/day7/gen/descriptors_properties/d4p_descriptors_readonly_prop_never__mut1_328a328e.py ; do
  i=$((i+1))
  mkdir -p /tmp/d7/alone/in$i
  cp $f /tmp/d7/alone/in$i/
  .venv/bin/python scripts/kbloop_run.py /tmp/d7/alone/out$i /tmp/d7/alone/in$i --jobs 1 --pyright-only --progress /tmp/d7/alone/prog$i.log > /tmp/d7/alone/run$i.log 2>&1
  echo "== $i $f rc=$?"
  .venv/bin/python scripts/kbloop_stats.py /tmp/d7/alone/out$i 2>&1 | head -2
  grep -h -E "^\| D|^\| C" /tmp/d7/alone/out$i/seed-*.md
done
