# [Plan §6 step 8 / Day 3 morning / record upstream] Day 3 run log
- Setup completed: branch campaign/day3-p2 checked out, gate files cleared.
- [Plan §6 step 8 / Day 3 morning / record upstream] plan written: .agents/tasks/day3-upstream-plan.md (crash extension kind "crash" warranted; pyright#11851/#11859 not representable).
- Setup completed: branch campaign/day3-p2 checked out, gate files cleared.
- [Plan §6 step 8 / Day 3 morning / record upstream] implement step started; baseline 201 passed, kb-selftest 15 PASS.
- [Plan §6 step 8 / Day 3 morning / record upstream] crash extension (typediff/crash_upstream.py) + 11 crash entries committed (ce63f5c); ty#4883 only closes at depth >= 24 (148 s), pyright#11960 is closed upstream but 1.1.414 still hangs.
- [Plan §6 step 8 / Day 3 morning / record upstream] 9 discrepancy entries + 2 priors committed (ca5f30b); calibration: only ty-4882 changed (kept -> dismissed), no other known-real bug newly dismissed; replay skipped (runs/day2 empty).
- [Plan §6 step 8 / Day 3 morning / record upstream] done: 20 entries, 2 priors, 2 not representable (pyright#11851, #11859); pytest 352 passed, kb-selftest 20 PASS; report campaign/day3-upstream-entries.md
