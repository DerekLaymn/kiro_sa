# Results

Output of the 10-day campaign that ran the typediff pipeline against mypy 2.4.0, ty 0.0.97 and pyright 1.1.414 (CPython 3.13).

| File | Content |
|---|---|
| [FINAL-SUMMARY.md](FINAL-SUMMARY.md) | Campaign summary: pipeline changes, KB growth, live-rate trend, verified bugs, duplicates, limitations |
| [verified-bugs.md](verified-bugs.md) | Table of the 12 verified bug drafts with tool, description, confidence and filing state |
| [bugs.md](bugs.md) | The 12 issue drafts (reduced program, versions, expected and actual behaviour) |
| [funnel.md](funnel.md) | Per-day funnel: programs, discrepancies, auto-closed, live; KB growth |
| [days/](days/) | Report of each day (`day2-report.md` to `day10-report.md`) and the Day 8 pipeline experiment note |
| [kb-loop-log.md](kb-loop-log.md), [kb-loop-candidates.md](kb-loop-candidates.md) | Log of the knowledge-base improvement rounds on the harvested corpus, and the ranked candidate list |
| [../calibration/RESULTS.md](../calibration/RESULTS.md) | Calibration of the judge on known true bugs (positives) and known non-bugs (negatives) |

Strings such as `[campaign working file]` in these files stand for scratch files of the original campaign that are not part of the repository.
