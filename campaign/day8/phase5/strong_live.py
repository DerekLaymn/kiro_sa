"""Day 8 phase 5: list every live finding of runs/day8/out with strong bug evidence (and the programs holding them),
plus per-program: parent, live count, dismissed count, dismissal entries. Read-only."""
import glob, json, os, collections
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + 'runs/day8/out'
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    path = (org[0][7:] if org else '').replace('seed ', '')
    kind_of = {x['id']: x['kind'] for x in d['discrepancies']}
    live = [fi for fi in d['findings'] if fi['dismissal'] is None]
    strong = [fi for fi in live if any(e['strength'] == 'strong' and 'bug' in str(e['supports']) for e in fi['evidence'])]
    for fi in strong:
        ev = [e for e in fi['evidence'] if e['strength'] == 'strong' and 'bug' in str(e['supports'])]
        print(os.path.basename(f)[:-5], path[len('runs/day8/gen/'):], fi['discrepancy_id'], kind_of.get(fi['discrepancy_id']))
        for e in ev:
            print('    ', e.get('kind'), str(e.get('text', e))[:200].replace('\n', ' '))
