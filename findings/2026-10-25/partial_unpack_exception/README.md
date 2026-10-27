# Candidate new bug: partial stores during nested unpacking

**Result:** a reproducible ty false negative, with no matching filed issue found
in the duplicate checks described below. This is a new generated seed, separate
from the previously known lambda and TypeVarTuple findings.

- [Minimal reproducer](repro.py)
- [Upstream issue draft](ISSUE_DRAFT.md), saved locally and not posted
- [Mutation/control generator and verifier](verify.py)
- Seed corpus entry: `seeds/tuples_unpacking/partial_unpack_exception.py`
- `evidence/pipeline/repro.json` and `.md`: unmodified pipeline judgment
- `evidence/current-matrix.json` and `pinned-matrix.json`: checker commands,
  output, exit codes, source, and direct Python results for all 13 variants
- `evidence/novelty-audit.json`: duplicate search coverage and results

## What fails

Python completes the first store in `value, (a, b) = "bad", items`, then the
nested unpack raises `ValueError`. Ty incorrectly treats `value` as the old
integer in the handler and permits `.bit_length()`. Python sees a string and
raises `AttributeError`. Mypy detects the error; pyright shares the false negative.

Both ty 0.0.84 and 0.0.91 reproduce it. It remains with `--error all`. A guarded
control is accepted by all tools and runs successfully. Splitting the two stores
into separate statements makes ty catch the error, which isolates the missing
flow state to a nested assignment target.

## Search and validation work

The initial generated screens covered 127 call/attribute/tuple-length programs,
212 dataclass programs, 87 operator programs, and 36 control-flow programs.
The control-flow screen led to the nested-unpacking mutation. The final focused
matrix covers 13 variants on each of the two ty versions. The direct Python
checks are independent of the runtime harness.

Older operator leads were excluded after finding existing ty issues #630 and
#1150. The earlier mypy lambda lead is now a narrow KB duplicate of mypy#9658.
The TypeVarTuple lead is recorded as potentially covered by ty#4152, using a
review-only prior rather than automatically dismissing all related behavior.

Public issue research uses ordinary unauthenticated HTTPS downloads. No GitHub
integration, account token, security key, or external write is involved.
3,871 issue titles/bodies were saved in
`runs/novelty/public-github/issues.jsonl`; comments are not included. GitHub's
public rate limit interrupted pagination, so the snapshot is explicitly marked
incomplete and its cursor is saved for later resumption.

Targeted public searches covered both open and closed issues, body text as well
as titles, and related Ruff PRs. The relevant results were read, including the
checkpoint implementation and existing exception-flow tests. None was a matching
report of partial stores before nested-unpacking failure. This supports treating
the finding as a candidate new report; it cannot prove that nobody has discussed
it in unindexed comments or elsewhere.

## Replay from repository root

Use Python 3.13 with the checkers installed next to the interpreter:

```bash
PYTHONPATH=. /tmp/typediff-current/bin/python \
  findings/2026-10-25/partial_unpack_exception/verify.py --out runs/unpack-replay

PYTHONPATH=. /tmp/typediff-current/bin/python -m typediff.cli \
  --llm null --python-version 3.13 --no-reduce --out runs/unpack-pipeline \
  run seeds/tuples_unpacking/partial_unpack_exception.py --keep-names
```

The pipeline's stored tier remains REVIEW because no LLM adjudicator was used.
It attaches strong, verified runtime evidence to the mypy/ty discrepancy. The
manual bug assessment and novelty assessment are recorded separately in this
directory; no automatic verdict has been rewritten.

Search the downloaded corpus without network access:

```bash
python scripts/public_issues.py search --out runs/novelty/public-github \
  --pattern 'nested unpacking|partial unpack|partially assigned'
```

Resume the public download after the rate limit resets:

```bash
python scripts/public_issues.py download --repo astral-sh/ty \
  --out runs/novelty/public-github
```
