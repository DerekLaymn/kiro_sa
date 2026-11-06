"""Check the '21 only_ty rows' claim of day10-verification.md D10-13: live findings of the programs named
rsv_generics_variance_3c28536f* in a Day-10 report directory. Usage: gv_rows.py OUT_DIR"""
import collections, glob, json, os, sys
OUT = sys.argv[1]
tot = collections.Counter()
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    org = [x for x in d['notes'] if x.startswith('origin=')]
    path = (org[0][7:] if org else '').replace('seed ', '')
    base = os.path.basename(path)
    if 'rsv_generics_variance_3c28536f' not in base:
        continue
    kind_of = {x['id']: x['kind'] for x in d['discrepancies']}
    live = [fi for fi in d['findings'] if fi['dismissal'] is None]
    dis = [fi for fi in d['findings'] if fi['dismissal'] is not None]
    kinds = collections.Counter(kind_of.get(fi['discrepancy_id'], '?') for fi in live)
    print(base, 'discrepancies', len(d['discrepancies']), 'live', len(live), dict(kinds), 'dismissed', len(dis))
    for k, v in kinds.items():
        tot[k] += v
print('total live by kind', dict(tot), 'sum', sum(tot.values()))
