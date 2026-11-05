import json, glob, os
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day6/'
n = 0
for f in sorted(glob.glob(R + 'out/seed-*.json')):
    a = json.load(open(f))
    b = json.load(open(f.replace('/out/', '/replay/')))
    bf = {x['discrepancy_id']: x for x in b['findings']}
    disc = {x['id']: x for x in b['discrepancies']}
    org = [x for x in a['notes'] if x.startswith('origin=')]
    src = os.path.basename(org[0][7:]) if org else ''
    for x in a['findings']:
        y = bf.get(x['discrepancy_id'])
        if y is None:
            print('MISSING', f); continue
        if (x['dismissal'], x['decided_by']) != (y['dismissal'], y['decided_by']):
            dd = disc.get(x['discrepancy_id'], {})
            n += 1
            print(f"{a['case_id']} {src[:62]} {x['discrepancy_id']} L{dd.get('anchor')} {dd.get('kind')}/{dd.get('reveal_relation')} {dd.get('statement','')[:60]!r}")
            print(f"     {x['dismissal']}/{x['decided_by']} -> {y['dismissal']}/{y['decided_by']} ({y.get('reasoning','')[:70]})")
print(n)
