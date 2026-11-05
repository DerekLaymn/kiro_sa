import json, glob, os, collections
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
rows = []
progs = {}
for f in sorted(glob.glob(R + 'runs/day6/out/seed-*.json')):
    d = json.load(open(f))
    org = [n for n in d['notes'] if n.startswith('origin=')]
    org = org[0][7:].replace('seed ', '') if org else ''
    src = os.path.basename(org)
    progs[d['case_id']] = (src, org)
    disc = {x['id']: x for x in d['discrepancies']}
    for fi in d['findings']:
        dd = disc.get(fi['discrepancy_id'], {})
        strong = sum(1 for e in fi['evidence'] if e['strength'] == 'strong' and 'bug' in str(e['supports']))
        cb = fi.get('closed_by')
        cbid = cb.get('id') if isinstance(cb, dict) else cb
        kind = dd.get('kind') or ('crash' if (fi['discrepancy_id'] or '').startswith('C') else None)
        pyr = dd.get('pyright') or []
        rows.append(dict(case=d['case_id'], src=src, live=fi['dismissal'] is None, kind=kind, strong=strong,
                         closed=cbid, dis=fi['dismissal'], sig=fi['signature'], did=fi['discrepancy_id'],
                         stmt=dd.get('statement'), pyright=len(pyr)))
json.dump(rows, open('/tmp/d6/rows.json', 'w'))
# group live by parent family (source name before __mut)
fam = collections.defaultdict(list)
for r in rows:
    if r['live']:
        key = r['src'].split('__mut')[0] if '__mut' in r['src'] else r['src']
        fam[key].append(r)
print('live findings', sum(len(v) for v in fam.values()), 'programs', len(set(r['case'] for r in rows if r['live'])))
for k, v in sorted(fam.items(), key=lambda kv: -len(kv[1])):
    kinds = collections.Counter(r['kind'] for r in v)
    print(f'{len(v):3d} {k}  strong={sum(1 for r in v if r["strong"])}  {dict(kinds)}')
