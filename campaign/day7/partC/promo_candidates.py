"""Day 7 morning: live findings with strong bug evidence (or a live crash), their origin parent, the best difflib
ratio to any file in runs/hits (body without header comments, as campaign/day4m/check_hits.py), and the file path."""
import difflib, glob, json, os, re, sys
R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + (sys.argv[1] if len(sys.argv) > 1 else 'runs/day7/out')
def body(src):
    return "\n".join(ln for ln in src.split("\n") if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip())
hb = {os.path.basename(p): body(open(p).read()) for p in glob.glob(R + 'runs/hits/*.py')}
rows = []
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    d = json.load(open(f))
    for fi in d['findings']:
        if fi['dismissal'] is not None:
            continue
        strong = [e for e in fi['evidence'] if e['strength'] == 'strong' and 'bug' in str(e['supports'])]
        if not strong:
            continue
        org = [x for x in d['notes'] if x.startswith('origin=')]
        src = org[0][7:] if org else ''
        b = body(d['source'])
        best = max((difflib.SequenceMatcher(None, b, v, autojunk=False).ratio(), k) for k, v in hb.items())
        rows.append((best[0], best[1], d['case_id'], fi['discrepancy_id'], os.path.basename(src), len(strong)))
rows.sort()
for r in rows:
    print('%.2f %s %s %s <- %s | origin %s | strong=%d' % (r[0], r[2], r[3], '', r[1][:55], r[4][:70], r[5]))
