# Command-line reference

`typediff` is installed by `pip install -e .` (see [reproducibility.md](reproducibility.md) for the pinned setup). Every
command below was checked against `typediff --help` and `typediff <command> --help`.

```
typediff [global options] <command> [command options]
```

Global options go **before** the command name. Commands: `judge`, `run`, `loop`, `seeds`, `triage`, `generate`,
`fetch-docs`, `kb-selftest`, `doctor`, `calibrate`, `report`.

## Global options

| Option | Default | Meaning |
|---|---|---|
| `--out DIR` | `typediff_out` | Output directory for reports, `dataset.jsonl` and `strategy.json`. |
| `--docs DIR` | `$TYPEDIFF_DOCS` or `~/.cache/typediff/docs` | Documentation corpus used to verify citations. |
| `--llm SPEC` | `$TYPEDIFF_LLM`, else `null` | `anthropic:<model>`, `openai:<model>[@url]`, `file:<dir>` or `null`. See [llm-setup.md](llm-setup.md). |
| `--python-version X.Y` | `3.12` | Target version passed to all three checkers. **Pass `3.13` to match the published results.** The interpreter running typediff must be at least this version. |
| `--no-pyright` | off | Do not run pyright. |
| `--pyright-only` | off | Also report errors only pyright makes (mypy and ty silent) when CPython evidence supports or contradicts them (kind `only_pyright`). |
| `--no-reduce` | off | Skip delta-debugging reduction of findings (faster). |
| `--audit-rate R` | `0.05` | Fraction of KB auto-dismissals re-checked by the LLM advocate. Only matters with an LLM. Use `0` to disable. |
| `--typeshed DIR` | none | One typeshed checkout used by both mypy and ty, which removes stub skew. |

`typediff` also reads a `.env` file from the current directory; see [llm-setup.md](llm-setup.md#where-the-api-key-goes).

## `typediff run SRC [SRC ...] [--keep-names]`

Runs mypy, ty, pyright (unless `--no-pyright`) and CPython on each file, then judges the result. Writes
`<out>/<case>.json`, `<out>/<case>.md` and appends to `<out>/dataset.jsonl`, and prints a summary per file.

| Option | Meaning |
|---|---|
| `--keep-names` | Use the file stem as the case id instead of a timestamp and hash. |

```bash
typediff --python-version 3.13 run examples/known_divergences.py --keep-names
```

## `typediff judge SRC --mypy-out F --ty-out F --runtime F [...]`

Judges outputs you already have. This is the offline four-input contract: source, mypy output, ty output and the CPython
result.

| Option | Meaning |
|---|---|
| `SRC` | The program that was checked. |
| `--mypy-out F`, `--ty-out F` | Required. Files with stdout of each checker. |
| `--mypy-err F`, `--ty-err F` | Optional stderr files (used for crash detection). |
| `--mypy-exit N`, `--ty-exit N` | Optional exit codes. |
| `--runtime F` | Required. The JSON written by `python typediff/runtime_harness.py case.py runtime.json`, a raw traceback, or the word `Success`. The JSON adds coverage and runtime `reveal_type` values. |
| `--pyright-json F` | Optional output of `pyright --outputjson`. |
| `--flags JSON` | The flags used to produce the logs, as `{"mypy": [...], "ty": [...]}`. |
| `--experiments` | Allow re-running installed tools for experiments. Without it, KB entries that need a verifying experiment stay in review. |

Recommended flags for producing the logs: mypy `--python-version 3.13 --check-untyped-defs --show-column-numbers
--show-error-codes --no-incremental`; ty `check --python-version 3.13 --output-format concise`. Run both in a directory
with no `pyproject.toml` or `ty.toml`, and with `XDG_CONFIG_HOME` pointing to an empty directory.

## `typediff seeds SEEDS [--iterations N] [--area A] [--mutate K] [--depth D] [--max-llm-calls N]`

Runs a seed corpus: every `*.py` file under `SEEDS`, recursively. A sub-folder named after a feature area sets the area
(or an `# area:` header in the file does). This is the main way to judge programs without an LLM.

| Option | Default | Meaning |
|---|---|---|
| `SEEDS` | | Directory of programs. |
| `--iterations N` | `100000` | Maximum number of programs to run. |
| `--area A` | all | Only seeds of this area. |
| `--mutate K` | `0` | With an LLM: ask for `K` variants of every seed that produced a live finding. |
| `--depth D` | `1` | Maximum mutation generations. |
| `--max-llm-calls N` | `0` (no limit) | Stop after `N` uncached LLM calls. |

```bash
TYPEDIFF_TOOL_MEM_MB=2048 TYPEDIFF_LLM=null typediff --python-version 3.13 --no-reduce seeds seeds/
```

`TYPEDIFF_TOOL_MEM_MB` limits the memory of each mypy and ty process (default: unlimited). The seeds contain a mypy crash
reproducer that otherwise uses more than 8 GB; see [reproducibility.md](reproducibility.md#3-judge-the-seeds-no-llm-no-api-key).

Programs that fail the preflight lint (syntax error for the target version, non-stdlib import, randomness or I/O) are
reported as rejected and skipped. All programs in one run share `dataset.jsonl`, so a later program whose signature
matches an earlier finding is marked `DUPLICATE`. For a run without that order dependence use
`scripts/kbloop_run.py` (see [scripts/README.md](../scripts/README.md)).

## `typediff generate --out-dir DIR [--area A] [--from-seeds DIR] [--n N] [--ops OPS] [--max-llm-calls N]`

Writes LLM-generated programs to `DIR` without checking them. Needs an LLM (`TYPEDIFF_LLM` or `--llm`); with `null` it
exits with code 2.

| Option | Default | Meaning |
|---|---|---|
| `--out-dir DIR` | required | Where programs are written, in one sub-folder per area. |
| `--area A` | every area | Generate for one feature area. |
| `--from-seeds DIR` | none | Mutate every program in `DIR` instead of writing from scratch. |
| `--n N` | `3` | Programs per area, or per seed with `--from-seeds`. |
| `--ops OPS` | none | Comma-separated mutation operators, for example `union_widen,scope_relocation`. |
| `--max-llm-calls N` | `0` (no limit) | Budget of uncached LLM calls. |

Each written file starts with `# area:`, `# hypothesis:` and `# origin:` headers. With `--llm file:<dir>` this command is
the first half of the file bridge; see [llm-setup.md](llm-setup.md#the-file-bridge-filedir).

## `typediff loop [--iterations N] [--area A] [--max-llm-calls N]`

The older all-in-one campaign loop: generate a program, run the tools, judge, record in the dataset, ask the strategy
what to do next. Needs an LLM (exit code 2 with `null`).

| Option | Default | Meaning |
|---|---|---|
| `--iterations N` | `20` | Number of generated programs. |
| `--area A` | chosen by the bandit | Start in this feature area. |
| `--max-llm-calls N` | `0` (no limit) | Budget of uncached LLM calls. |

## `typediff triage RUN_DIR [--top N] [--examples N] [--all] [--details] [--only FILE] [--exclude FILE]`

Groups the live findings of a run directory into patterns (kind, silent or reporting tool, codes, message template) so
you read one pattern at a time. Patterns with strong verified bug evidence come first.

| Option | Default | Meaning |
|---|---|---|
| `RUN_DIR` | | A directory of `<case>.json` reports. |
| `--top N` | `30` | Number of patterns shown. |
| `--examples N` | `3` | Examples per pattern. |
| `--all` | off | Include dismissed findings. |
| `--details` | off | Show both tools' messages, the evidence and the report path. |
| `--only FILE` | none | File with seed paths (one per line): triage only these. |
| `--exclude FILE` | none | File with seed paths to skip, for example the hold-out set. |

## `typediff report CASE.json --finding ID`

Re-judges the source stored in a report and prints a draft upstream issue for one finding (for example `D1`). Needs the
checkers installed. With an LLM the text is written by the reporter prompt; without one a template is filled. If the
finding's tier is not `confirmed` or `candidate`, a warning is printed. If a prior upstream stance matches, the draft
starts with the stance and its URL.

```bash
typediff --python-version 3.13 report typediff_out/<case>.json --finding D1
```

## `typediff fetch-docs [--refresh-rule-map]`

Downloads the typing spec, mypy documentation, ty documentation and the pyright mypy-comparison page into `--docs`,
plus the ty rule list from the installed ty binary. Needs network access. The corpus is used to verify quotes in LLM
verdicts; deterministic runs do not need it.

| Option | Meaning |
|---|---|
| `--refresh-rule-map` | Rebuild `typediff/data/ty_rule_map.json` from ty's migration guide. Only needed after upgrading ty. |

## `typediff kb-selftest`

Runs the canonical example of every KB entry that has one and checks that the entry still fires. Prints `PASS` or `FAIL`
per entry and exits 1 on any failure. Warns when the installed tools differ from the pinned versions. Expected on the
pinned versions: 20 `PASS`, 0 `FAIL`.

```bash
typediff --python-version 3.13 kb-selftest
```

## `typediff doctor [--strict]`

Compares the installed mypy, ty, pyright and Python with the versions the results were produced with
(`typediff/pins.py`). Prints one row per tool with status `ok`, `DIFFERENT` or `MISSING`.

| Option | Meaning |
|---|---|
| `--strict` | Exit 1 when any version differs or is missing. |

Expected output on the pinned environment:

```
tool     pinned   installed  status
mypy     2.4.0    2.4.0      ok
ty       0.0.97   0.0.97     ok
pyright  1.1.414  1.1.414    ok
python   3.13     3.13       ok
```

## `typediff calibrate [options]`

Measures whether the deterministic stage ever dismisses a real bug. It runs open maintainer-labelled bug reports from
GitHub (positives) and the documented-difference programs (negatives, `calibration/negatives/`) and checks the
`calibration/must_stay_live/` programs. Results go to `<out>/calibration/`.

| Option | Default | Meaning |
|---|---|---|
| `--manifest F` | `calibration/positives.json` | Positives manifest. |
| `--negatives DIR` | `calibration/negatives` | Documented-difference programs. |
| `--must-stay-live DIR` | `calibration/must_stay_live` | Programs no dismissal may touch. A dismissed one is reported as a violation. |
| `--fetch` | off | (Re)download the bug reports from GitHub. Needs network access. |
| `--tools LIST` | `ty,mypy` | Which checkers' bug reports to use. |
| `--limit N`, `--offset N` | `0`, `0` | Run in chunks; rows are appended. The negatives run with the last chunk. |
| `--timeout S` | `30` | Per-checker timeout, for hang reports. |

The committed manifest `calibration/positives.json` is the frozen set used for the published numbers, so calibration can
be re-run without `--fetch`. See [calibration/README.md](../calibration/README.md).

## Helper scripts

`scripts/` holds helpers that are not part of the `typediff` command: seed harvesting, the parallel corpus runner, replay,
statistics and the reproduction scripts. They are listed in [scripts/README.md](../scripts/README.md).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | `kb-selftest` had a failure, `doctor --strict` found a difference, or `report` did not find the finding. |
| `2` | Configuration error: for example a missing API key (`error: ANTHROPIC_API_KEY is not set ...`), an unknown provider, or `generate`/`loop` without an LLM. |
