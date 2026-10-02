"""Calibration: measure whether the pipeline ever DISMISSES a real bug (recall) and how much
documented-divergence noise it closes on its own (DESIGN.md §7).

Positives are open, maintainer-labelled bug reports from astral-sh/ty and python/mypy with a
stdlib-only repro (fetched from the GitHub REST API). Negatives are documented divergences
(``calibration/negatives/*.py`` plus every KB example).

Outcome per positive:
  kept       at least one finding is confirmed/candidate/review  -> the bug survives the pipeline
  dismissed  discrepancies exist but ALL were dismissed            -> a false dismissal to investigate
  invisible  no discrepancy and no crash: mypy and ty agree       -> differential testing cannot see it
  excluded   not applicable (ty_extensions-only, no longer reproduces as a crash/hang, ...)
"""

from __future__ import annotations

import ast
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from .models import Tier

_STD = set(getattr(sys, "stdlib_module_names", ())) | {"typing_extensions", "__future__"}
_BLOCK = re.compile(r"```(?:py|python|python3|pycon)?[ \t]*\r?\n(.*?)```", re.S)

QUERIES = {
    "ty": [("astral-sh/ty", "bug")],
    "mypy": [("python/mypy", "bug,false-positive"), ("python/mypy", "crash")],
}


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers={"accept": "application/vnd.github+json", "user-agent": "typediff"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed GitHub API URL
        return json.loads(resp.read().decode())


def extract_repro(body: str) -> str | None:
    for block in _BLOCK.findall(body or ""):
        code = block.replace("\r\n", "\n")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        if not tree.body or len(code.splitlines()) > 150:
            continue
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                mods.add(n.module.split(".")[0])
        if mods - _STD - {"ty_extensions"}:
            return None  # environment-dependent repro: not usable for calibration
        return code
    return None


def fetch_positives(dest: Path, tools: tuple[str, ...] = ("ty", "mypy"), max_pages: int = 2) -> list[dict]:
    cases: list[dict] = []
    for tool in tools:
        for repo, labels in QUERIES[tool]:
            for page in range(1, max_pages + 1):
                items = _get(f"https://api.github.com/repos/{repo}/issues?state=open&labels={labels}"
                             f"&per_page=100&page={page}")
                if not isinstance(items, list) or not items:
                    break
                for it in items:
                    if "pull_request" in it:
                        continue
                    lab = [x["name"] for x in it["labels"]]
                    if "server" in lab or "daemon" in it["title"].lower():
                        continue
                    code = extract_repro(it.get("body") or "")
                    if code is None:
                        continue
                    cases.append({"id": f"{tool}-{it['number']}", "url": it["html_url"], "title": it["title"],
                                  "labels": lab, "faulty_tool": tool, "kind": "positive", "source": code})
                time.sleep(1)
    uniq = {c["id"]: c for c in cases}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(list(uniq.values()), indent=1))
    return list(uniq.values())


def negatives(neg_dir: Path) -> list[dict]:
    from .kb import ENTRIES

    out = [{"id": f"kb-{e.id}", "kind": "negative", "source": e.example, "title": e.title, "faulty_tool": "none",
            "labels": [], "url": e.source} for e in ENTRIES if e.example]
    for p in sorted(neg_dir.glob("*.py")) if neg_dir.exists() else []:
        out.append({"id": f"neg-{p.stem}", "kind": "negative", "source": p.read_text(), "title": p.stem,
                    "faulty_tool": "none", "labels": [], "url": str(p)})
    return out


def classify(case: dict, report) -> str:
    if case["kind"] == "positive" and "ty_extensions" in case["source"]:
        return "excluded"
    findings = report.findings
    if not findings:
        return "invisible"
    kept = [f for f in findings if f.tier in (Tier.CONFIRMED, Tier.CANDIDATE, Tier.REVIEW)]
    return "kept" if kept else "dismissed"


def run_calibration(pipeline, cases: list[dict], out_dir: Path, log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, case in enumerate(cases, 1):
        t0 = time.monotonic()
        try:
            report = pipeline.run_source(case["source"], case_id=case["id"])
            outcome = classify(case, report)
            detail = [(f.discrepancy_id, f.tier.value, f.decided_by,
                       (f.symptom or f.dismissal).value if (f.symptom or f.dismissal) else None) for f in report.findings]
            crashes = [c.signature for c in report.crashes]
        except Exception as exc:  # noqa: BLE001 - one broken case must not stop the run
            outcome, detail, crashes = "error", [str(exc)[:200]], []
        row = {"id": case["id"], "kind": case["kind"], "url": case.get("url"), "labels": case.get("labels", []),
               "outcome": outcome, "findings": detail, "crashes": crashes, "seconds": round(time.monotonic() - t0, 1)}
        rows.append(row)
        log(f"[{i}/{len(cases)}] {case['id']:<12} {case['kind']:<8} {outcome:<9} {detail}")
        (out_dir / "calibration_rows.jsonl").open("a").write(json.dumps(row) + "\n")
    summary = summarize(rows)
    (out_dir / "calibration_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def summarize(rows: list[dict]) -> dict:
    pos = [r for r in rows if r["kind"] == "positive" and r["outcome"] != "excluded"]
    neg = [r for r in rows if r["kind"] == "negative"]
    vis = [r for r in pos if r["outcome"] in ("kept", "dismissed")]
    by_tool = {}
    for tool in ("ty", "mypy"):
        t = [r for r in pos if r["id"].startswith(tool)]
        by_tool[tool] = dict(Counter(r["outcome"] for r in t))
    neg_auto = [r for r in neg if r["outcome"] == "dismissed"]
    return {
        "positives": len(pos), "positive_outcomes": dict(Counter(r["outcome"] for r in pos)), "by_tool": by_tool,
        "recall_on_visible": round(sum(r["outcome"] == "kept" for r in vis) / len(vis), 3) if vis else None,
        "false_dismissals": [{"id": r["id"], "url": r["url"], "findings": r["findings"]}
                             for r in pos if r["outcome"] == "dismissed"],
        "dismissal_reasons_on_positives": dict(Counter(f[2] for r in pos for f in r["findings"]
                                                       if isinstance(f, (list, tuple)) and f[1] == "dismissed")),
        "negatives": len(neg), "negatives_closed_automatically": len(neg_auto),
        "negatives_left_for_review": [r["id"] for r in neg if r["outcome"] == "kept"],
    }
