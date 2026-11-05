import json, glob, os, sys
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
pat = sys.argv[1:]  # substrings of source name; empty -> fresh gen only
def msgs(L):
    out = []
    for x in L:
        m = x.get('revealed_type') and ('reveal ' + x['revealed_type']) or ('[%s] %s' % (x.get('code'), x['message']))
        out.append(m[:140])
    return ' | '.join(out) or '-'
for f in sorted(glob.glob(R + 'runs/day6/replay/seed-*.json')):
    d = json.load(open(f))
    org = [n for n in d['notes'] if n.startswith('origin=')]
    org = org[0][7:].replace('seed ', '') if org else ''
    src = os.path.basename(org)
    ok = (any(p in src for p in pat) if pat else src.startswith('gen'))
    if not ok:
        continue
    disc = {x['id']: x for x in d['discrepancies']}
    for fi in d['findings']:
        if fi['dismissal'] is not None:
            continue
        dd = disc.get(fi['discrepancy_id'], {})
        print(f"{d['case_id']} {src[:70]} {fi['discrepancy_id']} L{dd.get('anchor')} {dd.get('kind')}/{dd.get('reveal_relation')} :: {dd.get('statement')}")
        for t in ('mypy', 'ty', 'pyright'):
            print(f"      {t}: {msgs(dd.get(t, []))}")
        for e in fi['evidence']:
            if e['strength'] != 'weak' and e['type'] not in ('CONSENSUS',):
                print(f"      EV {e['type']}/{e['strength']}/{e['supports']}: {e['summary'][:200]}")
