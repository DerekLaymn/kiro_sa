#!/usr/bin/env python
"""Fixed-seed stratified 20% hold-out split of the seed corpus (strata: harvest source, plus 'hand').

    python scripts/kbloop_split.py seeds docs/kb-loop-split

Writes holdout.txt and tuning.txt (one seed path per line). KB entries and matchers may be written and tuned
ONLY from the tuning set; the hold-out is used to measure overfitting. Deterministic: re-running yields the same
split as long as the seed files are the same (a path set change only moves the new files).
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

SEED = "typediff-kbloop-2026"


def stratum(path: Path) -> str:
    if "harvested" in path.parts:
        return path.name.split("__", 1)[0]
    return "hand"


def main(seeds: str, out: str) -> None:
    groups = defaultdict(list)
    for f in sorted(Path(seeds).rglob("*.py")):
        groups[stratum(f)].append(str(f))
    hold, tune = [], []
    for k, files in sorted(groups.items()):
        ranked = sorted(files, key=lambda p: hashlib.sha256(f"{SEED}:{p}".encode()).hexdigest())
        n = max(1, round(len(files) * 0.2))
        hold += ranked[:n]
        tune += ranked[n:]
        print(f"{k}: {len(files)} programs, {n} hold-out")
    Path(out).mkdir(parents=True, exist_ok=True)
    Path(out, "holdout.txt").write_text("\n".join(sorted(hold)) + "\n")
    Path(out, "tuning.txt").write_text("\n".join(sorted(tune)) + "\n")
    print(f"hold-out {len(hold)}, tuning {len(tune)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
