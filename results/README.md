# Results

Output of the 10-day campaign that ran the typediff pipeline against mypy 2.4.0, ty 0.0.97 and pyright 1.1.414 (CPython
3.13). Days 1 and 2 improved the deterministic judge on a harvested corpus. Days 3 to 10 each generated about 250
programs with a model, judged them, and read the remaining discrepancies by hand.

Start with [FINAL-SUMMARY.md](FINAL-SUMMARY.md). For the bugs, read [verified-bugs.md](verified-bugs.md) and, for the
reduced programs, [`../examples/bugs/`](../examples/bugs/README.md).

## Headline numbers

| | |
|---|---|
| Programs | 29 hand-written seeds, 5,086 harvested programs (Day 2), 1,880 generated programs (Days 3 to 10) |
| Verified new bugs | 12: ty 4, mypy 6, pyright 2 |
| Filed upstream | 9 (ty 4, mypy 4, pyright 1); 3 not filed |
| Fixed upstream | 1 ([ty#4934](https://github.com/astral-sh/ty/issues/4934)) |
| Tests / KB self-test at the end | 760 passed (730 when the last report was written; later work added reproducibility and memory-limit tests) / 20 PASS |

Issue states were read on 2026-11-06 and may have changed.

## Files

| File | Content |
|---|---|
| [FINAL-SUMMARY.md](FINAL-SUMMARY.md) | Campaign summary: pipeline changes, KB growth, live-rate trend, verified bugs, duplicates, limitations, what was not verified |
| [verified-bugs.md](verified-bugs.md) | Table of the 12 verified bugs with tool, description, confidence and filing state |
| [bugs.md](bugs.md) | The 12 issue drafts: reduced program, versions, expected and actual behaviour, duplicate search |
| [funnel.md](funnel.md) | Per-day funnel: programs, discrepancies, auto-closed, live; KB growth; effect of KB changes on old reports |
| [days/](days/) | The report of each day |
| [kb-loop-log.md](kb-loop-log.md), [kb-loop-candidates.md](kb-loop-candidates.md) | Log of the knowledge-base improvement rounds on the harvested corpus, and the ranked candidate list |
| [../calibration/RESULTS.md](../calibration/RESULTS.md) | Calibration of the judge on known true bugs (positives) and known non-bugs (negatives) |

## Per-day reports (`days/`)

| File | Day | Content |
|---|---|---|
| [day2-report.md](days/day2-report.md) | 2 | Review queue on the harvested corpus, reviewer loop, NameError policy |
| [day3-report.md](days/day3-report.md) | 3 | First generated round (160 programs), upstream entries |
| [day4-report.md](days/day4-report.md) | 4 | Verification of Day-3 candidates, ty#4656 recorded as design |
| [day5-report.md](days/day5-report.md) | 5 | Crash closing by reference, ty bump to 0.0.97 |
| [day6-report.md](days/day6-report.md) | 6 | Generator settings, draft 5, TY-4756 entry and TY-2171 prior stance |
| [day7-report.md](days/day7-report.md) | 7 | Narrow entries for ty#2171 and ty#2792, `only_pyright` kind, drafts 6 and 7 |
| [day8-pipeline.md](days/day8-pipeline.md), [day8-report.md](days/day8-report.md) | 8 | Pipeline changes (ParamSpec family, display noise), draft 8 |
| [day9-report.md](days/day9-report.md) | 9 | New operators and areas, drafts 9 and 10 |
| [day10-report.md](days/day10-report.md) | 10 | Last round (250 programs), drafts 11 and 12, final comparison with Day 9 |

## How to read these files

- The day reports are the original records written during the campaign. They are in the first person, quote exact
  counts from run output, and say where a figure was not captured. They keep the day-by-day structure on purpose.
- Strings such as `[campaign working file]`, `[run output]`, `[agent working file]` and `[temp file]` stand for scratch
  files of the campaign that are not part of this repository.
- `<PLAYGROUND LINK>` in `bugs.md` is a placeholder: the drafts were reduced and run with the command-line tools, and
  only drafts 1 and 2 were also run on a playground.
- "Verified" means reduced, reproduced on the pinned and the newest tool versions and searched on the trackers. It does
  not mean that a maintainer confirmed the bug.
- To reproduce the judge results from these reports, see [../docs/reproducibility.md](../docs/reproducibility.md).
