#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for f in campaign/day8/mk_groups.sh campaign/day8/gen_pass.sh campaign/day8/answer_pending.sh campaign/day8/gen_worker.sh \
         campaign/day8/judge.sh campaign/day8/gen-pass-dryrun.sh; do
  bash -n "$f" && echo "syntax ok: $f"
done
.venv/bin/python -m py_compile campaign/day8/only_pyright_relations.py campaign/day8/check_reserve.py && echo "py_compile ok"
echo "== diff vs Day 7 (path substitutions only expected in the unchanged parts)"
diff <(sed 's/day7/day8/g; s/DAY7/DAY8/g; s/d7/d8/g' campaign/day7/gen_worker.sh) campaign/day8/gen_worker.sh && echo "gen_worker.sh: identical to Day 7 after day7->day8"
diff <(sed 's/day7/day8/g; s/DAY7/DAY8/g; s/d7/d8/g' campaign/day7/answer_pending.sh) campaign/day8/answer_pending.sh
echo "== model flags in gen_worker.sh"
grep -n "kiro-cli chat" campaign/day8/gen_worker.sh
echo "== --llm in gen_pass.sh"
grep -n "llm file:" campaign/day8/gen_pass.sh
