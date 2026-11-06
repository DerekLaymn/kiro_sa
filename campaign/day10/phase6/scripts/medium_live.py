"""Day 10 phase 6: live findings of runs/day10/out with MEDIUM (not strong) evidence that supports a bug, grouped by kind.
Read-only. Used to check that no pattern outside the strong list and the 13 only_pyright rows was left unexamined."""
import collections
import glob
import json
import os

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + 'runs/day10/out'
by_kind = collections.defaultdict(list)
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    path = (org[0][7:] if org else '').replace('seed ', '')
    kind_of = {x['id']: x['kind'] for x in d['discrepancies']}
    for fi in d['findings']:
        if fi['dismissal'] is not None:
            continue
        ev = [e for e in fi['evidence'] if 'bug' in str(e['supports'])]
        if not ev:
            continue
        top = 'strong' if any(e['strength'] == 'strong' for e in ev) else ('medium' if any(e['strength'] == 'medium' for e in ev) else 'weak')
        if top == 'medium':
            e = [e for e in ev if e['strength'] == 'medium'][0]
            by_kind[kind_of.get(fi['discrepancy_id'])].append(
                (os.path.basename(f)[:-5], path[len('runs/day10/gen/'):], fi['discrepancy_id'], str(e.get('text', e))[:170].replace('\n', ' ')))
for k, rows in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
    print('##', k, len(rows))
    for r in rows:
        print('   ', *r)
