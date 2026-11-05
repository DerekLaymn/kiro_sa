import json
from pathlib import Path

d = json.loads(Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/typediff/data/known_upstream.json").read_text())
items = d["entries"] if isinstance(d, dict) and "entries" in d else d
print(type(d), list(d.keys()) if isinstance(d, dict) else len(d))
for e in items if isinstance(items, list) else []:
    print(e.get("id"), e.get("kind"), e.get("tool"), e.get("url", e.get("issue", "")), "|", (e.get("signature") or e.get("title") or "")[:90])
