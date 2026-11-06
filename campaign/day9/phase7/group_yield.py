"""Per-group, per-parent and per-area yield of the Day 9 judge run (adapted from campaign/day8/phase4/group_yield.py).
Group = subdirectory of runs/day9/parents that holds the parent of the mutant (see campaign/day9/mk_groups.sh);
fresh programs (no `__mut` in the name) form the group `fresh`. Counts: programs, programs with a live finding,
live findings, live with strong bug evidence, dismissed findings, tool crashes (as in kbloop_stats `tool_crashes`)."""
import collections, glob, json, os
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + 'runs/day9/out'
parent2group = {}
for g in sorted(os.listdir(R + 'runs/day9/parents')):
    for f in os.listdir(R + 'runs/day9/parents/' + g):
        parent2group[f[:-3]] = g
groups = collections.defaultdict(collections.Counter)
parents = collections.defaultdict(collections.Counter)
areas = collections.defaultdict(collections.Counter)
kinds = collections.defaultdict(collections.Counter)
total = collections.Counter()
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    path = (org[0][7:] if org else '').replace('seed ', '')
    parts = path.split('/')
    area = parts[3] if path.startswith('runs/day9/gen/') else '?'
    base = os.path.basename(path)
    parent = base.split('__mut')[0] if '__mut' in base else 'fresh'
    group = parent2group.get(parent, 'UNMAPPED:' + parent) if parent != 'fresh' else 'fresh'
    live = [fi for fi in d['findings'] if fi['dismissal'] is None]
    dis = [fi for fi in d['findings'] if fi['dismissal'] is not None]
    strong = [fi for fi in live if any(e['strength'] == 'strong' and 'bug' in str(e['supports']) for e in fi['evidence'])]
    for c in (groups[group], parents[parent], areas[area], total):
        c['programs'] += 1
        c['programs_with_live'] += 1 if live else 0
        c['live'] += len(live)
        c['live_strong'] += len(strong)
        c['dismissed'] += len(dis)
        c['tool_crashes'] += len(d.get('crashes') or [])
    kind_of = {x['id']: x['kind'] for x in d['discrepancies']}
    for fi in live:
        kinds[group][kind_of.get(fi['discrepancy_id'], '?')] += 1
cols = ['programs', 'programs_with_live', 'live', 'live_strong', 'dismissed', 'tool_crashes']
def show(title, rows):
    print(title)
    print('  %-62s ' % 'name' + ' '.join('%s' % c[:12].rjust(12) for c in cols))
    for k, c in sorted(rows.items()):
        print('  %-62s ' % k[:62] + ' '.join(str(c[x]).rjust(12) for x in cols))
show('per group:', groups)
show('per parent / fresh:', parents)
show('per area dir:', areas)
show('total:', {'ALL': total})
print('live by kind per group:')
for g, c in sorted(kinds.items()):
    print('  %-24s %s' % (g, dict(c)))
