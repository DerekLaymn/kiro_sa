"""Command-line interface.

  typediff judge  SRC --mypy-out F --ty-out F --runtime F [--mypy-err F --ty-err F --pyright-json F] [--experiments]
  typediff run    SRC [SRC ...]                       run mypy+ty+pyright+CPython yourself, then judge
  typediff loop   --iterations N [--seeds DIR]        generate -> run -> judge -> dataset -> strategy
  typediff fetch-docs [--refresh-rule-map]            build the local spec/doc corpus used for citations
  typediff kb-selftest                                re-validate every KB entry against the installed tools
  typediff report OUT_DIR/CASE.json --finding D1      draft an upstream issue for a finding
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .corpus import DEFAULT_DIR, Corpus, fetch_docs
from .dataset import Dataset
from .generator import blocking, generate, preflight
from .kb import ENTRIES
from .llm import NullLLM, CachedLLM, from_env
from .models import Tier, to_jsonable
from .pipeline import Pipeline, PipelineConfig
from .report import draft_issue, render_summary
from .runners import Runners, ToolConfig
from .strategy import AREAS, Strategy


def _read(p: str | None) -> str:
    return Path(p).read_text(encoding="utf-8") if p else ""


def _pipeline(args, llm=None) -> Pipeline:
    tools = ToolConfig(python_version=args.python_version)
    if getattr(args, "typeshed", None):
        tools.shared_typeshed = args.typeshed
    cfg = PipelineConfig(tools=tools, use_pyright=not args.no_pyright, reduce=not args.no_reduce,
                         audit_rate=args.audit_rate)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    return Pipeline(cfg, llm or from_env(args.llm), Corpus(Path(args.docs)), Dataset(out / "dataset.jsonl"))


def _save(report, out: Path, dataset: Dataset | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{report.case_id}.json").write_text(json.dumps(to_jsonable(report), indent=1))
    (out / f"{report.case_id}.md").write_text(render_summary(report))
    if dataset:
        dataset.add_case(report)


def cmd_judge(args) -> int:
    p = _pipeline(args)
    flags = json.loads(args.flags) if args.flags else {}
    report = p.judge_logs(
        _read(args.src), _read(args.mypy_out), _read(args.ty_out), _read(args.runtime), mypy_stderr=_read(args.mypy_err),
        ty_stderr=_read(args.ty_err), mypy_exit=args.mypy_exit, ty_exit=args.ty_exit,
        pyright_json=_read(args.pyright_json) or None, flags=flags, target_python=args.python_version,
        allow_experiments=args.experiments,
    )
    _save(report, Path(args.out), p.dataset)
    print(render_summary(report))
    return 0


def cmd_run(args) -> int:
    p = _pipeline(args)
    for src in args.src:
        report = p.run_source(_read(src), case_id=Path(src).stem if args.keep_names else None)
        _save(report, Path(args.out), p.dataset)
        print(render_summary(report))
    return 0


def _seed_header(source: str, key: str) -> str:
    m = re.search(rf"^#\s*{key}:\s*(.+)$", source, re.M)
    return m.group(1).strip() if m else ""


def _seed_area(path: Path, source: str, default: str) -> str:
    for cand in (path.parent.name, _seed_header(source, "area").split()[0] if _seed_header(source, "area") else ""):
        if cand in AREAS:
            return cand
    return default


def cmd_seeds(args) -> int:
    """Seed mode: run every seed (recursively); with --mutate K and an LLM, also run K LLM variants of each
    seed (and of each variant, up to --depth) that produced a non-dismissed finding."""
    llm = from_env(args.llm)
    p = _pipeline(args, llm)
    out = Path(args.out)
    strategy = Strategy(out / "strategy.json", llm)
    files = sorted(Path(args.seeds).rglob("*.py"))
    if args.area:
        files = [f for f in files if _seed_area(f, f.read_text(), "") == args.area]
    queue = [(f.read_text(), _seed_area(f, f.read_text(), args.area or "gradual_any"), f"seed {f}", 0) for f in files]
    can_mutate = args.mutate > 0 and not isinstance(llm.inner, NullLLM)
    if args.mutate > 0 and not can_mutate:
        print("note: --mutate needs an LLM (TYPEDIFF_LLM=...); running seeds only", file=sys.stderr)
    i = 0
    while queue and i < args.iterations:
        if args.max_llm_calls and llm.calls >= args.max_llm_calls:
            print(f"stopping: LLM call budget reached ({llm.calls})")
            break
        source, area, origin, depth = queue.pop(0)
        problems = preflight(source, args.python_version)
        if blocking(problems):
            print(f"[{i}] {origin}: preflight rejected: {problems}")
            i += 1
            continue
        report = p.run_source(source)
        report.notes += [f"area={area}", f"origin={origin}", f"depth={depth}"] + problems
        before = len(p.dataset._sigs)
        p.dataset.add_case(report)
        new_sigs = len(p.dataset._sigs) - before
        strategy.record(area, report, new_sigs)
        advice = strategy.rule_decision(area, report)
        report.strategy = advice
        strategy.save()
        _save(report, out, None)
        live = [f for f in report.findings if f.tier != Tier.DISMISSED]
        print(f"[{i}] {report.case_id} {area} d={depth} {origin}: "
              f"{len(report.discrepancies)} disc, live={[(f.discrepancy_id, f.tier.value) for f in live]}")
        if can_mutate and live and depth < args.depth:
            brief = (_seed_header(source, "hypothesis") or AREAS[area]) + \
                " Keep the construct that caused the disagreement; vary everything around it."
            for k in range(args.mutate):
                variant, meta = generate(llm, area, brief, advice.mutations, source, advice.avoid_patterns,
                                         args.python_version)
                if variant:
                    queue.append((variant, area, f"{origin} > mut{k}", depth + 1))
        i += 1
    print(f"done: {i} programs, {llm.calls} LLM calls, dataset {p.dataset.path}")
    return 0


def cmd_generate(args) -> int:
    """Generation only: write LLM programs to a directory (no checking/judging). Lets a cheap/free model
    generate while judging happens later with `typediff seeds DIR` (no LLM, or a stronger one)."""
    llm = from_env(args.llm)
    if isinstance(llm.inner, NullLLM):
        print("generate needs an LLM (TYPEDIFF_LLM=...)", file=sys.stderr)
        return 2
    out = Path(args.out_dir)
    parents: list[tuple[str, str, Path | None]] = []
    if args.from_seeds:
        for f in sorted(Path(args.from_seeds).rglob("*.py")):
            src = f.read_text()
            parents.append((src, _seed_area(f, src, args.area or "gradual_any"), f))
    else:
        parents = [("", args.area or a, None) for a in ([args.area] if args.area else list(AREAS))]
    written = 0
    for previous, area, origin in parents:
        brief = (_seed_header(previous, "hypothesis") if previous else "") or AREAS[area]
        mutations = [{"operator": op} for op in (args.ops.split(",") if args.ops else [])]
        for k in range(args.n):
            if args.max_llm_calls and llm.calls >= args.max_llm_calls:
                print(f"stopping: LLM call budget reached ({llm.calls})")
                return 0
            src, meta = generate(llm, area, brief, mutations, previous, [], args.python_version)
            if not src:
                print(f"  failed ({area}): {meta.get('preflight') or meta.get('error')}")
                continue
            name = (origin.stem + f"__mut{k}") if origin else f"gen{k}"
            dest = out / area / f"{name}_{abs(hash(src)) % 10**6:06d}.py"
            dest.parent.mkdir(parents=True, exist_ok=True)
            header = f"# area: {area}\n# hypothesis: {meta.get('hypothesis', '').strip()}\n# origin: {origin or 'llm'}\n"
            dest.write_text(header + src)
            written += 1
            print(f"  wrote {dest}")
    print(f"done: {written} programs, {llm.calls} uncached LLM calls")
    return 0


def cmd_triage(args) -> int:
    """Group the review queue of a run directory into patterns (kind + silent/reporting tool + codes +
    message template) so you triage one pattern at a time instead of one finding at a time."""
    from collections import defaultdict

    from .dataset import message_template

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for f in sorted(Path(args.run_dir).glob("*.json")):
        if f.name in ("strategy.json",) or f.name.startswith("calibration"):
            continue
        try:
            r = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if "findings" not in r:
            continue
        ds = {d["id"]: d for d in r["discrepancies"]}
        origin = next((n.split("=", 1)[1] for n in r.get("notes", []) if n.startswith("origin=")), r["case_id"])
        for x in r["findings"]:
            if x["tier"] == "dismissed" and not args.all:
                continue
            d = ds.get(x["discrepancy_id"])
            if d is None:
                key = ("crash", x.get("signature") or x["reasoning"][:60])
            else:
                diags = d["mypy"] or d["ty"]
                if d["kind"].startswith("reveal"):
                    key = (d["kind"], d.get("reveal_relation"))
                else:
                    key = (d["kind"], tuple(sorted({y.get("code") or "" for y in diags})),
                           message_template(diags[0]["message"]) if diags else "")
            bug_ev = any(e["supports"] == "bug" and e["verified"] and e["strength"] == "strong" for e in x["evidence"])
            def show(lst):
                return "; ".join(f"reveal {y['revealed_type']}" if y.get("revealed_type") is not None
                                 else f"[{y.get('code')}] {y['message']}" for y in lst) or "(nothing)"
            groups[key].append({"origin": origin, "case": r["case_id"], "id": x["discrepancy_id"], "tier": x["tier"],
                                "line": d["anchor"] if d else None, "stmt": d["statement"][:70] if d else "",
                                "bug_evidence": bug_ev, "mypy": show(d["mypy"]) if d else "", "ty": show(d["ty"]) if d else "",
                                "kb": d.get("kb_hits", []) if d else [], "decided_by": x["decided_by"],
                                "report": str(f.with_suffix(".md")),
                                "evidence": [f"[{e['type']}/{e['strength']}, supports {e['supports']}] {e['summary']}"
                                             for e in x["evidence"] if e["verified"] and e["supports"] != "neutral"
                                             or e["strength"] == "strong"]})
    ranked = sorted(groups.items(), key=lambda kv: (-sum(i["bug_evidence"] for i in kv[1]), -len(kv[1])))
    for key, items in ranked[: args.top]:
        nb = sum(i["bug_evidence"] for i in items)
        print(f"\n## {len(items):>4} findings ({nb} with strong bug evidence)  {' | '.join(map(str, key))}")
        for i in sorted(items, key=lambda i: not i["bug_evidence"])[: args.examples]:
            print(f"     {'*' if i['bug_evidence'] else ' '} {i['origin'][-60:]}  {i['id']} L{i['line']}: {i['stmt']}")
            if args.details:
                print(f"         mypy: {i['mypy'][:200]}")
                print(f"         ty:   {i['ty'][:200]}")
                if i["kb"]:
                    print(f"         KB hints: {', '.join(i['kb'])}   decided by: {i['decided_by']}")
                for e in i["evidence"][:4]:
                    print(f"         {e[:220]}")
                print(f"         full report: {i['report']}")
    print(f"\n{sum(len(v) for v in groups.values())} findings in {len(groups)} patterns "
          f"(* = strong verified bug evidence; triage those patterns first)")
    return 0


def cmd_loop(args) -> int:
    llm = from_env(args.llm)
    p = _pipeline(args, llm)
    out = Path(args.out)
    strategy = Strategy(out / "strategy.json", llm)
    if args.seeds:
        print("use `typediff seeds DIR` for seed mode", file=sys.stderr)
        return 2
    if isinstance(llm.inner, NullLLM):
        print("loop needs an LLM (TYPEDIFF_LLM=...); for seeds without an LLM use `typediff seeds DIR`", file=sys.stderr)
        return 2
    area = args.area or strategy.choose_area()
    brief, mutations, previous, avoid = AREAS[area], [], "", []
    for i in range(args.iterations):
        if args.max_llm_calls and llm.calls >= args.max_llm_calls:
            print(f"stopping: LLM call budget reached ({llm.calls})")
            break
        source, meta = generate(llm, area, brief, mutations, previous, avoid, args.python_version)
        problems = meta.get("preflight", [])
        if source is None:
            print(f"[{i}] generator failed: {meta}")
            continue
        if blocking(problems):
            print(f"[{i}] preflight rejected program: {problems}")
            continue
        report = p.run_source(source)
        report.notes += [f"area={area}", f"hypothesis={meta.get('hypothesis', '')}"] + problems
        before = len(p.dataset._sigs)
        p.dataset.add_case(report)
        new_sigs = len(p.dataset._sigs) - before
        strategy.record(area, report, new_sigs)
        advice = strategy.advise(area, report, brief)
        report.strategy = advice
        strategy.save()
        _save(report, out, None)
        tiers = [f.tier.value for f in report.findings]
        print(f"[{i}] {report.case_id} area={area} findings={tiers} -> {advice.decision} {advice.next_area or ''}")
        if advice.decision in ("CONTINUE", "MUTATE"):
            previous, mutations = source, advice.mutations
            brief = advice.next_program_brief or brief
        elif advice.decision == "REPAIR_GENERATOR":
            avoid = sorted(set(avoid) | set(advice.avoid_patterns) | {"programs that fail the preflight lint"})
            previous, mutations = "", []
        else:  # PIVOT / ABANDON
            area = advice.next_area or strategy.choose_area()
            brief, previous, mutations = advice.next_program_brief or AREAS[area], "", []
        avoid = sorted(set(avoid) | set(advice.avoid_patterns))
    return 0


def cmd_fetch(args) -> int:
    for line in fetch_docs(Path(args.docs), Runners(ToolConfig()).cfg.ty_cmd, args.refresh_rule_map):
        print(line)
    print(f"corpus: {len(Corpus(Path(args.docs)).chunks)} chunks in {args.docs}")
    return 0


def cmd_kb_selftest(args) -> int:
    p = _pipeline(args, CachedLLM(NullLLM()))
    p.cfg.reduce = False
    p.cfg.audit_rate = 0.0
    failures = 0
    for e in ENTRIES:
        if not e.example:
            continue
        r = p.run_source(e.example, case_id=f"kb-{e.id}")
        hit = any(f.decided_by == f"kb:{e.id}" for f in r.findings)
        failures += not hit
        print(f"{'PASS' if hit else 'FAIL'}  KB:{e.id}  findings={[(f.discrepancy_id, f.decided_by) for f in r.findings]}")
    return 1 if failures else 0


def cmd_calibrate(args) -> int:
    from .calibration import fetch_positives, negatives, run_calibration

    manifest = Path(args.manifest)
    if args.fetch or not manifest.exists():
        cases = fetch_positives(manifest, tuple(args.tools.split(",")))
        print(f"fetched {len(cases)} positive cases -> {manifest}")
    cases = json.loads(manifest.read_text())
    cases = [c for c in cases if c["faulty_tool"] in args.tools.split(",")]
    total = len(cases)
    cases = cases[args.offset:]
    if args.limit:
        cases = cases[: args.limit]
    if args.offset + len(cases) >= total:  # last chunk also runs the negatives
        cases += negatives(Path(args.negatives))
    p = _pipeline(args)
    p.cfg.tools.timeout_s = args.timeout
    p.cfg.reduce = False
    p.cfg.audit_rate = 0.0
    p.dataset = None  # calibration must not pollute (or dedup against) the campaign dataset
    out = Path(args.out) / "calibration"
    if args.offset == 0:
        (out / "calibration_rows.jsonl").unlink(missing_ok=True)
    run_calibration(p, cases, out)
    from .calibration import summarize

    rows = [json.loads(x) for x in (out / "calibration_rows.jsonl").read_text().splitlines() if x.strip()]
    summary = summarize(rows)  # over all chunks run so far
    (out / "calibration_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0


def cmd_report(args) -> int:
    data = json.loads(Path(args.case).read_text())
    from .models import CaseReport

    # rebuilding the full object graph is not needed: re-judge from the stored source for an exact report
    p = _pipeline(args)
    report = p.run_source(data["source"], case_id=data["case_id"])
    f = next((x for x in report.findings if x.discrepancy_id == args.finding), None)
    if f is None:
        print(f"finding {args.finding} not found (re-run produced {[x.discrepancy_id for x in report.findings]})")
        return 1
    if f.tier not in (Tier.CONFIRMED, Tier.CANDIDATE):
        print(f"warning: finding tier is {f.tier.value}; drafting anyway", file=sys.stderr)
    print(draft_issue(report, f, p.llm))
    return 0 if isinstance(report, CaseReport) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="typediff", description="mypy-vs-ty differential bug adjudicator")
    ap.add_argument("--out", default="typediff_out")
    ap.add_argument("--docs", default=str(DEFAULT_DIR))
    ap.add_argument("--llm", default=None, help="override TYPEDIFF_LLM (anthropic:<model> | openai:<model>[@url] | file:<dir> | null)")
    ap.add_argument("--python-version", default="3.12")
    ap.add_argument("--no-pyright", action="store_true")
    ap.add_argument("--no-reduce", action="store_true")
    ap.add_argument("--audit-rate", type=float, default=0.05)
    ap.add_argument("--typeshed", default=None, help="shared typeshed checkout for both checkers (removes stub skew)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("judge", help="judge pre-computed tool outputs (the 4-input contract)")
    j.add_argument("src")
    j.add_argument("--mypy-out", required=True)
    j.add_argument("--mypy-err")
    j.add_argument("--mypy-exit", type=int)
    j.add_argument("--ty-out", required=True)
    j.add_argument("--ty-err")
    j.add_argument("--ty-exit", type=int)
    j.add_argument("--runtime", required=True, help="runtime_harness JSON, a raw traceback, or 'Success'")
    j.add_argument("--pyright-json")
    j.add_argument("--flags", help='JSON: {"mypy": [...], "ty": [...]} used to produce the logs')
    j.add_argument("--experiments", action="store_true", help="allow re-running installed tools for experiments")
    j.set_defaults(fn=cmd_judge)

    r = sub.add_parser("run", help="run all tools on SRC files and judge")
    r.add_argument("src", nargs="+")
    r.add_argument("--keep-names", action="store_true", help="use file stems as case ids")
    r.set_defaults(fn=cmd_run)

    lp = sub.add_parser("loop", help="generation/judging campaign")
    lp.add_argument("--iterations", type=int, default=20)
    lp.add_argument("--area", choices=sorted(AREAS))
    lp.add_argument("--seeds", help=argparse.SUPPRESS)
    lp.add_argument("--max-llm-calls", type=int, default=0, help="stop after this many (uncached) LLM calls")
    lp.set_defaults(fn=cmd_loop)

    sd = sub.add_parser("seeds", help="run a seed corpus (recursively), optionally with LLM mutation of hits")
    sd.add_argument("seeds", help="directory; sub-folders named after feature areas set the area")
    sd.add_argument("--iterations", type=int, default=100000, help="max programs to run")
    sd.add_argument("--area", choices=sorted(AREAS), help="only seeds of this area")
    sd.add_argument("--mutate", type=int, default=0, help="LLM variants per seed that produced a live finding")
    sd.add_argument("--depth", type=int, default=1, help="max mutation generations")
    sd.add_argument("--max-llm-calls", type=int, default=0, help="stop after this many (uncached) LLM calls")
    sd.set_defaults(fn=cmd_seeds)

    tr = sub.add_parser("triage", help="group a run's review queue into patterns")
    tr.add_argument("run_dir")
    tr.add_argument("--top", type=int, default=30)
    tr.add_argument("--examples", type=int, default=3)
    tr.add_argument("--all", action="store_true", help="include dismissed findings")
    tr.add_argument("--details", action="store_true", help="show both tools' messages, evidence and the report path")
    tr.set_defaults(fn=cmd_triage)

    gn = sub.add_parser("generate", help="LLM generation only: write programs to a directory (judge later)")
    gn.add_argument("--out-dir", required=True)
    gn.add_argument("--area", choices=sorted(AREAS), help="default: every area (or the seed's own area)")
    gn.add_argument("--from-seeds", help="mutate every seed in this directory instead of writing from scratch")
    gn.add_argument("--n", type=int, default=3, help="programs per area / per seed")
    gn.add_argument("--ops", default="", help="comma-separated mutation operators, e.g. feature_crossover,runtime_witness")
    gn.add_argument("--max-llm-calls", type=int, default=0)
    gn.set_defaults(fn=cmd_generate)

    fd = sub.add_parser("fetch-docs", help="download spec/doc corpus for citation verification")
    fd.add_argument("--refresh-rule-map", action="store_true")
    fd.set_defaults(fn=cmd_fetch)

    ks = sub.add_parser("kb-selftest", help="check KB entries still fire on the installed tool versions")
    ks.set_defaults(fn=cmd_kb_selftest)

    cb = sub.add_parser("calibrate", help="measure false dismissals on real bug reports + documented divergences")
    cb.add_argument("--manifest", default="calibration/positives.json")
    cb.add_argument("--negatives", default="calibration/negatives")
    cb.add_argument("--fetch", action="store_true", help="(re)download open bug reports from GitHub")
    cb.add_argument("--tools", default="ty,mypy")
    cb.add_argument("--limit", type=int, default=0)
    cb.add_argument("--offset", type=int, default=0, help="resume / run in chunks (rows are appended)")
    cb.add_argument("--timeout", type=int, default=30, help="per-checker timeout (hang reports)")
    cb.set_defaults(fn=cmd_calibrate)

    rp = sub.add_parser("report", help="draft an upstream issue")
    rp.add_argument("case")
    rp.add_argument("--finding", required=True)
    rp.set_defaults(fn=cmd_report)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
