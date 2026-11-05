import json, glob, os, difflib
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
rows = json.load(open('/tmp/d6/rows.json'))
# recompute live status from replay
import collections
live = collections.defaultdict(list)
for f in sorted(glob.glob(R + 'runs/day6/replay/seed-*.json')):
    d = json.load(open(f))
    for fi in d['findings']:
        if fi['dismissal'] is None:
            strong = sum(1 for e in fi['evidence'] if e['strength'] == 'strong' and 'bug' in str(e['supports']))
            if strong:
                live[d['case_id']].append((fi['discrepancy_id'], strong))
hits = {os.path.basename(p): open(p).read() for p in glob.glob(R + 'runs/hits/*.py')}
def body(s):
    return '\n'.join(l for l in s.splitlines() if not l.startswith('#'))
hb = {k: body(v) for k, v in hits.items()}
out = []
for cid, fl in live.items():
    d = json.load(open(R + 'runs/day6/replay/%s.json' % cid))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    src = os.path.basename(org[0][7:]) if org else ''
    b = body(d['source'])
    best = max(((difflib.SequenceMatcher(None, b, v, autojunk=False).ratio(), k) for k, v in hb.items()))
    out.append((best[0], best[1], cid, src, len(fl)))
out.sort()
for o in out:
    print('%.2f %s <- %s | %s | strong findings=%d' % (o[0], o[2], o[1][:60], o[3][:70], o[4]))
