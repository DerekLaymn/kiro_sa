#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/python - <<'EOF'
from typediff.llm import CachedLLM, NullLLM
from typediff.pipeline import Pipeline, PipelineConfig
p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
C = {
 "unbound_mod": "def g() -> None:\n    value: str\n    reveal_type(value.upper())\n",
 "slots": "class S:\n    __slots__ = ()\n\n\ndef g(s: S) -> None:\n    reveal_type(s.__dict__)\n",
 "implicit_attr": "class C:\n    reveal_type(__qualname__)\n",
 "lambda_unbound": "def g() -> None:\n    n: int\n    reveal_type(n + 1)\n",
}
for k, src in C.items():
    rep = p.run_source(src, k)
    print(k, [(x.discrepancy_id, x.tier.value, x.decided_by) for x in rep.findings])
    for d in rep.discrepancies:
        print("   ", d.id, d.kind.value, [x.short() for x in d.mypy], [x.short() for x in d.ty])
EOF
