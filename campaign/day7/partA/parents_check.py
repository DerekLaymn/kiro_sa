"""Run every parent in runs/hits through the pipeline (mypy + ty, no pyright) and list findings closed by the Day-7 entries."""
import sys
from pathlib import Path

from typediff.llm import CachedLLM, NullLLM
from typediff.pipeline import Pipeline, PipelineConfig

NEW = {"kb:UPSTREAM-TY-2171", "kb:UPSTREAM-TY-2171-ASSERT", "kb:UPSTREAM-TY-2792", "kb:UPSTREAM-TY-2792-READONLY"}
p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
names = sys.argv[1:]
for name in names:
    path = Path("runs/hits") / name
    rep = p.run_source(path.read_text(), name)
    ds = {d.id: d for d in rep.discrepancies}
    print(name, [(f.discrepancy_id, ds[f.discrepancy_id].kind.value if f.discrepancy_id in ds else "crash", f.tier.value, f.decided_by) for f in rep.findings])
