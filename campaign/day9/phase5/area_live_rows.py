"""Day 9 phase 5: live rows of the two new areas (context_managers, dunder_dispatch) of runs/day9/out, one line per
live finding: program, id, kind, source line, per-tool message (first 110 chars), whether the tool gate hint says deprecated.
Read-only. Usage: area_live_rows.py <area> [<area> ...]"""
import glob, json, os, sys

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
areas = sys.argv[1:]
first = True
for f in sorted(glob.glob(R + 'runs/day9/out/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    path = (org[0][7:] if org else '').replace('seed ', '')
    parts = path.split('/')
    if len(parts) < 4 or parts[3] not in areas:
        continue
    live = [fi for fi in d['findings'] if fi['dismissal'] is None]
    if not live:
        continue
    disc = {x['id']: x for x in d['discrepancies']}
    for fi in live:
        x = disc[fi['discrepancy_id']]
        if first:
            print('keys of a discrepancy:', sorted(x.keys()))
            first = False
        tools = x.get('tool_views') or x.get('views') or {}
        print(os.path.basename(path), fi['discrepancy_id'], x['kind'], '|', str(x.get('anchor') or x.get('source_line') or x.get('line'))[:70])
        print('     ', json.dumps({k: v for k, v in x.items() if k in ('summary', 'tools', 'messages', 'codes')})[:400])
