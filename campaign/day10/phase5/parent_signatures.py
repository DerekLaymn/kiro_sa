"""Day 10 phase 5: is a mutated parent rediscovery-only? For each parent of runs/hits that has mutants in runs/day10/out:
the coarse signature of a LIVE discrepancy = (kind, mypy codes, ty codes, pyright rules). A mutant signature is "new" when
the parent's own live findings (parent run alone, /tmp/d10p5/parents-out) do not contain it. Prints per parent: programs,
live in mutants, live signatures, new signatures (with counts), and the parent's own live signatures.
Coarse on purpose: it can only overstate rediscovery, so every retirement is also checked by message template by hand."""
import collections, glob, json, os

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'


def sigs(path):
    d = json.load(open(path))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    src = (org[0][7:] if org else '').replace('seed ', '')
    out = []
    for fi in d['findings']:
        if fi['dismissal'] is not None:
            continue
        dis = next((x for x in d['discrepancies'] if x['id'] == fi['discrepancy_id']), None)
        if dis is None:  # crash finding (id C..)
            out.append(('crash', (), (), ()))
            continue
        s = (dis['kind'],
             tuple(sorted({x.get('code') or '-' for x in dis['mypy']})),
             tuple(sorted({x.get('code') or '-' for x in dis['ty']})),
             tuple(sorted({x.get('code') or '-' for x in dis['pyright']})))
        out.append(s)
    return os.path.basename(src)[:-3], out


par = {}
for f in glob.glob('/tmp/d10p5/parents-out/seed-*.json'):
    name, s = sigs(f)
    par[name] = collections.Counter(s)
mut = collections.defaultdict(lambda: [0, collections.Counter()])
for f in glob.glob(R + 'runs/day10/out/seed-*.json'):
    name, s = sigs(f)
    if '__mut' not in name:
        continue
    p = name.split('__mut')[0]
    mut[p][0] += 1
    mut[p][1].update(s)
for p in sorted(mut):
    if p not in par:
        continue
    n, c = mut[p]
    new = {k: v for k, v in c.items() if k not in par[p]}
    print('%s: programs=%d live=%d signatures=%d new_signatures=%d (live in new=%d); parent live=%d' % (
        p, n, sum(c.values()), len(c), len(new), sum(new.values()), sum(par[p].values())))
    for k, v in sorted(new.items(), key=lambda kv: -kv[1]):
        print('    NEW x%d %s' % (v, k))
    for k, v in sorted(par[p].items(), key=lambda kv: -kv[1]):
        print('    parent x%d %s' % (v, k))
