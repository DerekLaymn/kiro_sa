"""Day 10: verify the generator sessions (plan day10-morning.md section 8 step 5).
Usage: check_gen_sessions.py SINCE_FILE   (sessions whose session.json is newer than SINCE_FILE, workspace /tmp/d10/work)
Prints counts per (modelId, effortLevel) and any session whose messages mention opus, gpt-* or sol-5.6.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

since = Path(sys.argv[1]).stat().st_mtime
BAD = re.compile(r"(?<![A-Za-z0-9+/=])(?:claude-)?opus(?![A-Za-z0-9+/=])|(?<![A-Za-z0-9+/=])gpt-[0-9]|(?<![A-Za-z0-9+/=])sol-5\.6", re.I)
combo = Counter()
total = 0
bad = []
for sj in Path.home().glob(".kiro/sessions/*/sess_*/session.json"):
    if sj.stat().st_mtime < since:
        continue
    d = json.loads(sj.read_text())
    if "/tmp/d10/work" not in d.get("workspacePaths", []):
        continue
    total += 1
    combo[(d.get("modelId"), d.get("effortLevel"))] += 1
    if d.get("effortLevel") is None:
        print("  no effortLevel in", sj.parent.name, "created", d.get("createdAt"))
    text = (sj.parent / "messages.jsonl").read_text(errors="replace") if (sj.parent / "messages.jsonl").exists() else ""
    hits = sorted(set(m.group(0).lower() for m in BAD.finditer(text + sj.read_text())))
    if hits:
        bad.append((sj.parent.name, hits))
print(f"worker sessions since {sys.argv[1]}: {total}")
for (m, e), n in combo.items():
    print(f"  modelId={m} effortLevel={e}: {n}")
print(f"sessions mentioning opus/gpt-*/sol-5.6: {len(bad)}")
for name, hits in bad:
    print("  ", name, hits)
