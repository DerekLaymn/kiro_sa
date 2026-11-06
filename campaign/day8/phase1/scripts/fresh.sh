cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=campaign/day8/phase1
rm -rf /tmp/d8/fresh /tmp/d8/fresh_out
mkdir -p /tmp/d8/fresh
cp runs/hits/d4v_eq_no_hash_hashable.py runs/hits/d4p_inheritance_hash_none_from_eq.py runs/hits/d3p_inheritance_mro_hash_none_from_eq.py /tmp/d8/fresh/
cp campaign/day6/partB/evidence/hash_h1.py /tmp/d8/fresh/h1.py
cp campaign/day7/partD/evidence/repro/h1b.py /tmp/d8/fresh/h1b.py
cp campaign/day7/partD/evidence/repro/c3.py /tmp/d8/fresh/c3_readonly_after_descriptor_store.py
cp campaign/day7/partD/evidence/repro/c3r.py /tmp/d8/fresh/c3r_descriptor_vs_method.py
cp campaign/day7/partD/evidence/repro/p1.py /tmp/d8/fresh/p1_gauge_level.py
cp runs/day7/gen/descriptors_properties/d4p_descriptors_readonly_prop_never__mut1_328a328e.py /tmp/d8/fresh/
cp runs/day6/gen/generics_variance/d3p_generics_callable_attr_contravariant__mut0_0bac40f6.py /tmp/d8/fresh/
cp runs/hits/d4v_recursive_alias_dots.py /tmp/d8/fresh/
cp runs/hits/d3p_paramspec_self_annotated_dunder_call.py /tmp/d8/fresh/paramspec_parent_E8.py
ls /tmp/d8/fresh
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py /tmp/d8/fresh_out /tmp/d8/fresh --jobs 4 --pyright-only --progress /tmp/d8/fresh_progress.log
echo rc=$?
.venv/bin/python - <<'EOF'
import json, glob
for f in sorted(glob.glob("/tmp/d8/fresh_out/seed-*.json")):
    r = json.load(open(f))
    org = next((n for n in r["notes"] if n.startswith("origin=")), "")
    ds = {d["id"]: d for d in r["discrepancies"]}
    print("##", org[-70:], "crashes:", [c["signature"] for c in r.get("crashes", [])])
    for fi in r["findings"]:
        d = ds.get(fi["discrepancy_id"])
        kind = d["kind"] if d else "crash"
        ev = [f'{e["type"]}/{e["strength"]}/{e["supports"]}' for e in fi["evidence"] if e["type"] == "RUNTIME"]
        print("   ", fi["discrepancy_id"], kind, (d["statement"][:48] if d else ""), "->", fi["tier"], fi["decided_by"], d["reveal_relation"] if d else "", ev)
EOF
