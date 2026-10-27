# Candidate new mypy false positive: overloaded dataclass post-init hook

This finding is independent of the earlier ty nested-unpacking candidate.
Mypy 2.4.0 rejects a compatible overload set for `__post_init__`; ty and pyright
accept it. The generated dataclass initializer has a matching overload, the
implementation handles its input correctly, and Python runs the program.

- [Minimal reproducer](repro.py)
- [Local issue draft](ISSUE_DRAFT.md)
- [Offline mutation/control verifier](verify.py)
- Seed: `seeds/dataclasses/overloaded_post_init.py`
- Evidence: `evidence/current-matrix.json`, `pinned-matrix.json`, pipeline
  reports, source excerpts, and `novelty-audit.json`

## Discovery and validation

This follow-up screened 192 generator programs, 243 generic-alias/inheritance
programs, and 252 dataclass post-init programs. Some generated cases contain
identical source under different template settings; these are execution counts,
not counts of unique root causes.

The generator/protocol findings were excluded because the previously retrieved
upstream PR ruff#27598 describes that missing validation. Recursive-bound/default
mypy internal-error cases were retained as potential duplicates of mypy#21128
and #8320, rather than claimed as new crashes.

The dataclass screen led to the overloaded-hook finding. Its focused verifier
checks 12 variants, with normal mypy, strict mypy, ty, pyright, and direct CPython
execution. It includes valid controls, the ordinary-method override comparison,
reversed overload order, an extra-arity overload, and invalid negative controls.

## Novelty checks

Public issue search results were downloaded with ordinary unauthenticated HTTPS
before the request to stop network access. All 28 returned issues/PRs containing
`__post_init__` in their title or body were downloaded and inspected for relevance.
Additional searches covered `InitVar` plus `overload`, `post_init` plus
`overloaded`, and related issue and PR spellings. No matching report was found.

The existing signature-validation reports #15498, #9254, and PR #15503 were
reviewed. They establish the intended validation but do not describe this false
positive. The exact queries, result counts, and related report titles are saved
in the novelty audit. Comments were not exhaustively downloaded; novelty is a
best-effort conclusion, not proof that no prior discussion exists.

All subsequent validation runs use local tools and downloaded sources only.
No issue, comment, commit, or push was made.

## Replay offline from the repository root

```bash
PYTHONPATH=. /tmp/typediff-current/bin/python \
  findings/2026-10-25/overloaded_post_init/verify.py --out runs/postinit-replay

PYTHONPATH=. /tmp/typediff-current/bin/python -m typediff.cli \
  --llm null --python-version 3.13 --no-reduce --out runs/postinit-pipeline \
  run seeds/dataclasses/overloaded_post_init.py --keep-names
```

The pipeline's automatic verdict remains REVIEW because no LLM judge was used.
Its runtime-success evidence is correctly weak: successful execution alone does
not establish a false positive. The manual assessment additionally uses the
downloaded callable-assignability specification, ordinary-override control, and
checker-source inspection, as explained in the issue draft.
