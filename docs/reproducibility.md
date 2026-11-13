# Reproducibility

How to get the same environment, the same test results and the same judge results as the published study, what depends
on a model and what does not, and how to run everything with no API key.

The short version:

```bash
python3.13 -m venv .venv && . .venv/bin/activate
pip install -e ".[tools,test]" -c constraints.txt
scripts/reproduce.sh
```

## 1. Environment

| Item | Reference value |
|---|---|
| OS | Linux (also expected to work on macOS) |
| CPython | 3.13 (reference environment: 3.13.16). typediff targets `--python-version 3.13` and the interpreter that runs it must be at least that version. |
| mypy | 2.4.0 |
| ty | 0.0.97 |
| pyright | 1.1.414 (the PyPI wrapper; it downloads Node.js on first use, so the first run needs network access) |
| pytest | 8.3.5 |
| Other | `git` 2.25 or newer for `scripts/harvest_seeds.py`; network access only for `fetch-docs`, `harvest_seeds.py`, `calibrate --fetch` and an LLM provider |

The versions are defined in one place, `typediff/pins.py`, and mirrored in `constraints.txt` and the `tools` extra in
`pyproject.toml`. A test (`tests/test_reproducibility.py`) fails if they disagree.

```bash
git clone <this repository> typediff && cd typediff
python3.13 -m venv .venv && . .venv/bin/activate         # or: uv venv --python 3.13
pip install -e ".[tools,test]" -c constraints.txt        # or: uv pip install -e ".[tools,test]" -c constraints.txt
typediff --python-version 3.13 doctor --strict           # exit code 0 when all versions match
```

Expected output of `doctor`:

```
tool     pinned   installed  status
mypy     2.4.0    2.4.0      ok
ty       0.0.97   0.0.97     ok
pyright  1.1.414  1.1.414    ok
python   3.13     3.13       ok
```

**Why the pins matter.** The checkers change output between releases (ty is `0.0.x` and releases weekly). Moving ty from
0.0.84 to 0.0.97 during the study changed which discrepancies exist and closed two upstream issues. With other versions
everything still runs, but counts, KB matches and some tests can differ. `doctor` and `kb-selftest` print a warning when
the installed versions differ from the pins.

## 2. Check the installation

```bash
pytest -q                                      # expected: 762 passed in about 3 minutes
typediff --python-version 3.13 kb-selftest     # expected: 20 PASS, 0 FAIL (exit code 0)
python scripts/check_hits.py 0.80              # expected: the 36 parent programs, 0 with problems
```

A test count above 762 means tests were added after this document was written. Failures with other tool versions are
expected and are not a defect of the checkout.

## 3. Judge the seeds (no LLM, no API key)

```bash
TYPEDIFF_TOOL_MEM_MB=2048 TYPEDIFF_LLM=null typediff --python-version 3.13 --no-reduce --audit-rate 0 --out runs/seeds-out seeds seeds/
```

**Memory.** `seeds/parents/d3p_crash_mypy_segv_recursive_tvt_default_alias.py` is a mypy crash reproducer. Without a limit,
mypy grows past 8 GB on it (until the 120 s checker timeout or the SIGSEGV), which can take a machine with 16 GB down.
`TYPEDIFF_TOOL_MEM_MB` makes typediff watch the resident memory of each mypy and ty process (Linux only, read from
`/proc`; pyright is not watched) and SIGKILL it above the limit. That is recorded as a `mypy:signal-SIGKILL` crash finding,
which the reference numbers contain for this program. The default is unlimited;
`reproduce.sh` and `replay_final_round.sh` use 2048 unless you set the variable. The other seed programs stay below
250 MB per checker process, and the replay gives its reference numbers at 2048. For your own corpora raise the value if a legitimate program needs more, and keep `--jobs` at 6
or fewer: the limit is per process, not for the whole run.

`scripts/reproduce.sh` does this on a copy of `seeds/` without `seeds/harvested/` and prints the tier counts. Expected on
the pinned versions:

```
programs=65 discrepancies=88 findings by tier: confirmed=8, dismissed=30, review=60
```

The 65 programs are the 29 hand-written seeds plus the 36 parent programs. With `TYPEDIFF_LLM=null` the 8 `confirmed`
findings are all checker crashes (7 signal crashes of ty and mypy, 1 pyright internal error); everything else the rules cannot close stays in `review`. Read the review queue as patterns:

```bash
typediff triage runs/seeds-out --top 15 --details
```

Run order matters slightly for `typediff seeds` because all programs share one `dataset.jsonl` and a later program with
the same signature as an earlier finding is marked `DUPLICATE`. `scripts/kbloop_run.py` has no shared dataset and is
independent of order.

### Seed harvest (optional)

`seeds/harvested/` is not committed. To rebuild it:

```bash
python scripts/harvest_seeds.py                      # network, about 100 MB of shallow clones in ~/.cache/typediff/upstream
python scripts/harvest_seeds.py --sources conformance,mypy --out seeds/harvested
```

Sources: the python/typing conformance tests, ty's mdtests (in the ruff repository), mypy's `check-*.test` files,
pyright's sample files and typeshed's `@tests/test_cases`. mypy and pyright are taken at the pinned tags (`v2.4.0`,
`1.1.414`); ruff has no tag per ty release, so the ty tests come from its default branch. The commit of every source is
written to `seeds/harvested/PROVENANCE.json`. Because upstream changes, a harvest made later gives a different corpus.
Judge it with `TYPEDIFF_TOOL_MEM_MB=2048 scripts/kbloop_run.py OUT seeds/harvested --jobs 4 --progress OUT.log` (several thousand programs).
`docs/kb-loop-split/` holds the fixed hold-out split used while the KB was tuned.

## 4. A generation round

The programs of the study came from a model. A new run uses your model and therefore produces different programs. The
procedure is the same for every provider; the provider is the only thing that changes (see
[llm-setup.md](llm-setup.md) for keys and settings).

**1. Choose the provider.**

```bash
cp .env.example .env     # then set TYPEDIFF_LLM and the matching key; or export the variables
```

| Option | `TYPEDIFF_LLM` | Key |
|---|---|---|
| Anthropic | `anthropic:<model>` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:<model>` | `OPENAI_API_KEY` |
| Local server (vLLM, Ollama, LiteLLM) | `openai:<model>@http://localhost:8000/v1` | none |
| File bridge (a person, a script or a coding agent answers) | `file:<dir>` | none |

**2. Generate.** Mutate the parent programs with chosen operators, or write fresh programs for an area.

```bash
typediff --python-version 3.13 generate --from-seeds seeds/parents --n 2 --ops union_widen,scope_relocation \
    --out-dir runs/gen --max-llm-calls 50
typediff --python-version 3.13 generate --area protocols --n 3 --out-dir runs/gen
```

Each program is checked by the preflight lint (valid syntax for 3.13, stdlib imports only, deterministic, no I/O) before
it is written. Files start with `# area:`, `# hypothesis:` and `# origin:` headers.

**With the file bridge.** The first run writes the prompts and answers nothing:

```bash
typediff --llm file:runs/inbox --python-version 3.13 generate --from-seeds seeds/parents --n 1 --ops union_widen --out-dir runs/gen
ls runs/inbox/*.prompt.md                       # one prompt per request
```

Write `runs/inbox/<key>.answer.json` for each prompt (`{"source": "...", "hypothesis": "...", "features": [...]}`), check
with `python scripts/inbox_check.py runs/inbox`, then run the same command again. It now writes the programs.

**3. Judge, without an LLM.**

```bash
TYPEDIFF_TOOL_MEM_MB=2048 TYPEDIFF_LLM=null python scripts/kbloop_run.py runs/out runs/gen --jobs 4 --progress runs/progress.log
python scripts/kbloop_stats.py runs/out
typediff triage runs/out --top 20
```

`kbloop_stats.py` prints programs, discrepancies, auto-closed and live counts. Expect the live count per program to be
between 0.3 and 0.9 and 25 % to 52 % of the programs to have a live finding: those are the ranges of the study's rounds
([results/funnel.md](../results/funnel.md)). Your numbers will differ, because the programs differ.

**4. Read and decide.** Group the live findings with `triage`, reduce candidates, search the trackers (issue bodies, not
only titles), and add KB entries for what turns out to be a duplicate or a design difference
([knowledge-base.md](knowledge-base.md)). Re-judge saved runs after a KB change with
`python scripts/kbloop_replay.py runs/out runs/out2 --verify-sample 30`.

## 5. Replay the last round without an LLM

The 250 model answers of the last round of the study are stored in the repository, so the exact programs can be
regenerated and judged without any model:

```bash
scripts/replay_final_round.sh                # about 3 minutes with 4 jobs; output in runs/replay-final-round/
JOBS=6 scripts/replay_final_round.sh my-output-dir
```

The script copies the answers to a file-bridge inbox, runs `typediff generate` with the parents, operators and counts of
that round, and judges the result. Because the prompt key is a hash of the prompt text and the prompts are built
deterministically from the parent files, every request finds its stored answer. Expected on the pinned versions:

```
prompts=250 (retry prompts=0) answers=250 answered=250 pending=0 orphan_answers=0 malformed_keys=0
programs written: 250 (expected 250)
[all] programs=250 discrepancies=247 live=168 ... dismissed=79 ...
```

(The 168 live findings are the result on the final KB. The round report quotes 172 live for the run made before the last
KB entry.) Changing `typediff/prompts.py` or a parent file changes the keys, so the stored answers stop matching;
`inbox_check.py` then reports pending prompts and orphan answers. `scripts/reproduce.sh` runs the replay when
`WITH_REPLAY=1`.

## 6. What to expect

| Check | Command | Expected (pinned versions) |
|---|---|---|
| Versions | `typediff --python-version 3.13 doctor --strict` | all `ok`, exit 0 |
| Tests | `pytest -q` | 762 passed |
| KB self-test | `typediff --python-version 3.13 kb-selftest` | 20 `PASS`, 0 `FAIL` |
| Parent programs | `python scripts/check_hits.py 0.80` | 36 files, 0 with problems |
| Judge on seeds | `scripts/reproduce.sh`, step 4 | programs=65, discrepancies=88, confirmed=8, dismissed=30, review=60 |
| Replay of the last round | `scripts/replay_final_round.sh` | 250 programs, 247 discrepancies, 168 live, 79 dismissed |
| Bug reproducers | [examples/bugs/README.md](../examples/bugs/README.md) | each file shows the listed actual behaviour on the named tool |

## 7. Deterministic and model-dependent parts

| Part | Deterministic? | Notes |
|---|---|---|
| Tool invocation, flags, isolation, parsing | Yes | Fresh temp directory, no user config, no cache, pinned flags. |
| Discrepancy extraction, rules, KB, dismissals, reduction, dedup, triage, statistics | Yes | For the same program text and the same tool versions. |
| The judge as run in the study | Yes | `TYPEDIFF_LLM=null`; no model output enters any judgment. |
| ty run twice | Checked | A difference between the two runs is itself reported as a crash finding. |
| Stack-overflow crashes (bugs 1 and 7) | Mostly | Whether and how they are reported can depend on the machine's stack size. |
| Program generation | **No** | A different model, or the same model another day, writes different programs. Temperature is 0.8. |
| LLM adjudication, skeptic, advocate, strategist, reporter | **No** | Optional; not used for any published number. |
| Seed harvest | No | Upstream repositories change; `PROVENANCE.json` records the commits. |
| Issue states in `results/` | No | They were read on 2026-11-06 and may have changed. |
| Calibration | Deterministic for a fixed manifest, but not the published numbers | The committed summary is from the first run (ty 0.0.84, 156 reports). `positives.json` was refreshed later, so a re-run on the final KB scores 189 reports and dismisses 14 (10 ty, 4 mypy); see [calibration/README.md](../calibration/README.md). |

## 8. Running with no LLM and no key

Everything in sections 1, 2, 3, 5 and 6 works with no key and no network access beyond installing the packages
(and pyright's first-run Node.js download). `TYPEDIFF_LLM` defaults to `null`. Commands that need a model say so and exit
with code 2 and a clear message: `generate` and `loop`.

```bash
$ TYPEDIFF_LLM=null typediff generate --out-dir runs/gen
generate needs an LLM (TYPEDIFF_LLM=...)
```

If a provider is selected and its key is missing, typediff names the variable:
`error: ANTHROPIC_API_KEY is not set, but TYPEDIFF_LLM selects the anthropic provider ...`.

## 9. Files that define the study

| Path | Role |
|---|---|
| `seeds/<area>/` | 29 hand-written seed programs. |
| `seeds/parents/` | The 36 parent programs left after the last round (programs that showed a new pattern, minus the retired ones). |
| `examples/bugs/` | One reproducer for each of the 12 verified bugs. |
| `examples/replay/final-round/answers/` | The stored model answers of the last round (250). |
| `examples/replay/final-round/parents/` | The 45 parent programs those answers were written for. |
| `typediff/data/known_upstream.json` | Upstream entries, crash entries and prior stances. |
| `calibration/` | Negatives, known duplicates, the frozen positives manifest and the published results. |
| `results/` | The campaign's reports, funnel tables and bug drafts. |
| `docs/kb-loop-split/` | Hold-out and tuning split of the harvested corpus. |
| `constraints.txt`, `typediff/pins.py` | The pinned versions. |

## 10. Troubleshooting

| Symptom | Likely cause |
|---|---|
| `doctor` shows `DIFFERENT` or `MISSING` | Install with `-c constraints.txt`, or accept that counts may differ. |
| `kb-selftest` fails for one entry | Tool version differs from the pin. The entry's example depends on a message or reveal text. |
| `typediff runs on Python 3.12 but targets 3.13` | The virtual environment is older than the target. Create it with Python 3.13. |
| The first pyright run is slow or fails | The PyPI wrapper downloads Node.js on first use. Run `pyright --version` once with network access. |
| `pending` prompts in the replay | A prompt or parent file was changed; restore it with `git checkout`. |
| `error: ANTHROPIC_API_KEY is not set` | Add the key to `.env` or the shell; see [llm-setup.md](llm-setup.md). |
