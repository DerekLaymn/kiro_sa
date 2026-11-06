"""print the source of Day-7 reports: show_src.py RUN STEM [STEM ...]"""
import json
import sys

for stem in sys.argv[2:]:
    r = json.load(open(f"{sys.argv[1]}/{stem}.json"))
    print("=" * 30, stem)
    for i, line in enumerate(r["source"].splitlines(), 1):
        print(i, line)
