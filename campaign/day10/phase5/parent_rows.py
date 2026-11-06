"""Day 10 phase 5: live rows (kind, first message per tool) of the mutants of selected parents, runs/day10/out. Read-only."""
import glob, json, os, sys

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = os.environ.get('OUTDIR', R + 'runs/day10/out')  # OUTDIR=/tmp/d10p5/parents-out lists the parents' own rows
WANT = sys.argv[1:]


def one(lst):
    if not lst:
        return '-'
    x = lst[0]
    return ('[%s] %s' % (x.get('code') or '', (x.get('revealed_type') or x.get('message') or '')))[:150].replace('\n', ' ')


for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    name = os.path.basename((org[0][7:] if org else '').replace('seed ', ''))[:-3]
    p = name.split('__mut')[0]
    if p not in WANT:
        continue
    for fi in d['findings']:
        if fi['dismissal'] is not None:
            continue
        dis = next((x for x in d['discrepancies'] if x['id'] == fi['discrepancy_id']), None)
        if dis is None:
            print(name, 'CRASH finding')
            continue
        print('%s %s | %s %s L%s' % (p, name[len(p):], dis['id'], dis['kind'], dis['anchor']))
        print('    mypy:   ', one(dis['mypy']))
        print('    ty:     ', one(dis['ty']))
        print('    pyright:', one(dis['pyright']))
