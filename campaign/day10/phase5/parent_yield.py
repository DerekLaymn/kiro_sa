"""Day 10 phase 5: yield of every parent. For each parent name (file name before '__mut'), over the Day-9 judge run
(runs/day10/out): programs, live findings, strong live findings, live without only_pyright, dismissed findings, tool crashes,
and the three most common dismissal entries. A parent whose mutants have 0 live findings only rediscovers known issues.
Also: whether the parent is in runs/hits, runs/hits-dropped, or neither (seed, harvested, reserve)."""
import collections, glob, json, os

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
hits = {os.path.basename(p)[:-3] for p in glob.glob(R + 'runs/hits/*.py')}
dropped = {os.path.basename(p)[:-3] for p in glob.glob(R + 'runs/hits-dropped/*.py')}
stat = collections.defaultdict(collections.Counter)
ent = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(R + 'runs/day10/out/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    base = os.path.basename((org[0][7:] if org else '').replace('seed ', ''))[:-3]
    if '__mut' not in base:
        continue
    parent = base.split('__mut')[0]
    kind_of = {x['id']: x['kind'] for x in d['discrepancies']}
    live = [fi for fi in d['findings'] if fi['dismissal'] is None]
    dis = [fi for fi in d['findings'] if fi['dismissal'] is not None]
    strong = [fi for fi in live if any(e['strength'] == 'strong' and 'bug' in str(e['supports']) for e in fi['evidence'])]
    c = stat[parent]
    c['programs'] += 1
    c['live'] += len(live)
    c['live_no_pyright_only'] += sum(1 for fi in live if kind_of.get(fi['discrepancy_id']) != 'only_pyright')
    c['strong'] += len(strong)
    c['dismissed'] += len(dis)
    c['crashes'] += len(d.get('crashes') or [])
    for fi in dis:
        ent[parent][str(fi['dismissal'])[:40]] += 1
print('parent | where | programs live live_no_pyright_only strong dismissed crashes | top dismissals')
for p in sorted(stat, key=lambda p: (-stat[p]['live'], p)):
    where = 'hits' if p in hits else ('DROPPED' if p in dropped else 'other')
    c = stat[p]
    print('%-62s %-7s %2d %3d %3d %2d %3d %2d | %s' % (p, where, c['programs'], c['live'], c['live_no_pyright_only'],
          c['strong'], c['dismissed'], c['crashes'], dict(ent[p].most_common(3))))
