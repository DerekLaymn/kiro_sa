"""Does the crash dedupe give the same answer for the replay source and the promoted hits file of the same program?"""
import json
from pathlib import Path

from typediff.crash_upstream import match_crash

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
pairs = [
    ("seed-50a85e2bdd8d", "d3p_crash_ty_stack_overflow_protocol_flatten.py", "ty", "ty:signal-SIGABRT:stack-overflow"),
    ("seed-918936c5da72", "d3p_crash_mypy_segv_recursive_tvt_default_alias.py", "mypy", "mypy:signal-SIGSEGV"),
    ("seed-dc88d8cc6015", "d3p_crash_ty_panic_partial_or_none_in_loop.py", "ty",
     "ty:panic@/root/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/salsa-0.28.5/src/function/execute.rs:751:9"),
    ("seed-23cf4835dc66", "d3p_crash_ty_timeout_typeis_generic_in_loop.py", "ty", "ty:timeout"),
]
for sid, fname, tool, sig in pairs:
    rep = json.loads((R / "runs/day3/replay" / f"{sid}.json").read_text())
    rsrc = rep["source"]
    hsrc = (R / "runs/hits" / fname).read_text()
    a = match_crash(rsrc, tool, sig)
    b = match_crash(hsrc, tool, sig)
    print(fname, "| replay source ->", a and a.get("id"), "| hits file ->", b and b.get("id"))
    print("   replay crashes:", [(c["signature"][:50]) for c in rep["crashes"]], "| replay findings:",
          [(x["discrepancy_id"], x["tier"], x.get("dismissal"), x["decided_by"]) for x in rep["findings"]])
