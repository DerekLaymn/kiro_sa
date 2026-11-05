# Day 4 run log

[Plan §3 daily loop / setup] Created branch campaign/day4-p2 from campaign/day3-p2 (7d4488d).
[Plan §3 daily loop / setup] mkdir runs/day4/{inbox,gen,out}, campaign/day4.
[Plan §3 daily loop / setup] /tmp/d3v-latest: mypy 2.4.1, ty 0.0.97, pyright 1.1.414 (Python 3.13.16).
[Plan §3 daily loop / setup] /tmp/d3v-master: mypy 2.5.0+dev.879da562a4bba1ff8023799afad195bc364b730a.
[Plan §3 daily loop / setup] /tmp/d3v-trk/ty.json refreshed: 4060 issues (first gh attempt failed with network unreachable, retry succeeded).
[Plan §3 daily loop / setup] Deleted stale gate files day4-verify-review.json, day4-morning-review.json, day4-gen-status.json (if present).
[Plan §6 / verify ty#4656] gh (read-only): #4656 CLOSED not planned 2026-10-05; #4673 CLOSED duplicate 2026-10-05 (label bug, display issue); #4849 CLOSED duplicate 2026-10-28 (carljm: intentional, points to #4656).
[Plan §6 / verify ty#4656] Pipeline TYPEDIFF_LLM=null on seeds/self_classmethods/*.py and examples/self_param_unsound.py: Self-parameter findings dismissed NOT_BUG/DESIGN_DIVERGENCE by kb:TY-SELF-UPPER-BOUND; Self-typed-state crash stays in REVIEW. Mechanism consistent, no code change.
[Plan §6 / verify ty#4656] Wording only: stance text 'closed as intended behaviour (design divergence), not a bug' in known_upstream.json, kb.py, README, seeds/README, DESIGN §8, FUZZING_PLAN §1; TY-4673 stance open -> duplicate-of. Report: campaign/day4/fix-4656.md.
[Plan §3 daily loop / flaky-test] test_timeout_kills_grandchild: not reproduced before the fix (30/30 with 4 `yes` burners, 30/30 with 72 burners on 24 cores). Under load after a first rewrite, 1/30 failed: `_alive()` raised ProcessLookupError reading /proc/<pid>/stat as the process exited (a real test race besides the 1s-timeout pidfile race). Production `_exec` is correct (killpg on timeout), unchanged.
[Plan §3 daily loop / flaky-test] Fix (test only): timeout 1s -> 5s, atomic pidfile write, polling with 30s deadlines, `_alive` tolerates FileNotFoundError/ProcessLookupError, finally kills the grandchild. Proof: 30/30 loop under 4 burners, 3/3 full suite (360 passed each). Burners killed; no leftover `sleep 300`.
