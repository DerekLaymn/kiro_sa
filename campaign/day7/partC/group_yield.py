"""Per-parent and per-group yield of the Day 7 judge run: programs, live findings, live with strong bug evidence,
dismissed, crashes (live / closed). Group = subdirectory of runs/day7/gen; parent = file name before `__mut`."""
import collections, glob, json, os, re, sys
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + 'runs/day7/out'
GEN = R + 'runs/day7/gen'
case2file = {}
for f in glob.glob(OUT + '/seed-*.json'):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    case2file[d['case_id']] = (org[0][7:] if org else '', d)
rows = collections.defaultdict(lambda: collections.Counter())
byarea = collections.defaultdict(lambda: collections.Counter())
for cid, (org, d) in case2file.items():
    path = org.replace('seed ', '')
    area = path.split('/')[3] if path.startswith('runs/day7/gen/') else '?'
    base = os.path.basename(path)
    parent = base.split('__mut')[0] if '__mut' in base else 'fresh'
    key = parent
    r = rows[key]
    a = byarea[area]
    for c in (r, a):
        c['programs'] += 1
        for fi in d['findings']:
            if fi['dismissal'] is None:
                c['live'] += 1
                if any(e['strength'] == 'strong' and 'bug' in str(e['supports']) for e in fi['evidence']):
                    c['live_strong'] += 1
            else:
                c['dismissed'] += 1
        c['tool_crashes'] += len(d.get('crashes') or [])
print('per parent / fresh:')
for k, c in sorted(rows.items()):
    print('  %-70s %s' % (k[:70], dict(c)))
print('per area dir:')
for k, c in sorted(byarea.items()):
    print('  %-24s %s' % (k, dict(c)))
