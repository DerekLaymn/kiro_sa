"""Campaign steering: per-feature-area statistics, UCB1 bandit, hard rules, optional LLM strategist.

Hard rules (PIVOT / ABANDON / REPAIR_GENERATOR) cannot be overridden by the LLM; the LLM refines
CONTINUE/MUTATE decisions and writes the concrete next-program brief and mutation instructions.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from . import prompts
from .llm import complete_json
from .models import CaseReport, Dismissal, StrategyAdvice, Tier, Verdict

AREAS: dict[str, str] = {
    "generics_variance": "TypeVar bounds/constraints, PEP 695 variance inference, invariance of mutable containers",
    "paramspec_concatenate": "ParamSpec, Concatenate, decorators preserving signatures, *args/**kwargs forwarding",
    "typevartuple_unpack": "TypeVarTuple, Unpack, variadic tuples, star-unpacking in tuple types",
    "protocols": "structural subtyping, protocol members with defaults, properties in protocols, generic protocols",
    "typeddict": "Required/NotRequired/ReadOnly, closed/extra_items, Unpack[TypedDict] kwargs, TypedDict ops",
    "overloads": "overload resolution with unions/Any/literals, overload consistency, overloads with generics",
    "narrowing_builtin": "isinstance/issubclass/is/==/in/len/callable/hasattr narrowing, walrus, early returns",
    "narrowing_user": "TypeIs vs TypeGuard, negative branches, generic TypeIs, narrowing of attributes/subscripts",
    "match_statement": "class/value/sequence/mapping patterns, exhaustiveness with assert_never, guards",
    "dataclasses": "field ordering, kw_only, InitVar, __post_init__, frozen inheritance, dataclass_transform",
    "enums_literals": "Enum members/values, auto(), Literal unions, enum narrowing and exhaustiveness",
    "self_classmethods": "Self in methods/classmethods/properties, fluent interfaces, alternative constructors",
    "descriptors_properties": "__get__/__set__ descriptors, property setters, cached_property, class vs instance access",
    "constructors_metaclasses": "__new__/__init__ interplay, metaclass __call__, type[T] instantiation",
    "callables": "Callable assignability, callback protocols, positional-only/keyword-only, default args, lambdas",
    "recursive_aliases": "recursive type aliases (PEP 695 type stmt), self-referential generics (crash hunting)",
    "final_classvar": "Final reassignment, ClassVar access, Final in dataclasses/protocols, @final classes",
    "abstract_classes": "abstract methods, instantiation, abstract properties, ABC registration",
    "async_generators": "async def/await, AsyncIterator, Generator send/return types, yield from",
    "inheritance_mro": "multiple inheritance, super(), method override compatibility (LSP), diamond MRO",
    "tuples_unpacking": "fixed vs variadic tuples, indexing/slicing, unpacking assignments, NamedTuple",
    "gradual_any": "Any propagation, object vs Any, gradual guarantee, cast/assert_type interplay",
}

AVOID_FOR_KB = {
    "TY-REDECLARATION": "re-annotating a name that already has a declared type",
    "TY-CALLABLE-DUNDER": "accessing __name__/__qualname__ on Callable-typed values",
    "TY-STRICT-EQUALITY": "narrowing str/int to Literal via == or `in` (only if not the hypothesis)",
    "TY-GRADUAL-GENERIC-NARROWING": "isinstance(x, list) on object-typed values then using the element type",
    "TY-UNKNOWN-UNION": "reveal_type on unannotated class attributes (annotate them)",
    "LITERAL-WIDENING": "reveal_type on unannotated literal-initialised variables (annotate them)",
    "JOIN-VS-UNION": "unannotated heterogeneous collection literals / ternaries (annotate them)",
    "PRECISION-RUNTIME-CONSISTENT": "reveal_type right after an assignment to a wider declared type",
    "MYPY-SKIPS-UNREACHABLE": "reveal_type in statically unreachable branches",
    "ENV-IMPORT": "third-party imports",
    "INFERENCE-DOWNSTREAM": "operations on unannotated variables whose inferred type is the only difference",
    "TY-CHECK-NOT-IMPLEMENTED": "mypy-only checks ty does not implement (see ty rule-mapping table)",
}
CRASH_OPS = ["recursion_deepening", "invalid_type_form", "feature_crossover"]
DEPTH_OPS = ["feature_crossover", "generic_nesting", "narrowing_construct_swap", "runtime_witness"]


class Strategy:
    def __init__(self, state_path: str | Path, llm=None, exploration: float = 1.2):
        self.path = Path(state_path)
        self.llm = llm
        self.c = exploration
        self.stats: dict[str, dict] = json.loads(self.path.read_text()) if self.path.exists() else {}
        for a in AREAS:
            self.stats.setdefault(a, {"cases": 0, "reward": 0.0, "confirmed": 0, "candidates": 0, "review": 0,
                                      "crashes": 0, "invalid": 0, "discrepancies": 0, "dismissals": {}, "kb_hits": {},
                                      "recent": [], "abandoned": False})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.stats, indent=1))

    # ------------------------------------------------------------------ bookkeeping
    def record(self, area: str, report: CaseReport, new_signatures: int) -> dict:
        st = self.stats.setdefault(area, {})
        tiers = Counter(f.tier.value for f in report.findings)
        crashes = sum(1 for f in report.findings if f.symptom and f.symptom.value == "CRASH")
        invalid = sum(1 for f in report.findings if f.dismissal == Dismissal.INVALID_TEST)
        dismissals = Counter(f.dismissal.value for f in report.findings if f.dismissal)
        kb = Counter(f.decided_by.removeprefix("kb:") for f in report.findings if f.decided_by.startswith("kb:"))
        reward = min(1.0, (10 * tiers.get("confirmed", 0) + 4 * tiers.get("candidate", 0) + 1 * tiers.get("review", 0)
                           + 6 * crashes) / 10 * (1.0 if new_signatures else 0.3))
        if invalid and invalid == len(report.findings):
            reward = 0.0
        st["cases"] += 1
        st["reward"] += reward
        st["confirmed"] += tiers.get("confirmed", 0)
        st["candidates"] += tiers.get("candidate", 0)
        st["review"] += tiers.get("review", 0)
        st["crashes"] += crashes
        st["invalid"] += 1 if invalid and invalid == len(report.findings) else 0
        st["discrepancies"] += len(report.discrepancies)
        for k, v in dismissals.items():
            st["dismissals"][k] = st["dismissals"].get(k, 0) + v
        for k, v in kb.items():
            st["kb_hits"][k] = st["kb_hits"].get(k, 0) + v
        summary = {"case": report.case_id, "reward": round(reward, 3), "tiers": dict(tiers), "kb": dict(kb),
                   "invalid": bool(invalid and invalid == len(report.findings)), "n_disc": len(report.discrepancies),
                   "new_sigs": new_signatures}
        st["recent"] = (st.get("recent", []) + [summary])[-12:]
        return summary

    def choose_area(self) -> str:
        total = sum(s["cases"] for s in self.stats.values()) + 1
        best, best_score = None, -1.0
        for a, s in self.stats.items():
            if s.get("abandoned"):
                continue
            if s["cases"] == 0:
                return a
            score = s["reward"] / s["cases"] + self.c * math.sqrt(math.log(total) / s["cases"])
            if score > best_score:
                best, best_score = a, score
        return best or next(iter(AREAS))

    # ------------------------------------------------------------------ decisions
    def rule_decision(self, area: str, report: CaseReport) -> StrategyAdvice:
        st = self.stats[area]
        recent = st.get("recent", [])
        tiers = Counter(f.tier for f in report.findings)
        avoid = sorted({AVOID_FOR_KB[k] for r in recent[-5:] for k in r.get("kb", {}) if k in AVOID_FOR_KB})
        if tiers.get(Tier.CONFIRMED) or tiers.get(Tier.CANDIDATE):
            return StrategyAdvice("CONTINUE", "bug candidate found: generate close variants to generalise it and pin the root "
                                  "cause (does it survive renaming, other spellings, other containers?)", area,
                                  mutations=[{"operator": "narrowing_construct_swap"}, {"operator": "annotation_spelling_swap"},
                                             {"operator": "runtime_witness"}], avoid_patterns=avoid)
        last4 = recent[-4:]
        if len(last4) >= 4 and sum(r["invalid"] for r in last4) >= 2:
            return StrategyAdvice("REPAIR_GENERATOR", ">=50% of the last programs were invalid tests; tighten generator "
                                  "constraints before spending more cycles", area, avoid_patterns=avoid)
        dis = st.get("dismissals", {})
        known = dis.get("KNOWN_LIMITATION", 0)
        if st["cases"] >= 6 and known >= 0.6 * max(1, sum(dis.values())) and not st["confirmed"]:
            st["abandoned"] = True
            return StrategyAdvice("ABANDON", "area dominated by documented unimplemented features (@Todo / 'None yet'); "
                                  "revisit after the next ty release", area, next_area=self.choose_area(), avoid_patterns=avoid)
        last5 = recent[-5:]
        if len(last5) >= 5 and not any(r["tiers"].get("confirmed") or r["tiers"].get("candidate") for r in last5):
            kb_ids = Counter(k for r in last5 for k in r.get("kb", {}))
            no_disc = sum(1 for r in last5 if r["n_disc"] == 0)
            if (kb_ids and len(kb_ids) <= 2) or no_disc >= 4:
                return StrategyAdvice("PIVOT", "saturated: recent cases only reproduce the same known divergences or "
                                      "agree completely", area, next_area=self._other_area(area), avoid_patterns=avoid)
        if len(last4) >= 4 and all(r["n_disc"] == 0 for r in last4):
            return StrategyAdvice("MUTATE", "checkers agree on everything lately: increase interaction depth", area,
                                  mutations=[{"operator": op} for op in DEPTH_OPS[:2]] + [{"operator": CRASH_OPS[0]}],
                                  avoid_patterns=avoid)
        return StrategyAdvice("MUTATE", "keep exploring the area with targeted mutations", area,
                              mutations=[{"operator": "feature_crossover"}, {"operator": "runtime_witness"}], avoid_patterns=avoid)

    def _other_area(self, area: str) -> str:
        saved = self.stats[area].get("abandoned", False)
        self.stats[area]["abandoned"] = True  # exclude temporarily
        nxt = self.choose_area()
        self.stats[area]["abandoned"] = saved
        return nxt

    def advise(self, area: str, report: CaseReport, brief: str = "") -> StrategyAdvice:
        advice = self.rule_decision(area, report)
        if self.llm is None or getattr(self.llm, "name", "null") == "null":
            if not advice.next_program_brief:
                advice.next_program_brief = f"Area '{advice.next_area or area}': {AREAS.get(advice.next_area or area, '')}"
            return advice
        stats_block = "\n".join(
            f"- {a}: cases={s['cases']} mean_reward={(s['reward'] / s['cases']) if s['cases'] else 0:.2f} "
            f"confirmed={s['confirmed']} candidates={s['candidates']} crashes={s['crashes']} invalid={s['invalid']} "
            f"top_kb={sorted(s['kb_hits'].items(), key=lambda kv: -kv[1])[:3]}{' ABANDONED' if s.get('abandoned') else ''}"
            for a, s in self.stats.items() if s["cases"] or a == area)
        findings = "\n".join(
            f"- {f.discrepancy_id}: {f.tier.value} {f.verdict.value} {f.faulty_tool} "
            f"{(f.symptom or f.dismissal).value if (f.symptom or f.dismissal) else ''} by {f.decided_by}: {f.reasoning[:160]}"
            for f in report.findings) or "- (no discrepancies: both checkers agreed)"
        user = prompts.STRATEGIST_USER.format(
            area=area, stats_block=stats_block, rule_advice=f"{advice.decision}: {advice.rationale}", brief=brief or "(none)",
            findings_block=findings, areas="\n".join(f"- {a}: {d}" for a, d in AREAS.items()))
        obj = complete_json(self.llm, prompts.STRATEGIST_SYSTEM, user,
                            lambda o: [] if isinstance(o, dict) and o.get("decision") else ["need 'decision'"])
        if obj.get("_null") or obj.get("_invalid"):
            return advice
        hard = advice.decision in ("PIVOT", "ABANDON", "REPAIR_GENERATOR")
        decision = advice.decision if hard else (obj["decision"] if obj["decision"] in ("CONTINUE", "MUTATE", "PIVOT") else advice.decision)
        nxt = obj.get("next_area") if obj.get("next_area") in AREAS else advice.next_area
        if decision == "PIVOT" and not nxt:
            nxt = self._other_area(area)
        return StrategyAdvice(
            decision=decision, rationale=(advice.rationale if hard else str(obj.get("rationale", advice.rationale))),
            feature_area=area, next_area=nxt, mutations=obj.get("mutations") or advice.mutations,
            next_program_brief=str(obj.get("next_program_brief", "")), decided_by="rules" if hard else "rules+llm",
            avoid_patterns=sorted(set(advice.avoid_patterns) | {str(p) for p in obj.get("avoid_patterns", [])}),
        )


def bug_found(report: CaseReport) -> bool:
    return any(f.verdict == Verdict.BUG and f.tier in (Tier.CONFIRMED, Tier.CANDIDATE) for f in report.findings)
