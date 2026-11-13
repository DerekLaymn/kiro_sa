# Calibration

Calibration measures one thing: **does the deterministic stage ever dismiss a real bug?** It runs real, open bug reports
(positives) and documented non-bugs (negatives) through the pipeline with no LLM and counts what was dismissed.

| Path | Content |
|---|---|
| `positives.json` | Frozen manifest of open, maintainer-labelled bug reports (ty `bug`; mypy `bug` + `false-positive`, and `crash`) with their stdlib-only repro source. Used by `typediff calibrate` without `--fetch`. |
| `negatives/` | Programs that show documented differences between the tools. Each must be closed automatically with a KB citation. |
| `known_duplicates/` | Real discrepancies already tracked upstream. Each must be closed by exactly one named entry. See its README. |
| `must_stay_live/` | Programs no dismissal may touch. Empty by decision; see its README. |
| `results/` | `calibration_rows.jsonl` (one row per case) and `calibration_summary.json` of the published run. |
| `RESULTS.md` | Analysis of every dismissal and the false-dismissal bugs the run found in typediff. |

## Re-run

```bash
typediff --no-pyright --python-version 3.13 calibrate --timeout 30                 # about 7 minutes for the full manifest
typediff --no-pyright --python-version 3.13 calibrate --offset 40 --limit 40       # or in chunks; rows are appended
typediff --no-pyright calibrate --fetch                                            # replace the manifest with fresh reports (network)
```

Output goes to `typediff_out/calibration/` (set another place with the global `--out`). A case ends as `kept`,
`dismissed` (a candidate false dismissal), `invisible` (mypy and ty agree, so differential testing cannot see the bug) or
`excluded` (for example the repro needs `ty_extensions`).

## Published numbers (`results/`, `RESULTS.md`)

The committed rows and summary come from the first calibration run: ty 0.0.84, mypy 2.4.0, CPython 3.12, 156 bug
reports fetched in October 2026, and the KB as it was then.

| | kept | invisible | dismissed | excluded |
|---|---|---|---|---|
| ty bug reports (80) | 58 | 17 | **0** | 5 |
| mypy bug reports (76) | 38 | 34 | 4 | 0 |

Of the 4 mypy dismissals, 3 bugs no longer reproduce on mypy 2.4 and 1 falls under the deliberate join-versus-union
policy. Details: [RESULTS.md](RESULTS.md).

## A re-run on the final state is not the same experiment

`positives.json` was refreshed after that run: it now holds 194 reports, including newer ones and reports the authors
filed themselves. Re-running `typediff --no-pyright --python-version 3.13 calibrate` on the final KB with ty 0.0.97
scores 189 positives (5 excluded) and gives

| | kept | invisible | dismissed |
|---|---|---|---|
| ty | 82 | 26 | 10 |
| mypy | 36 | 31 | 4 |

and closes 26 of the 31 negatives automatically (four KB examples, `ANNOTATION-ONLY-READ`, `MYPY-15182-NEW-RETURNS`,
`JOIN-VS-UNION-CALLABLE` and `MDTEST-TODO`, are listed as left for review; `kb-selftest` passes for them). So "no ty report is dismissed" is
a statement about the published run, not about the final KB. The 10 ty dismissals of the re-run were **not** analysed one
by one. By their `decided_by`, they are: a crash that the KB records as already reported (ty#4882), two incomplete repros
(`rule:undefined-name`), and entries for documented differences (`BOTH-GRADUAL`, `MYPY-OPTIONAL-CHECK`,
`MYPY-FIRST-ASSIGNMENT-TYPE`, `LITERAL-WIDENING`, `TY-REDECLARATION`, `TY-SELF-UPPER-BOUND`). Read them before you rely on
the KB for a new campaign: the next calibration step is to check each one against its issue, as `RESULTS.md` does for
the mypy dismissals.
