#!/usr/bin/env bash
# run the pipeline on the new negative + must-stay-live files and print tiers/deciders
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/python - <<'EOF'
from pathlib import Path
from typediff.llm import CachedLLM, NullLLM
from typediff.pipeline import Pipeline, PipelineConfig
p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
for f in ["calibration/negatives/reveal_error_recovery.py", "calibration/must_stay_live/ty_constant_fold_tuple_subclass.py",
          "calibration/negatives/assert_type_literal_retention.py", "calibration/negatives/mypy_aliased_condition.py"]:
    rep = p.run_source(Path(f).read_text(), f)
    print(f, [(x.discrepancy_id, x.tier.value, x.decided_by) for x in rep.findings])
EOF
