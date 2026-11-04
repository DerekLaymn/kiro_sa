"""End-to-end check of the Day-3 upstream entries: every reproducer and every control from tests/data/upstream_day3 goes
through the real pipeline (``TYPEDIFF_LLM=null typediff --out <tmp> seeds <dir>``), one fresh output directory per file
(so the dataset-level duplicate check cannot hide the result), and the decided_by / dismissal of each finding is printed.

usage: python scripts/upstream_day3_check.py [--jobs N] [name ...]
Exit code 1 if an expectation below is violated.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tests" / "data" / "upstream_day3"
TYPEDIFF = ROOT / ".venv" / "bin" / "typediff"

# file -> {(tool, crash signature or finding kind): expected closing id (None: must stay live)}
# crash expectations are keyed "crash:<tool>"; discrepancy expectations "disc:<kind>"
EXPECT: dict[str, dict[str, str | None]] = {
    "ty_TB_protocol_stack_overflow": {"crash:ty": "TY-4882"},
    "t20a": {"crash:ty": "TY-4882"},
    "ty_20": {"crash:ty": "TY-4882"},
    "C1": {"crash:ty": "TY-4898"},
    "C3": {"crash:ty": "TY-4898"},
    "C4": {}, "C5": {}, "C6": {},
    "E1": {"crash:ty": "TY-4899"}, "E2": {"crash:ty": "TY-4899"}, "E6": {"crash:ty": "TY-4899"},
    "E8": {"crash:ty": "TY-4899"}, "E10": {"crash:ty": "TY-4899"},
    "E3": {}, "E4": {}, "E5": {}, "E7": {}, "E9": {},
    "D1": {"crash:ty": "TY-4900", "crash:mypy": "MYPY-22360"},
    "D7": {"crash:ty": "TY-4900", "crash:mypy": "MYPY-22360"},
    "D10": {"crash:ty": "TY-4900", "crash:mypy": "MYPY-22360"},
    "D11": {"crash:ty": "TY-4900", "crash:mypy": "MYPY-22360"},
    "D9": {"crash:mypy": "MYPY-22360"},
    "B1": {"crash:mypy": "MYPY-22360"}, "B4": {"crash:mypy": "MYPY-22360"},
    "B3": {}, "B5": {}, "B6": {}, "D4": {}, "D8": {},
    "mypy_A_typealias_segfault": {"crash:mypy": "MYPY-22343"},
    "mypy_E_typevar_default_self": {"crash:mypy": "MYPY-22344"},
    "mypy_25": {"crash:mypy": "MYPY-22344"},
    "A2": {"crash:mypy": "MYPY-22361"}, "A4": {"crash:mypy": "MYPY-22361"}, "A5": {"crash:mypy": "MYPY-22361"},
    "A6": {"crash:mypy": "MYPY-22361"},
    "A1": {"crash:mypy": "MYPY-22361", "crash:ty": None},  # the ty overflow on A1 is an unfiled lead: must stay live
    "A3": {}, "A8": {}, "A10": {},
    "A7": {"crash:mypy": None},  # mypy crash of unconfirmed relation to #22361: stays live
    "A9": {"crash:pyright": None},  # unrelated pyright crash: stays live
    "ty_TA_depth24": {"crash:ty": "TY-4883"},  # ~150 s on ty 0.0.84: exceeds the 120 s runner timeout
    "ty_TA_nested_tuple_compare": {},  # depth 20 finishes in ~10 s: no crash, nothing to close
    "mypy_B_typealias_hang": {"crash:mypy": None},  # a different hang (mypy:timeout): stays live
    "pyright_11960_growing_alias": {"crash:pyright": "PYRIGHT-11960"},
    # discrepancy entries / priors (finding ids as the pipeline numbers them)
    "bug-01-narrowing-mypy-stale-index-narrowing": {"disc:D1": "MYPY-20969", "disc:D2": "MYPY-20969-REVEAL"},
    "bug-02-enums-ty-flag-or-literal-union": {"disc:D1": "TY-876"},
    "bug-02-ty-flag-or-assert-type": {"disc:D1": "TY-876-ASSERT"},
    "bug-03-generics-mypy-callable-attr-contravariant": {"disc:D1": "MYPY-22339", "disc:D2": None},
    "bug-04-dataclasses-mypy-initvar-default-class-attr": {"disc:D1": None, "disc:D2": None},  # priors only cap CONFIRMED/CANDIDATE; the gate already holds these at REVIEW
    "bug-05-typeddict-ty-generic-typeddict-typevar-unknown": {"disc:D1": "TY-4884", "disc:D2": "TY-4884",
                                                              "disc:D3": "TY-4884-REVEAL"},
    "bug-05-ty-generic-typeddict-crash-witness": {"disc:D1": "TY-4884", "disc:D2": None},
    "bug-06-enums-mypy-flag-is-narrowing-else-unreachable": {"disc:D1": "MYPY-21937"},
    "probe-bug01-index-variants": {"disc:D1": "MYPY-20969-REVEAL", "disc:D2": "MYPY-20969-REVEAL",
                                   "disc:D3": "MYPY-20969-REVEAL", "disc:D4": None},
    "probe-bug02-flag-operators": {"disc:D1": "TY-876", "disc:D2": "TY-876", "disc:D3": "TY-876", "disc:D4": "TY-876",
                                   "disc:D5": None, "disc:D6": None},
    "probe-bug03-variance-variants": {"disc:D1": "MYPY-22339", "disc:D2": "MYPY-22339"},
    "probe-bug05-typeddict-variants": {"disc:D1": "TY-4884-ASSERT", "disc:D2": "TY-4884-ASSERT"},
    "probe-bug06-flag-param-and-local": {"disc:D1": "MYPY-21937", "disc:D2": None, "disc:D3": "TY-876"},
    "probe-bug02-bug05-runtime-and-assignability": {},
    "pyright_init_attr": {"crash:pyright": "PYRIGHT-11961"},
    "pyright_new_attr": {"crash:pyright": "PYRIGHT-11961"},
    "pyright_call_metaclass": {"crash:pyright": "PYRIGHT-11961"},
}


def run_one(name: str) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix=f"updk3_{name}_"))
    seeds, out = tmp / "seeds", tmp / "out"
    seeds.mkdir()
    shutil.copy(DATA / f"{name}.py", seeds / f"{name}.py")
    env = dict(os.environ, TYPEDIFF_LLM="null")
    try:
        subprocess.run([str(TYPEDIFF), "--out", str(out), "--python-version", "3.13", "seeds", str(seeds)],
                       env=env, cwd=tmp, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"name": name, "error": "timeout", "rows": []}
    rows = []
    for p in sorted(out.glob("*.json")):
        d = json.loads(p.read_text())
        if "findings" not in d:
            continue
        crashes = {f"C{i}": c for i, c in enumerate(d.get("crashes", []), 1)}
        for f in d["findings"]:
            c = crashes.get(f["discrepancy_id"])
            key = f"crash:{c['tool']}" if c and f["discrepancy_id"].startswith("C") else f"disc:{f['discrepancy_id']}"
            note = next((n for n in f.get("review_notes", []) if "DUPLICATE of" in n), "")
            closed = _closing_id(note)
            if closed is None and f["decided_by"].startswith("kb:UPSTREAM-"):
                closed = f["decided_by"][len("kb:UPSTREAM-"):]
            priors = [n for n in f.get("review_notes", []) if n.startswith("PRIOR-STANCE:")]
            rows.append({"key": key, "signature": f.get("signature"), "tier": f["tier"], "dismissal": f.get("dismissal"),
                         "decided_by": f["decided_by"], "closed_by": closed, "priors": priors})
    shutil.rmtree(tmp, ignore_errors=True)
    return {"name": name, "rows": rows}


def _closing_id(note: str) -> str | None:
    import re

    m = re.search(r"\(((?:TY|MYPY|PYRIGHT)-\d+)\)", note)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    names = a.names or list(EXPECT)
    bad = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(run_one, names))
    for r in results:
        exp = EXPECT.get(r["name"], {})
        print(f"== {r['name']}" + (f"  ERROR {r['error']}" if r.get("error") else ""))
        seen = {}
        for row in r["rows"]:
            seen[row["key"]] = row
            print(f"   {row['key']:14} tier={row['tier']:10} dismissal={row['dismissal']} decided_by={row['decided_by']} "
                  f"closed_by={row['closed_by']} sig={row['signature']}")
        if not r["rows"]:
            print("   (no findings)")
        for key, want in exp.items():
            row = seen.get(key)
            if want is None:
                ok = row is not None and row["tier"] != "dismissed"
            elif want.startswith("PRIOR:"):  # capped at REVIEW by a prior stance, not dismissed
                ok = row is not None and row["tier"] == "review" and any(want[6:] in n for n in row["priors"])
            else:
                ok = row is not None and row["tier"] == "dismissed" and row["closed_by"] == want
            if not ok:
                bad += 1
                print(f"   !! EXPECTATION FAILED {key}: want {'live' if want is None else want}")
        for key, row in seen.items():
            if key.startswith("crash:") and key not in exp and row["tier"] == "dismissed":
                bad += 1
                print(f"   !! {key} dismissed but nothing was expected to close it")
        if not exp:
            for row in r["rows"]:
                if row["tier"] == "dismissed" and row["closed_by"]:
                    bad += 1
                    print(f"   !! control closed by {row['closed_by']}")
    print(f"\nviolations: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
