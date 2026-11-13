# Knowledge base

The knowledge base (KB) is the list of reasons a disagreement between checkers is **not** a bug worth reporting: a
documented design difference, a known limitation, a version or configuration artefact, or an issue that was already
reported upstream. It is what lets the deterministic judge close most discrepancies without a person reading them.

The KB never reports anything; it only dismisses. An entry that is too broad can hide a real bug, so entries are narrow,
CPython can veto them, and each is tested with near-miss controls. Every dismissal names the entry that did it
(`decided_by: kb:<ID>`), so a wrong entry can be found and fixed.

## What is in it

| Part | File | Content |
|---|---|---|
| Code entries | `typediff/kb.py` | 48 `KBEntry` objects with matcher functions, optional verifying experiments and canonical examples. |
| Upstream entries | `typediff/data/known_upstream.json`, key `entries` | 27 discrepancy entries, each turned into a `KBEntry` named `UPSTREAM-<id>` at import time, and 12 crash entries. Each links to a tracker issue. |
| Prior stances | same file, key `prior_stances` (plus entries that carry a `stance`) | Notes that a tracker has taken a position. They never dismiss; they only cap a finding at `review` and put the link into an issue draft. 7 stances plus the entries that carry `stance`. |
| Rule table | `typediff/data/ty_rule_map.json` | Pairs ty rules with mypy codes and pyright rules, from ty's own migration guide. |
| Controls | `calibration/`, `tests/` | Programs and tests that check the entries from outside. |

Counts are for the final commit of this repository. `typediff kb-selftest` re-runs the canonical example of the 20
entries that have one; the others are covered by the tests.

## What an entry looks like

A code entry in `typediff/kb.py`:

```python
KBEntry(
    "TY-CALLABLE-DUNDER",                                   # id
    "ty rejects __name__/__qualname__/... on Callable-typed values",   # title
    Dismissal.DESIGN_DIVERGENCE,                            # dismissal category
    f"{TY_DOCS}/reference/typing-faq/#why-does-ty-say-callable-has-no-attribute-__name__",   # source
    "Not every callable has function attributes ... (explanation for readers and for the LLM)",  # text
    (K.ONLY_TY,),                                           # discrepancy kinds the entry may explain
    m_callable_dunder,                                      # matcher: (CaseState, Discrepancy) -> bool
    auto=True,                                              # may dismiss on its own
    # runtime_override=True is the default: CPython can veto the entry
    # verify=..., demote=...                                optional, see the table below
    example="from typing import Callable\ndef g(c: Callable[[int], str]) -> str:\n    return c.__name__\n",
)
```

| Field | Meaning |
|---|---|
| `id` | Unique, upper-case, stable. Appears in reports as `kb:<id>`. |
| `dismissal` | One of the [dismissal categories](architecture.md#symptoms-evidence-and-dismissals). |
| `source` | URL of the documentation or issue that justifies the entry. |
| `text` | What the difference is, what the matcher requires, and what is not covered. Be explicit about the limits. |
| `kinds` | Discrepancy kinds the entry applies to: `only_mypy`, `only_ty`, `reveal_mismatch`, and so on. |
| `matcher` | A function of the case state and the discrepancy. It must be **narrow**: it should fire on the documented shape and on nothing else. |
| `auto` | `False`: hint only, shown to the LLM and never dismissing. `True`: dismisses when the matcher fires. |
| `runtime_override` | `True` (default): if CPython contradicts the entry's implied claim (a type-related exception in this statement, or a runtime value outside the more precise type), the entry is demoted to a hint and the case goes on to review or the LLM. |
| `runtime_override_kinds` | Kinds for which a runtime contradiction demotes the entry even when `runtime_override` is `False`. |
| `verify` | An experiment that must confirm the entry, for example "the discrepancy disappears with `--enable-error-code X`". Built with `_toggle(tool, flags)`. A verify-required entry dismisses only after its **own** experiment ran for this discrepancy and removed it. |
| `demote` | A function returning an explanation when the entry must not dismiss this case. The case then stays in review with the explanation as a note. |
| `example` | A canonical program that `kb-selftest` runs. The entry must be the `decided_by` of one finding. |

Trust levels, from weakest to strongest: hint only (`auto=False`); automatic (`auto=True`); automatic with
verification (`auto=True`, `verify=...`).

## How matching works

For each discrepancy `d` of a program (`rules.deterministic_stage`):

1. `matching_entries` collects every entry whose `kinds` contain `d.kind` and whose matcher returns true. A matcher that
   raises is treated as "no match", so a broken entry cannot break a run. Upstream entries are checked **first**: an
   exact upstream match beats a generic explanation.
2. Hint-only entries that carry a `verify` experiment are shown only if the experiment confirms them.
3. For each automatic entry, in order:
   - `entry_demotion` asks whether CPython contradicts the entry or the entry's own `demote` fires. If so the entry only
     adds evidence and the next entry is tried.
   - If the entry needs verification, its own experiment must have run for this discrepancy with the request the entry
     expects, and the discrepancy must have disappeared. Another entry's experiment does not count.
   - Otherwise the discrepancy is dismissed with `decided_by: kb:<ID>` and confidence 0.9 (0.95 with verification).
4. A sample of dismissals (`--audit-rate`, default 5 %, only with an LLM) is sent back to the LLM judge and advocate.

Crash findings have no discrepancy, so they never reach this matcher; see [crash entries](#crash-entries).

## Entries in `known_upstream.json`

Use this file when a discrepancy or crash is **already reported upstream**, so the pipeline stops re-triaging it. File
format (the `_doc` key of the file repeats it):

```json
{
  "id": "TY-4941",
  "kind": "only_pyright",
  "codes": ["reportArgumentType"],
  "message": "cannot be assigned to parameter \"\\w+\" of type \"Hashable\"",
  "requires": "eq_without_hash_argument",
  "dismissal": "DUPLICATE",
  "url": "https://github.com/astral-sh/ty/issues/4941",
  "note": "open (state on a date): ty accepts an instance of a class that defines __eq__ and no __hash__ for a Hashable parameter although CPython raises TypeError ..."
}
```

(Shortened from the real entry. Optional fields not shown here are `silent_tool`, `statement`, `source`, `stance`,
`demote_on_exception` and `example`.)

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Becomes the KB id `UPSTREAM-<id>`. |
| `kind` | yes | `only_mypy`, `only_ty`, `reveal_mismatch`, `reveal_unpaired`, `concern_mismatch`, `only_pyright` or `crash`. |
| `silent_tool` | no | For an `only_ty` entry with `silent_tool: "ty"`, the regexes are matched against pyright's diagnostics (a pyright-only concern that ty and mypy miss). |
| `codes` | no | Diagnostic codes of the reporting tool. Empty means any code. |
| `message` | yes (not for crash) | Regex over the diagnostic message. For `only_pyright` it is matched against pyright's messages. |
| `statement` | no | Regex over the first line of the statement. |
| `source` | no | Regex over the whole program. |
| `requires` | no for discrepancies | Name of a function in `kb._REQUIRES` that must also accept the case. Use it whenever the message alone is not specific enough. |
| `dismissal` | yes | `DUPLICATE` for an open issue, `DESIGN_DIVERGENCE` when the issue was closed as intended. |
| `stance` | no | `open`, `intended`, `not_planned` or `duplicate-of`. Used by the prior-stance check. |
| `url` | yes | The tracker issue. |
| `note` | yes | What the report says and the state on a date. Keep the date; issue states change. |
| `demote_on_exception` | no | `true`: step aside when CPython raised a type-related exception in that statement. |
| `example` | no | A program; adds the entry to `kb-selftest`. |

### Crash entries

A crash entry (`"kind": "crash"`) closes a known checker crash as `DUPLICATE`. It is matched by
`crash_upstream.match_crash` and needs **all** of:

- `tool`: the crashing tool equals the entry's tool (`mypy`, `ty` or `pyright`). One entry per tool.
- `signature`: a regex, matched with `re.fullmatch` against the crash signature such as
  `ty:signal-SIGABRT:stack-overflow`, `mypy:signal-SIGSEGV` or `pyright:internal:RangeError`.
- `requires`: the name of a function in `crash_upstream._CRASH_REQUIRES` that accepts the parsed program. This is
  mandatory. Several different ty bugs share one signature, so tool and signature alone must never close a crash.

A crash that matches nothing stays live. A crash with the same signature as an earlier finding is **not** closed as a
duplicate either; it gets a note to compare the programs.

### Prior stances

A prior stance records that a maintainer already took a position (for example "intended behaviour") without covering the
whole shape. It matches by message, codes, statement and source regexes, or by feature `tags` that must all be present.
It never dismisses. When a would-be `confirmed` or `candidate` finding matches, `priors.apply_prior_cap` lowers it to
`review` and adds a note with the stance and URL. `typediff report` puts the same warning at the top of the draft.

## Adding an entry

1. **Reproduce the difference** with the pinned tools (`typediff doctor`) and read the tracker issue or documentation
   page. Search issue bodies, not only titles.
2. **Choose the form.**
   - Already reported and describable by a regex plus, if needed, a small AST predicate: add a `known_upstream.json`
     entry. Put the predicate in `kb._REQUIRES` (discrepancies) or `crash_upstream._CRASH_REQUIRES` (crashes).
   - A documented design difference with its own logic: add a `KBEntry` to `typediff/kb.py` (append to the last
     `ENTRIES.extend([...])` block, before `ENTRIES[:0] = _upstream_entries()`).
   - A position that does not cover a whole shape: add a `prior_stances` item.
3. **Make the matcher as narrow as the documentation.** Say in `text` what it covers and what it does not.
4. **Decide the CPython policy.** Leave `runtime_override=True` unless the difference is about something CPython cannot
   show, such as a reveal or a missing check. Add a `demote` function if a runtime failure of a particular shape means
   the entry is wrong.
5. **Add tests**, in a new or existing file under `tests/`:
   - a positive: the exact shape is closed by exactly this entry;
   - **near-miss controls**: the same shape without the trigger, a different dunder, a different code, a rebound variable.
     Each must stay live. The controls are what prevent the entry from swallowing a real bug;
   - the other answers: the same program with a different message from the same tool must stay live.
   `tests/test_upstream_round7.py` is a good model. It builds discrepancies by hand with the `ids(...)` helper of
   `tests/test_upstream_round6.py` and asserts which entry ids fire.
6. **Add a calibration program** when the shape is a real discrepancy that should stay closed:
   `calibration/known_duplicates/<name>.py`, with an assertion that exactly one named entry closes it. Programs that no
   dismissal may touch go in `calibration/must_stay_live/` (it is empty at the final commit by decision; see its README).
7. **Run** `pytest`, `typediff --python-version 3.13 kb-selftest` and, if you changed rules that affect many programs,
   `python scripts/kbloop_replay.py OLD_OUT NEW_OUT --verify-sample 30` over a saved run to see which findings changed
   and to confirm that a full re-run gives the same answers as the replay.
8. **Read every finding the new entry closes** on a saved run before you trust it.

## Controls and tests

| Where | What it protects |
|---|---|
| `typediff kb-selftest` | Every entry with an `example` still fires on the installed tool versions. 20 `PASS` expected. |
| `calibration/negatives/` | Documented differences that must be closed automatically. |
| `calibration/known_duplicates/` | Real discrepancies tracked upstream; each must be closed by exactly one named entry. |
| `calibration/must_stay_live/` | Programs no dismissal may touch (empty by decision). |
| `calibration/positives.json` | 156 open bug reports; none of the ty reports may be dismissed. |
| `tests/test_upstream_*.py`, `tests/test_stage3_*.py`, `tests/test_kb*.py` | Positives and near-miss controls for upstream and code entries. |
| `tests/test_audit_fixes.py`, `tests/test_kbloop_*.py` | Regressions for false dismissals found earlier. |
| `tests/data/upstream_round*/` | Real reproducers and controls used by the upstream tests. |

See [calibration/README.md](../calibration/README.md) and [tests/README.md](../tests/README.md).

## Reading the entry list

The built-in code entries, by group (ids as in `kb.py`):

- **Documented ty design:** `TY-REDECLARATION`, `TY-CALLABLE-DUNDER`, `TY-STRICT-EQUALITY`,
  `TY-GRADUAL-GENERIC-NARROWING`, `TY-UNKNOWN-UNION`, `TY-TODO`, `TY-SELF-UPPER-BOUND`.
- **Checks one tool does not have:** `TY-CHECK-NOT-IMPLEMENTED`, `TY-CHECK-MISSING-JUDGE-MYPY` (hint), `TY-CHECK-PARTIAL`,
  `TY-ONLY-CHECK`, `MYPY-OPTIONAL-CHECK`, `MYPY-UNTYPED-DEFS`, `MYPY-UNBOUND-OPT-IN-CHECK`.
- **Inference and display differences:** `BOTH-GRADUAL`, `LITERAL-WIDENING`, `JOIN-VS-UNION`,
  `JOIN-VS-UNION-CALLABLE`, `PRECISION-RUNTIME-CONSISTENT`, `INFERENCE-DOWNSTREAM`, `DISPLAY-EQUIVALENT`,
  `ASSERT-TYPE-LITERAL-RETENTION`, `MYPY-FIRST-ASSIGNMENT-TYPE`, `REVEAL-ERROR-RECOVERY`.
- **Reachability and environment:** `MYPY-SKIPS-UNREACHABLE`, `REACHABILITY-VS-COVERAGE`, `ENV-IMPORT`, `STUB-SKEW`,
  `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED`, `MYPY-SUITE-ALLOW-EMPTY-BODIES`.
- **Suppression:** `SUPPRESSION-SEMANTICS`, `SUPPRESSION-LINE`.
- **Specific mypy and ty behaviours:** `ANNOTATION-ONLY-READ`, `MYPY-15182-NEW-RETURNS`, `MYPY-13807-ALIASED-CONDITIONS`,
  `MYPY-8595-METACLASS-CALL`, `CALLABLE-SELF-ATTR-STORE`, `CALLABLE-SELF-RECEIVER`, `MDTEST-TODO`.
- **Oracle helpers:** `ORIGIN-ORACLE-REVEAL`, `ORIGIN-ORACLE-NOTE`, `ORIGIN-MISMATCH`, `EXPECTED-ERROR-ORACLE`,
  `SUITE-EXPECTS-ERROR`, `PYRIGHT-REVEAL-EXPECTED-KWARG`.
- **Leads for the LLM (hint only):** `GRADUAL-OPERAND`, `ERROR-CASCADE`, `PARTIAL-TYPES`.

Two rules sit next to the KB: `rule:cascade-of:Dn` (a diagnostic downstream of an already dismissed rejection by the same
checker) and `rule:undefined-name` (the statement depends on names both checkers report as undefined, so the repro is
incomplete). The design notes for the most important entries are in [design.md](design.md#42-knowledge-base-kbpy).

## Keeping the KB valid

- Entries are version specific. After upgrading a checker, run `typediff kb-selftest` and the test suite; an entry whose
  upstream issue was fixed should be removed or marked fixed, as happened for the two ty issues fixed in 0.0.97.
- `typediff fetch-docs --refresh-rule-map` refreshes `ty_rule_map.json` from the ty documentation.
- Record the date of the tracker state in each `note`. Issue states change.
