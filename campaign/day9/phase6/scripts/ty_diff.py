"""Compare the ty 0.0.97 (pin) and ty 0.0.99 (newest) sections of every runall result file. Read-only."""
import glob
import re

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day9/phase6/results/'
same = diff = 0
for f in sorted(glob.glob(R + '*.txt')):
    t = open(f).read()
    m97 = re.search(r'--- ty 0\.0\.97 \(.*?\n(.*?)--- ty 0\.0\.99', t, re.S)
    m99 = re.search(r'--- ty 0\.0\.99 \(.*?\n(.*?)--- mypy 2\.4\.0', t, re.S)
    if not (m97 and m99):
        continue
    if m97.group(1) == m99.group(1):
        same += 1
    else:
        diff += 1
        print('DIFFERENT:', f.split('/')[-1])
print('files compared:', same + diff, 'identical ty output:', same, 'different:', diff)
