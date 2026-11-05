"""Day 7 morning: which typediff feature areas (typediff/strategy.py AREAS) have no parent in runs/hits?

    .venv/bin/python campaign/day7/partB/areas_without_hits.py

Prints every area with its parents (area taken the way `typediff generate --from-seeds` takes it: the `# area:` header,
else the folder name) and the hand seeds under seeds/<area>/."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from typediff.cli import _seed_area  # noqa: E402
from typediff.strategy import AREAS  # noqa: E402

by = defaultdict(list)
for p in sorted((ROOT / "runs/hits").glob("*.py")):
    by[_seed_area(p, p.read_text(), "gradual_any")].append(p.name)
print(f"{'area':26} {'parents':>7} {'hand seeds':>10}")
for a in AREAS:
    seeds = len(list((ROOT / "seeds" / a).glob("*.py"))) if (ROOT / "seeds" / a).is_dir() else 0
    print(f"{a:26} {len(by.get(a, [])):7} {seeds:10}")
print("\nareas with no parent in runs/hits:", [a for a in AREAS if a not in by])
