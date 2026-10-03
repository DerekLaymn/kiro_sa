# Fuzzing plan: mypy vs ty (15 days, ≈ $20)

Goal: find **new, confirmed, reportable** bugs in ty (and mypy) and build a documented discrepancy
dataset, using `typediff` to separate real bugs from design differences.

Assumptions:
- ty 0.0.84 and mypy 2.4.0 are pinned for the whole campaign. Upgrading mid-campaign invalidates
  the knowledge base and the dedup signatures.
- The target is **Python 3.13**. `TypeIs`, `ReadOnly` and PEP 696 type-parameter defaults need
  ≥ 3.13 at runtime, and typediff must run on a Python ≥ the target version.
- The LLM is OpenRouter: free tier first, paid credits later. The per-role LLM setting (separate
  generator and judge models) isn't built yet. This plan works around it by generating and
  judging in separate passes.

---

## 1. What we already know (day 0)

**How the first bug was found.** It wasn't random fuzzing. A hand-written seed probed a feature
ty claims to support (`Self` in a parameter). The pipeline flagged ty as silent where mypy
rejected the call, and the self-consistency oracle proved ty contradicts itself. Lesson:
**targeted seeds plus variants beat random programs.** Everything below builds on that.

**First pass over the 27 hand-written seeds** (`seeds/`, no LLM, about 1 minute):

| Result | Seed | Status |
|---|---|---|
| ty false negative: inherited method with a `Self` parameter | `self_param_inherited.py` | **Not reported upstream yet.** File it (draft in chat history) |
| Same bug in **classmethods** and **`tuple[Self, int]`** | `self_classmethod_param.py` | New variants of the same root cause; add them to that issue |
| ty silent on mixed constrained-TypeVar arguments (runtime `TypeError`) | `constrained_typevar.py` | Duplicate of open **ty#1090**, now closed automatically |
| ty accepts unknown keyword through `Unpack[TypedDict]` | `readonly_notrequired.py` | Closed upstream **as intended** (ty#4212; open TypedDicts), now closed automatically |
| mypy reveals `Weird` / `ViaMeta` where `__new__` / metaclass `__call__` return other types; CPython proves mypy wrong | `new_returns_other.py` | mypy candidate. Probably known; search python/mypy before filing |
| ty reveals `Divergent` in widening loops; mypy rejects redefinition | `widening_loop.py` | Documented ty behaviour plus mypy design; no bug |
| Others (match, LSP override, TypedDict reveal display, …) | various | In the review queue |

Of 27 seeds, 16 produced live findings, 1 is a new bug family, and 2 are already known upstream.
That is the expected ratio: most disagreements are known or intended, and the pipeline's job is to
make them cheap to discard.

**Harvested corpus** (`scripts/harvest_seeds.py`): 4,849 standalone programs from the typing
conformance suite (130), ty's mdtests (3,509) and mypy's test data (1,210). The first 130
(conformance) took 224 s, about 1.7 s per program: 0 crashes, 426 review findings in 163 patterns.

---

## 2. Strategy: where bugs are likely, in priority order

1. **Variants of known hits.** Bugs cluster: one root cause usually has several triggers. Every
   confirmed or candidate finding gets 5–20 variants (inherited vs overridden, classmethod,
   property, generic base, nested in `list`/`tuple`/`Callable`, keyword vs positional, unbound
   call, protocol).
2. **Features ty claims to support but implemented recently.** Check the type-system tracking
   issue (ty#1889) and the release notes of the last 10 ty versions. New code means fresh bugs.
   Avoid features still marked unsupported; they only yield `@Todo` / KNOWN_LIMITATION.
3. **Feature interactions.** For example `Self` × generics, ParamSpec × methods × decorators,
   TypedDict × `Unpack` × inheritance, overloads × unions × literals, descriptors × subclasses,
   dataclasses × inheritance × `KW_ONLY`.
4. **Inherited and specialised members.** The `Self` bug sits in the "inherited, not overridden"
   path. The same path exists for generic-base specialisation, descriptors on subclasses, and
   classmethods called on subclasses.
5. **Crash hunting.** Recursive aliases, self-referential generics, loops that widen types, very
   deep nesting, invalid type forms. Astral already runs a fuzzer (the `fuzzer` label), so crashes
   are less novel, but they are confirmed automatically.

What **not** to chase:
- Join-vs-union and literal-widening reveals. They are dismissed automatically.
- Anything needing third-party packages or mypy plugins.
- **Raw conformance-suite deviations.** ty's and mypy's conformance results are already published
  in python/typing, so they're known. Use conformance programs as mutation *parents*.

---

## 3. Phases

| Phase | Days | Input | LLM | Output |
|---|---|---|---|---|
| P0 Setup | 1 | — | — | Pinned tools, docs corpus, KB self-test, `Self` issue filed |
| P1 Hand seeds + harvest | 1–3 | `seeds/`, `seeds/harvested/` (4,849) | none | Review queue grouped by pattern; KB/upstream entries for recurring noise; crashes |
| P2 LLM mutation of hits | 3–10 | Seeds/harvested programs with live findings | free model (generate) | 5–20 variants per hit, judged deterministically |
| P3 LLM generation from briefs | 4–10 | Feature areas from §2 | free model (generate) | New programs in under-covered areas |
| P4 Crash hunting | 6–9 (background) | `recursive_aliases` area + crash operators | free model | Panics, hangs, non-determinism |
| P5 Judging + filing | 8–13 | Review queue | paid model (or you) | Confirmed bugs, reduced repros, issues filed |
| P6 Write-up | 13–15 | Dataset, issues | — | Submission: results tables, dataset, filed issues |

### Day-by-day

- **Day 1:**
  - Setup (§4).
  - File the `Self` issue and add it to `typediff/data/known_upstream.json` so it stops resurfacing.
  - `typediff seeds seeds/`.
  - `python scripts/harvest_seeds.py`.
- **Days 2–3 (P1):**
  - Run the harvested corpus. It's about 2.5 h of CPU for 4,849 programs; run it overnight.
  - `typediff triage` it. For each of the top patterns, decide one of: known upstream (add to
    `known_upstream.json`), design difference (add a KB entry plus a negative example), harness
    noise (fix the rule), or candidate (Phase 2 parent).
  - Target: the review queue shrinks by more than 50 % on a re-run.
- **Days 3–10 (P2 + P3, daily loop below):**
  - Spend about 70 % of LLM requests on mutating hits (P2) and 30 % on fresh briefs (P3).
- **Days 6–9 (P4):** crash-hunting generation runs in the background alongside P2/P3.
- **Days 8–13 (P5):**
  - Judge the top patterns with a paid model (or by hand).
  - For each candidate: reduce it, check the three checkers, the spec and the trackers, then file.
  - Allow one day per issue for maintainer replies; answer questions quickly.
- **Days 13–15 (P6):** freeze the versions, re-run calibration, produce results tables, write the
  report. Keep day 15 as a buffer.

### The daily loop (P2/P3)

```bash
# 1. generate (free model; generation only, no judging)
typediff --llm "openai:$GEN_MODEL@https://openrouter.ai/api/v1" --python-version 3.13 \
    generate --from-seeds runs/hits --n 5 --ops feature_crossover,narrowing_construct_swap,runtime_witness \
    --out-dir runs/day$D/gen --max-llm-calls 700
typediff --llm "openai:$GEN_MODEL@https://openrouter.ai/api/v1" --python-version 3.13 \
    generate --area self_classmethods --n 20 --out-dir runs/day$D/gen --max-llm-calls 250

# 2. judge deterministically (no LLM: KB, oracles, experiments)
TYPEDIFF_LLM=null typediff --out runs/day$D/out --python-version 3.13 seeds runs/day$D/gen

# 3. triage by pattern; copy promising programs into runs/hits for tomorrow's mutation
typediff triage runs/day$D/out --top 30
```

Every morning:
- Promote programs with strong bug evidence or new patterns into `runs/hits/`.
- Retire patterns you've classified: add a KB or upstream entry, or `avoid` them in briefs.
- Keep a log line per day: programs, discrepancies, new patterns, candidates, issues filed.

---

## 4. Setup

```bash
uv venv -p 3.13 .venv && source .venv/bin/activate      # Python >= target version
uv pip install ty==0.0.84 mypy==2.4.0 pyright typing_extensions -e .
typediff fetch-docs && typediff kb-selftest             # all PASS
python scripts/harvest_seeds.py                         # -> seeds/harvested (git-ignored)

export OPENAI_API_KEY=<openrouter key>
export TYPEDIFF_LLM_MIN_INTERVAL=3.5                    # OpenRouter free models: 20 requests/min
export GEN_MODEL=<a current ":free" coding model from openrouter.ai/models>
```

Run everything inside a container or VM with no network access for the executed programs (generated
code runs under CPython).

---

## 5. LLM budget (≈ $20)

OpenRouter limits (from [OpenRouter's rate-limit article](https://openrouter.zendesk.com/hc/en-us/articles/39501163636379-OpenRouter-Rate-Limits-What-You-Need-to-Know)):
- Free models allow 20 requests/minute.
- They allow **50 requests/day until you have bought $10 of credits, then 1,000/day**.
- Paid models have no OpenRouter-imposed request cap.

| Item | Cost | What it buys |
|---|---|---|
| **Buy $10 OpenRouter credits on day 1** | $10 | Free models go from 50 to **1,000 requests/day**, about 10,000 generated programs over the campaign. The credits stay available for paid models |
| Paid judge (the $10 of credits) | ≤ $10 | Judge, skeptic and issue drafts for the top patterns only (P5) |
| Reserve | $10 | Only if the review queue is still too large in week 2 |

**Judge cost estimate.** These are list prices from an [Aug 2026 comparison](https://www.spheron.network/blog/llm-api-pricing-comparison-gpt-claude-gemini-deepseek-2026/);
check current prices before buying. A judged case is about 3 calls of about 8k input and 1k output
tokens:

| Judge model | ≈ $ per judged case | Cases per $10 |
|---|---|---|
| DeepSeek V4-Pro | 0.013 | ≈ 750 |
| Gemini 3.1 Pro / GPT-5.6 Terra | 0.07 | ≈ 140 |
| Claude Sonnet 5.5 | 0.08 | ≈ 125 |

Rules:
- **Free models generate, never judge.** A hallucinated program costs CPU time; a hallucinated
  verdict loses bugs. Generation is cheap to verify: preflight lint, the checkers and CPython.
- **Judge patterns, not findings.** `typediff triage` groups hundreds of findings into tens of
  patterns. Judge one representative per pattern.
- **Use a different vendor for the skeptic than for the judge** when you add paid judging.
- **Responses are cached** (`~/.cache/typediff/llm`), so re-runs are free. `--max-llm-calls` caps
  a run.
- Free models may log prompts. That's fine here: only generated open-source-style test programs
  are sent.

---

## 6. Triage checklist (one candidate pattern)

This is what we did for the `Self` bug:

1. **Reproduce with all three checkers and CPython** on the minimal program.
2. **Which spec rule applies?** Quote it from the typing spec. "mypy does it" isn't a reason.
3. **Find the strongest oracle:** a runtime crash, the tool contradicting itself (its own revealed
   type or assignability), or a spec quote. Weak: "pyright agrees".
4. **Generalise:** 3–5 variants. Note which variants pass (they localise the bug, e.g. "only when
   inherited").
5. **Check for duplicates:**
   - astral-sh/ty issues, open and closed (closed ones may be *intended*, like #4212).
   - astral-sh/ruff pull requests (ty's code lives there).
   - For mypy: python/mypy issues.
6. **Playground:** play.ty.dev (it may be newer than 0.0.84) or mypy-play.net. If it no longer
   reproduces, don't file.
7. **File one issue per root cause.** Include the minimal repro, actual vs expected output, the
   spec rule, variants, links to related issues and the playground link.
8. **Record it:** add an entry to `typediff/data/known_upstream.json` with the issue URL, so later
   runs dismiss it as DUPLICATE.

---

## 7. When to stop, mutate or pivot

These rules are built into `typediff`'s strategy and apply per feature area:
- **Mutate harder** after 4 programs with no disagreement: increase interaction depth.
- **Pivot** after 5 programs whose findings are only known patterns.
- **Abandon** an area for this ty version if ≥ 60 % of its dismissals are KNOWN_LIMITATION.
- **Fix the generator** if ≥ 50 % of programs are invalid tests.

Campaign level:
- If by **day 7** P2/P3 have produced no new candidate pattern in two consecutive days, move LLM
  requests to the area with the most recent hits.
- If the review queue grows faster than you can triage, spend paid budget on judging (P5) earlier.

---

## 8. What to submit (track from day 1)

- **Volume:** programs run (hand / harvested / generated), discrepancies, and the share closed
  automatically by category (KB, upstream, cascade, invalid test).
- **Funnel:** discrepancies → review → candidates → confirmed → filed → acknowledged by
  maintainers.
- **Filed issues:** a table with links, symptom class (FALSE_NEGATIVE, …), faulty tool and status.
- **Calibration:** recall on 156 known bugs (`calibration/RESULTS.md`), re-run on the final versions.
- **Dataset:** `dataset.jsonl` from the campaign runs, plus the reduced repros of every confirmed
  finding.
