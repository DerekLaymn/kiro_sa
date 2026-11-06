#!/usr/bin/env bash
# Day 10 phase 5 morning decisions (Plan §3 "Every morning: retire parents"). Reversible; runs/ is git-ignored:
#   mv runs/hits-dropped/<name>.py runs/hits/
# Promoted: none (campaign/day10/phase5/alone.out, similarity rows, and the run log).
# Retired (3), rediscovery-only parents (campaign/day10/phase5/parent_yield.out, parent_signatures.out, parent_rows.out,
# parent_own_rows.out: every live row of the mutants is a row of the parent itself or of a family already filed or tracked):
#   d3p_generics_callable_attr_contravariant: the Day-10 revisit test of day10-morning.md section 1. 3 programs, 0 live, 4 dismissed
#     (DUPLICATE 2, NOISE 2); also 0 live on Day 9. The parent alone has 1 live row (a runtime_miss).
#   d4v_ty_alias_loop_backedge: 3 programs, 7 live, all `only_mypy` "Unsupported operand types for + (None and int)", the very row of
#     the parent (kind, mypy code and message the same; 0 new signatures except the pyright side of the same row).
#   d3p_typevartuple_unpack_paramspec_default_after_tvt: 4 programs, 15 live, 0 dismissed, 2 strong; the rows are mypy's "Can only replace
#     ParamSpec ..." message (draft 5, mypy#22375), the reveals that follow it, the TypeVarTuple-default TypeError (python/typing#2211)
#     and the consequences of that invalid default (`Pair[int, str, bool, bool]`). Second day in a row of rediscovery only; its
#     sibling d6p_..._mypy_subscript was retired in phase 2.
# Kept although mutated: d5p_descriptors_decorated_get_pyright_rangeerror (the only pyright RangeError reference; its 6 live rows are
# pyright-only rows still listed as "to verify" in day10-run-log.md phase 4 item 5, not rediscoveries),
# s3r1_mypy_class_base_forward_ref (its one live row is a function display difference, not the parent's finding),
# d3p_callables_partial_too_many_positional (a new ty/pyright `missing-argument` row), d9p_context_managers_swallowed_name_possibly_unbound
# (5 rows of new signatures), s3r1_ty_type_equality_narrowing_any, d4v_ty_flag_or_else_never, d8p_dunder_dispatch_annotation_only_call.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
echo "before: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
mkdir -p runs/hits-dropped
for b in d3p_generics_callable_attr_contravariant d4v_ty_alias_loop_backedge d3p_typevartuple_unpack_paramspec_default_after_tvt; do
  if [ -e "runs/hits/$b.py" ] && [ ! -e "runs/hits-dropped/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "skipped $b"; fi
done
echo "after: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
.venv/bin/python campaign/day4m/check_hits.py 0.80 > campaign/day10/phase5/check_hits-after.out 2>&1
echo "check_hits rc=$?" >> campaign/day10/phase5/check_hits-after.out
tail -n 4 campaign/day10/phase5/check_hits-after.out
echo "tracked files under runs: $(git ls-files runs | wc -l)"
git ls-files runs
