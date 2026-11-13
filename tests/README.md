# Tests

```bash
pytest -q                       # 762 passed in about 3 minutes (pinned tools installed)
pytest -q tests/test_reproducibility.py
```

The suite needs mypy, ty and pyright at the pinned versions (see [constraints.txt](../constraints.txt)); several tests
run the real checkers. No test calls an LLM or needs an API key. With other tool versions some tests can fail because
messages, reveals or KB matches differ; `typediff doctor` shows which versions you have.

File names contain generation-round numbers (`round8`, `stage3_round2`) or `kbloop`. The table groups them by topic.

| Topic | Files |
|---|---|
| KB entries and matchers | `test_kb.py`, `test_kbloop_entries.py`, `test_kbloop_upstream.py`, `test_stage3_round1.py`, `test_stage3_round2.py`, `test_stage3_round3.py`, `test_round8_pipeline.py`, `test_round9_pipeline.py`, `test_round10_pipeline.py`, `test_round10_entries.py` |
| Upstream entries (positives and near-miss controls) | `test_upstream_round3.py` to `test_upstream_round7.py`, `test_known_closure_bug.py` |
| Crash detection and process handling | `test_crash_detection.py`, `test_runner_timeout_kills_group.py` |
| Runtime oracle and evidence | `test_evidence.py`, `test_runtime_miss.py`, `test_harness_annotations.py`, `test_origin_oracle.py`, `test_kbloop_defects.py` |
| Pipeline behaviour and audits | `test_audit_fixes.py`, `test_phase3.py`, `test_pipeline_round5.py`, `test_pyright_only_round7.py` |
| Generation and the file bridge | `test_generate_variants.py`, `test_inbox_check_round5.py` |
| Seed harvesting | `test_harvest_mdtest_env.py` |
| Reproducibility plumbing (`.env`, API-key errors, version pins, replay data, no absolute paths) | `test_reproducibility.py` |

`data/known_closure/` holds the two programs of `test_known_closure_bug.py`.
`data/upstream_round3/`, `data/upstream_round4/` and `data/upstream_round5/` hold the real reproducers and controls that the
upstream tests run through the pipeline: each program is either a crash or a discrepancy that one named entry must close,
or a near-miss control that must stay live.

To add a test for a new KB entry, see [docs/knowledge-base.md](../docs/knowledge-base.md#adding-an-entry).
