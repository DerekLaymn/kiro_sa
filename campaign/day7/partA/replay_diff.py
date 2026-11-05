"""Day 7 part A: list every finding whose tier / dismissal / decided_by differs between two replays of the same run.

    python campaign/day7/partA/replay_diff.py runs/day6/replay runs/day7/day6replay

For each changed finding prints the seed, discrepancy, kind, anchor line, statement and old -> new decision. The
program text is not printed (read it with ``jq -r .source <seed>.json``)."""
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
        out[f["discrepancy_id"]] = (d.get("kind", "crash"), d.get("anchor"), (d.get("statement") or "")[:70],
                                    f["tier"], f.get("dismissal"), f["decided_by"])
    return out


def main(old: Path, new: Path) -> int:
    changed, total = [], 0
    for fo in sorted(old.glob("seed-*.json")):
        fn = new / fo.name
        ro, rn = rows(json.loads(fo.read_text())), rows(json.loads(fn.read_text()))
        total += len(ro)
        if set(ro) != set(rn):
            print("DISCREPANCY SET DIFFERS", fo.name)
        for k in sorted(ro):
            if ro[k][3:] != rn.get(k, ro[k])[3:]:
                changed.append((fo.stem, k, ro[k], rn[k]))
    for seed, k, o, n in changed:
        src = json.loads((old / f"{seed}.json").read_text())["source"].splitlines()
        origin = next((x for x in src if x.startswith("# origin:")), "")[:100]
        print(f"{seed} {k} {o[0]} L{o[1]} {o[2]!r}\n    {o[3]}/{o[4]}/{o[5]} -> {n[3]}/{n[4]}/{n[5]}\n    {origin}")
    print(f"\nfindings compared: {total}; changed: {len(changed)}")
    print("new decided_by:", dict(Counter(n[5] for *_, n in changed)))
    print("old decided_by:", dict(Counter(o[5] for _, _, o, _ in changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
