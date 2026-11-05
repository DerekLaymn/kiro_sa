"""List the findings of a replayed run, one line each: python live_dump.py REPLAY_DIR [--live] [--diff OTHER_DIR].

Without --diff: every finding (seed, program, discrepancy id, kind, tier, decided_by, statement, tool messages).
With --diff OTHER_DIR: only findings whose (tier, decided_by) differ between the two directories."""
import json
import sys
from pathlib import Path


def load(d: Path):
    out = {}
    for f in sorted(d.glob("seed-*.json")):
        r = json.loads(f.read_text())
        ds = {x["id"]: x for x in r["discrepancies"]}
        origin = next((n.split("=", 1)[1] for n in r.get("notes", []) if n.startswith("origin=")), "?")
        for fi in r["findings"]:
            did = fi["discrepancy_id"]
            dd = ds.get(did)
            out[(f.stem, did)] = {
                "seed": f.stem, "origin": origin, "id": did, "kind": dd["kind"] if dd else "crash",
                "tier": fi["tier"], "dismissal": fi.get("dismissal"), "by": fi["decided_by"],
                "line": dd["anchor"] if dd else None, "stmt": dd["statement"] if dd else "",
                "mypy": [(x.get("code"), x["message"][:90], x.get("revealed_type")) for x in dd["mypy"]] if dd else [],
                "ty": [(x.get("code"), x["message"][:90], x.get("revealed_type")) for x in dd["ty"]] if dd else [],
                "notes": fi.get("review_notes", [])[:3],
            }
    return out


def show(v):
    print(f"{v['seed']} {Path(v['origin']).name}")
    print(f"   {v['id']} {v['kind']} tier={v['tier']} dismissal={v['dismissal']} by={v['by']} L{v['line']}: {v['stmt'][:100]}")
    for t in ("mypy", "ty"):
        for x in v[t]:
            print(f"      {t}: {x}")
    for n in v["notes"]:
        print(f"      note: {n[:160]}")


def main():
    a = load(Path(sys.argv[1]))
    if "--diff" in sys.argv:
        b = load(Path(sys.argv[sys.argv.index("--diff") + 1]))
        n = 0
        for k in sorted(a):
            if k in b and (a[k]["tier"], a[k]["by"]) != (b[k]["tier"], b[k]["by"]):
                n += 1
                print(f"--- was tier={b[k]['tier']} by={b[k]['by']}  ->  now tier={a[k]['tier']} by={a[k]['by']}")
                show(a[k])
        print(f"{n} findings changed")
        return
    live_only = "--live" in sys.argv
    n = 0
    for k, v in sorted(a.items()):
        if live_only and v["tier"].lower() == "dismissed":
            continue
        n += 1
        show(v)
    print(f"{n} findings listed")


main()
