cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
rm -rf /tmp/d8/wt /tmp/d8/base_in /tmp/d8/base_out
git worktree add --detach /tmp/d8/wt campaign/day7-p2 > /tmp/d8/wt.log 2>&1
mkdir -p /tmp/d8/base_in
cp /tmp/d8/fresh/d4v_recursive_alias_dots.py /tmp/d8/fresh/d3p_generics_callable_attr_contravariant__mut0_0bac40f6.py /tmp/d8/fresh/h1.py /tmp/d8/base_in/
cd /tmp/d8/wt
PYTHONPATH=/tmp/d8/wt TYPEDIFF_LLM=null /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python scripts/kbloop_run.py /tmp/d8/base_out /tmp/d8/base_in --jobs 3 --pyright-only --progress /tmp/d8/base_progress.log
echo rc=$?
PYTHONPATH=/tmp/d8/wt /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python -c "import typediff, sys; print(typediff.__file__)"
/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python - <<'EOF'
import json, glob
for f in sorted(glob.glob("/tmp/d8/base_out/seed-*.json")):
    r = json.load(open(f))
    org = next((n for n in r["notes"] if n.startswith("origin=")), "")
    ds = {d["id"]: d for d in r["discrepancies"]}
    print("##", org[-70:])
    for fi in r["findings"]:
        d = ds.get(fi["discrepancy_id"])
        ev = [f'{e["type"]}/{e["strength"]}/{e["supports"]}' for e in fi["evidence"] if e["type"] == "RUNTIME"]
        print("   ", fi["discrepancy_id"], d["kind"] if d else "crash", (d["statement"][:48] if d else ""), "->", fi["tier"], fi["decided_by"], d["reveal_relation"] if d else "", ev)
EOF
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
git worktree remove --force /tmp/d8/wt
git worktree prune
git status --short | head
