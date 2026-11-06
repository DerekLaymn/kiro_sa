"""Day 10 phase 5: the discrepancies of the two mypy#8595 programs (alone runs in /tmp/d10p5/alone/out1 and out10)."""
import glob, json
for n in (1, 10):
    for f in glob.glob('/tmp/d10p5/alone/out%d/seed-*.json' % n):
        d = json.load(open(f))
        print('=====', n, [x for x in d['notes'] if x.startswith('origin')])
        for x in d['discrepancies']:
            print(x['id'], x['kind'], 'L%s' % x['anchor'], repr(x['statement'][:70]))
            for t in ('mypy', 'ty', 'pyright'):
                for g in x[t]:
                    print('   ', t, g.get('code'), (g.get('revealed_type') or g.get('message') or '')[:140])
