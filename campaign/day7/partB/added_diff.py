"""Day 7 part B: what does `--pyright-only` add to a replayed run?

    python campaign/day7/partB/added_diff.py runs/day7/day6replay runs/day7/day6replay-pyright

Prints (1) whether every finding of the old replay is unchanged in the new one (same id, kind, tier, dismissal,
decided_by), (2) every added finding (only_pyright), grouped by runtime relation and pyright rule, with seed, line,
statement and pyright message."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def rows(report: dict) -> dict:
    ds = {d["id"]: d for d in report["discrepancies"]}
    out = {}
    for f in report["findings"]:
        d = ds.get(f["discrepancy_id"], {})
        out[f["discrepancy_id"]] = (d.get("kind", "crash"), f["tier"], f.get("dismissal"), f["decided_by"])
    return out


def main(old: Path, new: Path) -> int:
    changed, added, total, progs = [], [], 0, Counter()
    for fo in sorted(old.glob("seed-*.json")):
        ro_j, rn_j = json.loads(fo.read_text()), json.loads((new / fo.name).read_text())
        ro, rn = rows(ro_j), rows(rn_j)
        total += len(ro)
        for k, v in ro.items():
            if rn.get(k) != v:
                changed.append((fo.stem, k, v, rn.get(k)))
        ds = {d["id"]: d for d in rn_j["discrepancies"]}
        for k, v in rn.items():
            if k not in ro:
                d = ds[k]
                if v[0] != "only_pyright":
                    changed.append((fo.stem, k, None, v))
                    continue
                added.append((fo.stem, d, v))
                progs[fo.stem] += 1
    print(f"old findings compared: {total}; old findings changed or missing in the new run: {len(changed)}")
    for c in changed:
        print("  CHANGED", c)
    print(f"added findings: {len(added)} in {len(progs)} programs")
    print("by runtime relation:", dict(Counter(d["reveal_relation"] for _, d, _ in added)))
    print("by tier / decided_by:", dict(Counter((v[1], v[3]) for _, _, v in added)))
    print("by pyright rule:", dict(Counter(p["code"] for _, d, _ in added for p in d["pyright"] if p["severity"] == "error")))
    for seed, d, v in added:
        msg = "; ".join(f"{p['code']}: {p['message'][:90]}" for p in d["pyright"] if p["severity"] == "error")
        print(f"{seed} {d['id']} L{d['anchor']} {d['reveal_relation']} {d['statement'][:60]!r}\n    {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
