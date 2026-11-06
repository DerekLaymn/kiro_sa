"""Count the gh search queries of Phase 6 by kind and repository, per output file. Read-only."""
import glob
from collections import Counter

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day9/phase6/search/'
total = Counter()
for f in sorted(glob.glob(R + 'out_*.txt')):
    c = Counter()
    for line in open(f):
        if line.startswith('### '):
            kind, repo = line.split()[1:3]
            c[(kind, repo)] += 1
    print(f.split('/')[-1], sum(c.values()))
    for k, v in sorted(c.items()):
        print('   ', k, v)
        total[k] += v
print('TOTAL search queries', sum(total.values()))
for k, v in sorted(total.items()):
    print('   ', k, v)
views = 0
for f in sorted(glob.glob(R + 'views*.out')):
    n = sum(1 for line in open(f) if line.startswith('################ '))
    print(f.split('/')[-1], 'views', n)
    views += n
print('TOTAL views', views)
