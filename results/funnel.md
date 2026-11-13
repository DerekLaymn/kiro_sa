# Per-day funnel

How many programs each day produced, how many findings the deterministic judge and the knowledge base closed, and how many stayed live for reading. Copied from sections 3 and 4 of [FINAL-SUMMARY.md](FINAL-SUMMARY.md); the per-day reports are in [rounds/](rounds/).

## Live-rate trend per day

Judge-run figures as recorded in each day's stats file (a scratch file of the campaign; the KB at the time of the run; Days 3 to 5 with ty 0.0.84, Day 5 judged before its morning entries). "Findings" = discrepancies + tool crash events. Rates computed here. Days 1 and 2 are a different regime (a harvested corpus, no generation) and are not in the table: Day 1 ran 29 hand seeds (35 discrepancies, 25 live, 14 programs with live), Day 2 ran 5086 programs with 7277 live findings at the end.

| Day | Programs | Discrepancies | Tool crash events | Findings | Auto-closed | Live | Live per program | Programs with live | Live w/o `only_pyright` per program | Drafts added |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 160 | 50 | 18 | 68 | 20 | 48 | 0.30 | 41 (25.6 %) | n/a | 0 (candidates, verified on Day 4) |
| 4 | 246 | 175 | 40 | 215 | 73 | 142 | 0.58 | 83 (33.7 %) | n/a | 4 (drafts 1 to 4, from Day 3 candidates) |
| 5 | 250 | 154 | 42 | 196 | 60 | 136 | 0.54 | 105 (42.0 %) | n/a | 0 |
| 6 | 250 | 259 | 62 | 321 | 103 | 218 | 0.87 | 127 (50.8 %) | n/a | 1 (draft 5) |
| 7 | 224 | 151 | 31 | 182 | 75 | 107 | 0.48 | 68 (30.4 %) | 88 / 224 = 0.39 | 2 (6, 7) |
| 8 | 250 | 208 | 16 | 224 | 69 | 155 | 0.62 | 104 (41.6 %) | 135 / 250 = 0.54 | 1 (8) |
| 9 | 250 | 335 | 4 | 339 | 115 | 224 | 0.90 | 129 (51.6 %) | 180 / 250 = 0.72 | 2 (9, 10) |
| 10 | 250 | 247 | 0 | 247 | 75 | 172 | 0.69 | 101 (40.4 %) | 142 / 250 = 0.57 | 2 (11, 12) |

Day 3 findings 68 = 50 + 18; Day 4 215 = 175 + 40; Day 5 196 = 154 + 42; Day 6 321 = 259 + 62; Day 7 182 = 151 + 31; Day 8 224 = 208 + 16; Day 9 339 = 335 + 4; Day 10 247 = 247 + 0 (computed here; each equals live + auto-closed in the stats file).

The same reports re-judged on the final Day-10 KB (so the KB is held fixed): Day 7 75 / 224 = 0.33 (0.28 without `only_pyright`), Day 8 152 / 250 = 0.61 (0.53), Day 9 198 / 250 = 0.79 (0.62), Day 10 168 / 250 = 0.67 (0.55). Days 3, 4 and 6 were not replayed on the final KB; Day 5 and Day 6 replays on their own morning KBs are in section 3.

Reading the trend: the live rate per program did not fall steadily, because the generation mix changed every day (crash-family programs: 40 on Day 7, 22 on Day 9, 10 on Day 10; new areas and operators added; the opt-in `only_pyright` kind added on Day 7). Tool crash events fell from 62 on Day 6 to 0 on Day 10 because the crash families were closed by entries and then mutated less. The auto-closed share was 29.4 % to 34.0 % on the judge runs of Days 3 to 6 and 8 to 10 (Day 7: 41.2 %), so most of the live queue each day is new material to read, not noise the KB could have closed. New drafts per day do not follow the live rate: 0.87 live per program on Day 6 gave 1 draft, 0.48 on Day 7 gave 2.

## Knowledge-base growth

`known_upstream.json` counts and the number of `KBEntry(` occurrences in `typediff/kb.py`, read with `git show` at the last commit of each day as chosen here. The day-to-commit mapping is mine, from `git log` order; Days 1 and 2 share one JSON state.

| Day | Commit | `known_upstream.json` entries | of which `kind=crash` | prior stances | `KBEntry(` in `kb.py` |
|---|---|---|---|---|---|
| 1 | `7f2969d` | 5 | 0 | 4 | 39 |
| 2 | `096a153` | 5 | 0 | 4 | 44 |
| 3 | `7d4488d` | 25 | 11 | 6 | 44 |
| 4 | `a403712` | 27 | 12 | 6 | 44 |
| 5 | `622f5b7` | 30 | 12 | 6 | 44 |
| 6 | `1f54286` | 31 | 12 | 7 | 44 |
| 7 | `03d88a5` | 35 | 12 | 7 | 44 |
| 8 | `1df508f` | 39 | 12 | 7 | 47 |
| 9 | `5a16806` | 39 | 12 | 7 | 47 |
| 10 | `c6c5a9a` | 39 | 12 | 7 | 49 |

Day 3 added 20 entries and 2 prior stances after the authors' team-filed upstream crashes and discrepancy bugs were recorded. Day 10 added two matcher entries in `kb.py` only. The `known_upstream.json` entries are matched by message, source shape and (for crashes) signal; prior stances never dismiss.

How much the KB changed live counts, measured by replaying old reports on a later KB (replay output, not a new judge run):

| Reports | Replay | Live before to after |
|---|---|---|
| Day 2 `out3` | Day-3 KB | 7277 to 7273 |
| Day 5 | Day-5 morning KB | 136 to 110 (26 findings changed, all hand-checked) |
| Day 6 | Day-6 KB, then Part A | 218 to 212 to 194 (19 changed in Part A, 11 same-family rows stay live on purpose) |
| Day 7 | Day-10 KB (`--rerun-runtime`) | 107 to 75 (`phase7/results/stats_replayed_day7.out`; includes the Day-8 harness change) |
| Day 8 | Day-10 KB | 155 to 152 |
| Day 9 | Day-10 KB | 224 to 198 (25 by the `deprecated` entry, 1 by `MYPY-8595`) |
