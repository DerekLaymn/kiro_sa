# Generation settings and replay

Which parts of a run are deterministic, which settings produced the published programs, and how to replay the last
generation round without calling an LLM. Provider setup and keys are in [llm-setup.md](llm-setup.md); the full
procedure is in [reproducibility.md](reproducibility.md).

## What is deterministic

| Stage | Deterministic? |
|---|---|
| Program generation (LLM) | **No.** A different model, or the same model on another day, writes different programs. |
| Preflight lint, mypy / ty / pyright / CPython runs, discrepancy pairing, rules, KB, judge, reduction | Yes, for fixed tool versions (`typediff doctor`) and the same program text. |
| Dedup, triage, statistics | Yes. |

So a new generation run gives a different program set, while the same programs always give the same findings. The judge
uses no LLM (`TYPEDIFF_LLM=null`). Only the optional LLM adjudicator (`typediff run` / `loop` with an LLM configured)
adds model output on top of the rules.

## Settings of the published campaign

| Setting | Value |
|---|---|
| Model | `claude-haiku-5.5`, used as a stand-in generator |
| Effort | `medium` |
| Transport | File bridge: `typediff --llm file:<dir> generate ...` writes one `<key>.prompt.md` per request; a model session wrote `<key>.answer.json` (`{"source": ..., "hypothesis": ..., "features": [...]}`); the same command run again reads the answers |
| Sessions | About 50 worker sessions per round, 5 prompts each, 4 at a time (the session runner is not part of this repository) |
| Target Python | 3.13 (`--python-version 3.13`) |
| Programs per round | about 250 (exactly 250 in the last round) |

[`results/FINAL-SUMMARY.md`](../results/FINAL-SUMMARY.md) (section 8) states the limits of this generator.

## Knobs that exist in the code

| Knob | Where | Effect |
|---|---|---|
| `TYPEDIFF_LLM` / `--llm` | `typediff/llm.py` | `null`, `anthropic:<model>`, `openai:<model>[@<base-url>]`, `file:<dir>` |
| temperature | `typediff/generator.py` | Fixed at **0.8** for generation (not configurable); other LLM calls use 0.0, the voting calls 0.7 |
| `max_tokens` | `typediff/generator.py` | Fixed at 3000 for generation |
| seed | `generate --n N` | Variant index `k` (0..N-1). It is part of the prompt key and the cache key. The OpenAI-compatible client also sends it as `seed`. The Anthropic API and the file bridge have no seed |
| `--n`, `--ops`, `--area`, `--from-seeds` | `typediff generate` | Programs per request, mutation operators (`typediff/operators.py`, [design.md](design.md#6-search-strategy)), feature area, parent directory |
| `--max-llm-calls` | `generate`, `seeds`, `loop` | Budget of uncached LLM calls |
| `TYPEDIFF_LLM_MIN_INTERVAL` | `typediff/llm.py` | Seconds between HTTP requests (rate limits) |
| `TYPEDIFF_CACHE` | `typediff/llm.py` | Directory of the response cache (HTTP providers only; the key is a hash of model, prompts, temperature and seed) |

The file bridge ignores temperature. Whatever sampling settings the answering session used decide the output.

To generate with your own model: put a key in `.env` (see `.env.example`), then for example

```bash
TYPEDIFF_LLM=anthropic:<model> typediff --python-version 3.13 generate --from-seeds seeds/parents --n 2 \
    --ops union_widen --out-dir runs/gen
TYPEDIFF_TOOL_MEM_MB=2048 TYPEDIFF_LLM=null python scripts/kbloop_run.py runs/out runs/gen --jobs 4 --progress runs/progress.log
```

## Replay the last round without an LLM

`examples/replay/day10/` holds the **250 stored model answers** of the last round (`answers/`, about 1 MB) and the 45
parent programs they were written for (`parents/<group>/`). `scripts/replay_day10.sh` puts the answers in a file-bridge
inbox, runs `typediff generate` with that round's parents, operators and counts, and judges the programs:

```bash
scripts/replay_day10.sh            # about 3 minutes with 4 jobs (JOBS=6 at most); output in runs/replay-day10/
```

Every prompt finds its answer, because the prompt key is a hash of the prompt text and the prompts are built
deterministically from the parents. Expected output on the pinned tool versions:

```
prompts=250 (retry prompts=0) answers=250 answered=250 pending=0 orphan_answers=0 malformed_keys=0
programs written: 250 (expected 250)
[all] programs=250 discrepancies=247 live=168 ... dismissed=79 ...
```

The 168 live rows are the result on the final knowledge base. The round report (`results/days/day10-report.md`) quotes
172 live for the run before the last KB entry (`MYPY-8595-METACLASS-CALL`, which closes 4 rows).

If you change `typediff/prompts.py` or the parent files, the prompt keys change and the stored answers no longer match;
`scripts/inbox_check.py` then reports pending prompts and orphan answers.

To re-judge reports that were already produced (for example after a KB change) use
`scripts/kbloop_replay.py OLD_OUT NEW_OUT --jobs 4 --verify-sample 30`. It reads the saved tool outputs and does not run
the checkers again.

## Parents and seeds

| Directory | Content |
|---|---|
| `seeds/<area>/` | 29 hand-written seed programs, one feature area per folder |
| `seeds/parents/` | The 36 parent programs left after the last round: programs that were promoted because they produced a live finding, minus the ones retired later (`scripts/check_hits.py` validates them) |
| `seeds/harvested/` | Generated by `scripts/harvest_seeds.py` (needs network, not committed) |
| `examples/bugs/` | One reproducer per verified bug |
| `examples/replay/day10/` | Stored answers and parents of the last round |
