# Agentic LLM fuzzing pipeline (2026-10-27 run)

Agents played the LLM generator and the LLM judge. The `typediff` CLI did the
differential testing (mypy vs ty, pyright as tie-breaker, CPython as ground truth).
Workflow name: `typediff-llm-fuzz-run`. Straight-line, no review loop.

| Step | Agent | What it did |
|---|---|---|
| setup | wf-coder | Created the branch, checked cores and RAM (24 cores, 23 GiB, 8 workers), ran kb-selftest and pytest (65 passed), listed existing seeds and KB entries to avoid duplicates. |
| generate (4 parallel branches) | wf-coder | A structural (dataclasses, tuples, TypedDict, enums), B generics (variance, ParamSpec, TypeVarTuple, callables), C protocols (descriptors, constructors, MRO), D flow (narrowing, overloads, match, async). 142 programs, disjoint dirs and filename prefixes `genA_`..`genD_`. |
| pipeline | wf-coder | `typediff seeds` over all programs (checkers plus CPython runtime harness), then `typediff triage --details`. 199 discrepancies, 38 auto-dismissed. Output: `disagreements.md`. |
| judge (2 parallel branches) | wf-coder | Judge role: adjudicate each disagreement with CPython runtime, `reveal_type` and spec text. Verdicts: TRUE BUG, SPEC_AMBIGUITY, KNOWN_DUPLICATE, pipeline false positive. |
| reduce | wf-coder | Minimized the TRUE BUG candidates and re-ran the checkers. Output: `candidates.md`. |
| review | semantic_reviewer | Independent re-verification and upstream duplicate check. Output: `REPORT.md`, `review.json`. |
| finalize | wf-coder | pytest, scoped commits, push. |

Artifacts:

- Run logs, manifests, SETUP, disagreements, triage: `.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/`
- Generated programs: `.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/<area>/`
- Findings, reproducers, report: `findings/2026-10-27-llm-run/`

To rerun without an API key, write programs into `gen/<area>/` and run
`typediff seeds` on that directory, then triage and judge by hand.

Known caveats: branch B programs were not CPython-checked by their author (the
pipeline's runtime harness ran them later). pyright 1.1.400 only.
