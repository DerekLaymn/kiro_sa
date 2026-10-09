# typediff

Differential-testing adjudicator for **mypy vs ty** (with pyright as an optional, weak tie-breaker).
It separates real type-checker bugs from documented design differences, classifies them, keeps an
auditable trail, minimises repros, and advises what to generate next. See [DESIGN.md](DESIGN.md)
for the taxonomy, algorithm, oracles and prompts.

- Standard library only. The checkers run as subprocesses.
- Works with **no LLM**: deterministic rules, the KB and experiments run, and anything undecided
  goes to the human queue. Add an LLM for adjudication, review, strategy and generation.

## Install

```bash
pip install -e .            # Python >= your target version (3.13 recommended); also: pip install ty==0.0.84 mypy==2.4.0 pyright typing_extensions
typediff fetch-docs         # local typing-spec / mypy / ty / pyright corpus (needed to verify citations)
typediff kb-selftest        # confirm KB entries still match your installed tool versions
```

LLM: set `TYPEDIFF_LLM` to `anthropic:<model>`, `openai:<model>`, `openai:<model>@<base-url>`
(any OpenAI-compatible server), `file:<dir>` (manual / external agent), or `null` (default).
Responses are cached in `~/.cache/typediff/llm`.

## Use

**1. Judge outputs you already have.** These are the four inputs: source, mypy out/err, ty out/err,
and the CPython result.

```bash
typediff judge case.py --mypy-out mypy.out --mypy-err mypy.err \
                       --ty-out ty.out --ty-err ty.err --runtime runtime.txt \
                       [--pyright-json pyright.json] [--flags '{"mypy": [...], "ty": [...]}'] [--experiments]
```

- `--runtime` accepts a raw traceback, a success marker, or (best) the JSON from
  `python typediff/runtime_harness.py case.py runtime.json`. The JSON adds coverage and runtime
  `reveal_type` values.
- `--experiments` lets the judge re-run installed tools (config toggles, probes, witnesses). Without
  it, KB entries that need verification stay in review.
- Recommended flags for producing the logs:
  - mypy: `--python-version 3.12 --check-untyped-defs --show-column-numbers --show-error-codes --no-incremental`
  - ty: `check --python-version 3.12 --output-format concise`
  - Run both in a directory with no `pyproject.toml`/`ty.toml`, and with `XDG_CONFIG_HOME` pointing
    to an empty directory.

**2. Let typediff run everything** (isolated, pinned flags, runtime harness, pyright, experiments):

```bash
typediff run examples/*.py --keep-names        # results in typediff_out/<case>.{json,md} + dataset.jsonl
```

**3. Fuzz.** See [FUZZING_PLAN.md](FUZZING_PLAN.md) for the 15-day plan. The building blocks are:

```bash
typediff --python-version 3.13 seeds seeds/                     # judge a seed corpus (recursive; folder = area)
python scripts/harvest_seeds.py                                 # 4,849 programs from conformance / ty / mypy tests
typediff --llm ... generate --from-seeds DIR --n 5 --out-dir G  # LLM variants only (no judging)
typediff triage OUT_DIR                                         # group the review queue into patterns
```

Known upstream issues go in `typediff/data/known_upstream.json`. Later runs then close matching
findings as DUPLICATE, or as intended behaviour, with a link.

**Older all-in-one loop** (generate → run → judge → dataset → strategy, one LLM for every role):

```bash
TYPEDIFF_LLM=anthropic:<model> typediff loop --iterations 50 [--area narrowing_user]
typediff loop --seeds my_generated_programs/      # use your own generator's output instead
```

**4. Draft an upstream issue** for a confirmed finding:
`typediff report typediff_out/<case>.json --finding D1`

**5. Calibrate.** This measures whether the rules ever dismiss a real bug, using open bug reports
from GitHub and documented differences:

```bash
typediff --no-pyright calibrate --fetch --timeout 30            # ~7 min for 156 reports
typediff --no-pyright calibrate --offset 40 --limit 40          # or run it in chunks; rows are appended
```

Results on ty 0.0.84 / mypy 2.4.0 are in [calibration/RESULTS.md](calibration/RESULTS.md):
- **ty reports:** 0 of 80 were dismissed.
- **mypy reports:** 4 of 76 were dismissed. Three of those bugs no longer reproduce on mypy 2.4,
  and one falls under the deliberate join-vs-union policy.
- **Crashes:** 14 were confirmed automatically.

## Output

Each finding has a `tier`:

- `confirmed`: ready to report after reduction.
- `candidate`: probably a bug; glance at it before filing.
- `review`: human queue. Nothing is ever silently dropped.
- `dismissed`: has a cited reason.

Each finding also has `verdict`, `faulty_tool`, `symptom` or `dismissal`, `confidence`,
`decided_by` (`kb:<ID>`, `rule:...`, `llm+experiments`), evidence, reviewer notes, and a reduced
repro. `dataset.jsonl` holds one record per finding, with a dedup signature.

## Examples

| file | what happens (ty 0.0.84 / mypy 2.4.0) |
|---|---|
| `examples/known_divergences.py` | 6 discrepancies, all closed deterministically: 5 by KB entries (redeclaration, `Callable.__name__`, join vs union, literal widening, assignment narrowing) and 1 as an error cascade of the first |
| `examples/needs_experiments.py` | `==`-narrowing dismissed only after the `strict-equality-semantics` toggle confirms it. A mutable-override `AttributeError` that both checkers miss goes to review with opt-in-check evidence |
| `examples/self_param_unsound.py` | Reported upstream. The call is **intended** ty behaviour (`Self` is solved as a typevar per call); the wrong *displayed* signature is a real bug, ty#4673. Now closed automatically via `known_upstream.json`; see DESIGN.md §8 for the lessons |

## Layout

```
typediff/
  pipeline.py     orchestration (judge_logs / run_source)
  parsers.py      mypy/ty/pyright/runtime parsers + crash detection
  anchors.py      line → statement anchors and AST paths
  typenorm.py     revealed-type canonicalisation + relations
  concerns.py     rule pairing from ty's official mypy/pyright mapping (data/ty_rule_map.json)
  discrepancy.py  per-statement diff
  rules.py        deterministic stage (runtime evidence, probes, KB, cascades)
  kb.py           knowledge base of documented divergences (matchers + verify experiments)
  experiments.py  config toggles, probes, metamorphic, witness, assignability oracle, opt-in rerun
  adjudicator.py  LLM loop, citation verification, skeptic/advocate, asymmetric gate
  prompts.py      all LLM prompts
  corpus.py       doc corpus, BM25 retrieval, verbatim-quote verification
  reducer.py      AST delta debugging that preserves the discrepancy
  strategy.py     bandit + rules + LLM strategist
  generator.py    LLM program generator + preflight lint
  calibration.py  recall measurement on real bug reports + documented differences
  runtime_harness.py   CPython runner (coverage, reveal probes, traceback)
seeds/            hand-written seed programs per feature area (+ status)
scripts/harvest_seeds.py   seed harvester for upstream test suites
calibration/
  negatives/      documented-difference programs (must be closed automatically)
  results/        per-case rows + summary of the last calibration run
  RESULTS.md      analysis of every dismissal
```
