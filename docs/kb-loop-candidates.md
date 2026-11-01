# kb-loop candidates

Nothing here is a verified tool bug. Evidence rule (DESIGN.md section 1): a runtime crash, a verbatim spec quote, or call-versus-call
self-contradiction; never a printed revealed signature alone.

## Candidate bugs kept live (not dismissed)

| id | what | minimal repro | evidence so far |
|---|---|---|---|
| C-1 | ty reveals `Unknown` where mypy's own suite blessed a concrete type (imprecision, no unsoundness proven); now dismissed by ORIGIN-ORACLE-REVEAL as DESIGN_DIVERGENCE, so a human should sample them | `seeds/harvested/gradual_any/mypy__check_classes__testAttributeDefOrder2.py` (mypy `int`, ty `Unknown`) | suite expectation only |
| C-2 | pre-existing KB entries dismiss the repros of real ty bug reports (found by calibration, also with the baseline code): ty#4872 (rule:undefined-name), #4835 (BOTH-GRADUAL), #4817 and #4713 (MYPY-OPTIONAL-CHECK), #4786 (LITERAL-WIDENING) | `calibration/positives.json` ids above | calibration run, `runs/tmp/base.txt` |
| C-3 | runtime_miss: 73 programs where CPython raised a type error at a statement and both tools are silent (e.g. `del c.x` on a missing attribute, `Message[str, str]` subscript on a non-generic class) | `seeds/harvested/gradual_any/ty__del__4.py`, `typeshed__email__check_parser.py` | runtime exception (strong), still needs a check that the exception is the intended `# error` of the test |
| C-4 | tool timeouts: 4 ty (match/tuple comparison programs) and 3 mypy (pep695 aliases) hit the 120 s limit | `seeds/harvested/match_statement/pyright__matchSequence2.py`, `recursive_aliases/ty__pep695_type_aliases__70.py` | timeout; see round 2 crash work |

## Ranked list for the next round (round 2 plan)

| rank | block | live (tuning) | action | effort |
|---|---|---|---|---|
| 1 | crash detection defects (crash25-check.md section 6) | 25 crash findings | signal exits, pyright internal error, double-count, excerpt head+tail, signatures, version-skew flag | small |
| 2 | only_mypy (assignment 391, arg-type 141+29, valid-type 108, no-redef 104, attr-defined 72, misc 58+...) | 2627 | find real sources; mypy suite flags (`# flags:`), `tuple[()]` augmented assignment inference | large |
| 3 | only_ty (invalid-assignment 105, invalid-argument-type 101, invalid-return-type 69, empty-body 40, unsupported-operator 21...) | 1569 | most are tests of ty errors where mypy is lenient; group by ty rule, read the ty docs per rule | large |
| 4 | concern_mismatch (assignment 124, arg-type 58+25, valid-type 64) | 706 | pair by concern, check the toggle experiments for concern kinds | medium |
| 5 | assert_type mismatches (230 + 185 + 32 + 22 + 21) | ~490 | pyright-majority view as weak evidence only, spec text for assert_type | medium |
| 6 | pyright `expected_text=` kwarg (59) | 58 | harness noise candidate: pyright-only API | small |
| 7 | harvester: honour `# flags:` of mypy tests and mdtest python-version; record upstream SHAs and tool-version skew | ~300 ORIGIN-MISMATCH | harvester change + re-run of affected programs | medium |
