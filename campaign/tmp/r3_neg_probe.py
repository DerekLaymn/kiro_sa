"""Run candidate programs through the real pipeline (no pyright, no LLM) and print findings + raw diagnostics."""
import sys
from pathlib import Path

from typediff.llm import CachedLLM, NullLLM
from typediff.models import Tool
from typediff.pipeline import Pipeline, PipelineConfig

pyr = "--pyright" in sys.argv
p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=pyr), llm=CachedLLM(NullLLM()))
for f in [a for a in sys.argv[1:] if not a.startswith("--")]:
    src = Path(f).read_text()
    rep = p.run_source(src, "probe")
    print("=====", f)
    print(src)
    print("runtime:", rep.runtime.status, getattr(rep.runtime, "exc_type", None))
    for x in rep.findings:
        print("  ", x.discrepancy_id, x.tier.value, x.decided_by)
    for d in rep.discrepancies:
        print("   D", d.id, d.kind.value, "L", d.anchor, "rel", d.reveal_relation, "hints", d.kb_hits)
        for t in ("mypy", "ty", "pyright"):
            for y in getattr(d, t):
                print("      ", t, y.line, y.col, y.code, (y.revealed_type or y.message)[:100])
