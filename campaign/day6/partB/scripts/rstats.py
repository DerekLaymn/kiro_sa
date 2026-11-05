import json, glob, os, collections, re
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day6/replay/'
grp = collections.defaultdict(collections.Counter)
crash = collections.Counter()
crash_live = collections.Counter()
cons = collections.Counter()
pyr_ran = 0
pyr_diag_cases = 0
for f in sorted(glob.glob(R + 'seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    o = org[0][7:] if org else ''
    m = re.search(r'parents/([A-Z]_\w+?)/', d['source'][:600])
    g = m.group(1) if m else 'fresh'
    c = grp[g]
    c['programs'] += 1
    c['discrepancies'] += len(d['discrepancies'])
    c['crashes'] += len(d['crashes'])
    lv = [x for x in d['findings'] if x['dismissal'] is None]
    c['live'] += len(lv)
    c['dismissed'] += len(d['findings']) - len(lv)
    c['programs_live'] += 1 if lv else 0
    c['strong_programs'] += 1 if any(e['strength'] == 'strong' and 'bug' in str(e['supports']) for x in lv for e in x['evidence']) else 0
    for k in d['crashes']:
        crash[(k['tool'], k['signature'])] += 1
    for x in d['findings']:
        if x['signature'] and x['dismissal'] is None:
            crash_live[x['signature']] += 1
        for e in x['evidence']:
            if e['type'] == 'CONSENSUS':
                s = e['summary']
                key = 'agrees-with-ty' if 'like ty' in s else 'agrees-with-mypy' if 'like mypy' in s else s[:60]
                cons[key] += 1
    if any(d['diagnostics'].get('pyright')) or True:
        pyr_ran += 1 if 'pyright' in d['diagnostics'] else 0
        pyr_diag_cases += 1 if d['diagnostics'].get('pyright') else 0
tot = collections.Counter()
for g, c in sorted(grp.items()):
    print(g, dict(c))
    tot.update(c)
print('TOTAL', dict(tot))
print('crashes by tool/signature (tool crash events):', dict(crash))
print('live crash findings by signature:', dict(crash_live))
print('pyright consensus evidence:', dict(cons))
print('cases with pyright key', pyr_ran, 'cases with >=1 pyright diag', pyr_diag_cases)
