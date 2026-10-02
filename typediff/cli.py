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


def cmd_loop(args) -> int:
    llm = from_env(args.llm)
    p = _pipeline(args, llm)
    out = Path(args.out)
    strategy = Strategy(out / "strategy.json", llm)
    seeds = sorted(Path(args.seeds).glob("*.py")) if args.seeds else []
    if not seeds and isinstance(llm.inner, NullLLM):
        print("loop needs an LLM (TYPEDIFF_LLM=...) or --seeds DIR", file=sys.stderr)
        return 2
    area = args.area or strategy.choose_area()
    brief, mutations, previous, avoid = AREAS[area], [], "", []
    for i in range(args.iterations):
        if seeds:
            if i >= len(seeds):
                break
            source, meta = seeds[i].read_text(), {"hypothesis": f"seed {seeds[i].name}"}
            problems = preflight(source, args.python_version)
        else:
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
    lp.add_argument("--seeds", help="directory of .py programs to use instead of the LLM generator")
    lp.set_defaults(fn=cmd_loop)

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
