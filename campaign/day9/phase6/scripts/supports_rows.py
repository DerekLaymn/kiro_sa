"""Day 9 phase 6: for each only_pyright runtime_supports row of runs/day9/out print the statement, the pyright message
and the evidence text, to group the 22 rows by mechanism. Read-only."""
import glob
import json

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
OUT = R + 'runs/day9/out'
n = 0
for f in sorted(glob.glob(OUT + '/seed-*.json')):
    r = json.load(open(f))
    fs = {x['discrepancy_id']: x for x in r['findings']}
    origin = next((x[7:] for x in r.get('notes', []) if x.startswith('origin=')), '')
    for d in r['discrepancies']:
        if d['kind'] == 'only_pyright' and d['reveal_relation'] == 'runtime_supports':
            n += 1
            fi = fs[d['id']]
            if n == 1:
                print('KEYS discrepancy:', sorted(d.keys()))
                print('KEYS finding:', sorted(fi.keys()))
            print('-----', f.split('/')[-1][:-5], d['id'], origin.split('/')[-1], 'L%s' % d.get('line'))
            print('   stmt:', d['statement'][:100])
            for tool in ('mypy', 'ty', 'pyright'):
                v = d.get(tool)
                if v is None:
                    v = d.get(tool + '_messages')
                print('   %s:' % tool, str(v)[:260].replace('\n', ' '))
            for e in fi['evidence']:
                print('   ev:', e.get('kind'), e.get('strength'), e.get('supports'), str(e.get('text', ''))[:300].replace('\n', ' '))
print('rows:', n)
