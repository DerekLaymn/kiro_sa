# SETUP: fuzz/llm-run-2026-10-27

Branch: `fuzz/llm-run-2026-10-27` (created from main; nothing committed yet).
Repo: /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa

## Hardware budget
- nproc = 24; RAM 23 GiB total (about 16 GiB available), swap 23 GiB. (`free -g`)
- **PARALLELISM = 8** (checker workers). Leaves 16 cores and most RAM for the box. Do not exceed 8.

## Environment
- Python 3.13.16, mypy 2.4.0 (compiled: yes), ty 0.0.84, pyright 1.1.400 (a newer 1.1.414 exists; kept 1.1.400).
- pytest and pyright were NOT in the venv; I ran `ensurepip` and `pip install pytest==8.3.5 pyright==1.1.400` into .venv. pip is now present too.
- Housekeeping: stray `/-l` deleted (no other `-l` found). .gitignore now has .venv/, .mypy_cache, .pytest_cache, typediff.egg-info, typediff_out/, runs/, seeds/harvested/ (no duplicates). findings/ and seeds/ stay tracked. The LLM cache lives in ~/.cache/typediff/llm, so no ignore entry is needed.

## Priming
- `typediff fetch-docs`: PASS (all ok; corpus: 861 chunks in ~/.cache/typediff/docs).
- `typediff kb-selftest`: PASS (4/4: KB:TY-REDECLARATION, TY-CALLABLE-DUNDER, TY-STRICT-EQUALITY, TY-SELF-UPPER-BOUND).

## Baseline pytest
`.venv/bin/pytest`: **65 passed, 0 failed** in about 31 s (rc=0). The tree includes the uncommitted tests/test_known_closure_bug.py, scripts/public_issues.py, modified typediff/kb.py and known_upstream.json. These were left untouched. They pass.
Uncommitted before this work: M typediff/data/known_upstream.json, M typediff/kb.py, ?? findings/, scripts/public_issues.py, seeds/dataclasses/overloaded_post_init.py, seeds/tuples_unpacking/partial_unpack_exception.py, tests/test_known_closure_bug.py.

## Pipeline entry points (README.md, FUZZING_PLAN.md)
- Seeds: `typediff --python-version 3.13 seeds seeds/` (recursive; folder name = area). `python scripts/harvest_seeds.py` fills seeds/harvested (git-ignored).
- Generate (LLM variants only, no judging): `typediff --llm ... generate --from-seeds DIR --n 5 --ops feature_crossover,narrowing_construct_swap,runtime_witness --out-dir G --max-llm-calls N`, or `generate --area <area> --n 20 --out-dir G`.
  Here I act as generator: write files straight into `gen/` (no API LLM).
- Judge: `TYPEDIFF_LLM=null typediff --out OUT --python-version 3.13 seeds GEN_DIR` (deterministic: KB, oracles, experiments). Also `typediff run files.py --keep-names` (results go to typediff_out/<case>.{json,md} + dataset.jsonl) and `typediff judge case.py --mypy-out ... --ty-out ... --runtime ...`. `TYPEDIFF_LLM=file:<dir>` allows manual or external-agent judging.
- Triage: `typediff triage OUT_DIR --top 30`.
- Report: `typediff report typediff_out/<case>.json --finding D1`.
- Other: `typediff loop --iterations N [--area A]`, `typediff calibrate`.
- Recommended checker flags: mypy `--python-version 3.12 --check-untyped-defs --show-error-codes --no-incremental`; ty `check --python-version 3.12 --output-format concise`. Run in a dir with no pyproject/ty.toml.
- Generated programs run under CPython, so keep them side-effect free.

## 22 feature areas (typediff/strategy.py AREAS = seed subdir names)
generics_variance, paramspec_concatenate, typevartuple_unpack, protocols, typeddict, overloads, narrowing_builtin, narrowing_user, match_statement, dataclasses, enums_literals, self_classmethods, descriptors_properties, constructors_metaclasses, callables, recursive_aliases, final_classvar, abstract_classes, async_generators, inheritance_mro, tuples_unpacking, gradual_any

Note: strategy.py also has AVOID_FOR_KB (TY-REDECLARATION, TY-CALLABLE-DUNDER, TY-STRICT-EQUALITY, TY-GRADUAL-GENERIC-NARROWING, TY-UNKNOWN-UNION, ...). Avoid these patterns unless they are the hypothesis.

## Known-issues KB (typediff/data/known_upstream.json, 4 entries) - do not duplicate
- TY-1090: only_mypy, `type-var`, constrained TypeVar / PEP 695 bounds (DUPLICATE, open)
- TY-4212: only_mypy, `call-arg`, `Unpack[TypedDict]` kwargs with open TypedDict (DESIGN_DIVERGENCE)
- TY-2255: only_ty, ty silent on override incompatibility involving `Self` (DUPLICATE, open)
- MYPY-9658: only_ty, `unsupported-operator`, rebound inferred lambda (DUPLICATE)
Built-in kb.py entries: TY-REDECLARATION, TY-CALLABLE-DUNDER, TY-STRICT-EQUALITY, TY-SELF-UPPER-BOUND (plus join-vs-union, assignment narrowing).

## Existing seeds (seeds/<area>/, 29 files, 20 of 22 areas covered)
async_generators: generator_send_return.py; callables: positional_only_assignability.py; constructors_metaclasses: new_returns_other.py; dataclasses: dataclass_transform.py, kw_only_initvar_order.py, overloaded_post_init.py (uncommitted); descriptors_properties: descriptor_get_overload.py; enums_literals: enum_members_values.py; final_classvar: final_overrides.py; generics_variance: constrained_typevar.py, pep695_variance_inference.py, typevar_defaults.py; gradual_any: gradual_guarantee.py; inheritance_mro: override_lsp.py; match_statement: class_sequence_patterns.py; narrowing_builtin: len_in_walrus.py; narrowing_user: typeis_generic.py; overloads: literal_flag_overload.py; paramspec_concatenate: decorator_signature.py; protocols: generic_callback_protocol.py, property_vs_attribute.py; recursive_aliases: recursive_type_alias.py, widening_loop.py; self_classmethods: self_classmethod_param.py, self_param_inherited.py, self_runtime_witness.py; tuples_unpacking: partial_unpack_exception.py (uncommitted), variadic_tuples.py; typeddict: readonly_notrequired.py.
**No seed dirs yet for typevartuple_unpack or abstract_classes.** Good targets.

## Prior findings (findings/2026-10-25/, uncommitted) - avoid duplicating
- overloaded_post_init/ (dataclass `__post_init__` with overloads; ISSUE_DRAFT.md, repro.py, verify.py, evidence)
- partial_unpack_exception/ (partial tuple unpacking raising at runtime; same layout)
- lambda_rebinding.py and variadic_callback.py (evidence in evidence/{pinned,current})
- Top-level README.md and verify.py
New deliverables go to findings/2026-10-27-llm-run/ (empty so far).

## Campaign directories
- .agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27 (this file)
- .agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen
- .agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out
- findings/2026-10-27-llm-run
