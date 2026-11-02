import json
import sys
from pathlib import Path

f = sorted(Path(sys.argv[1]).glob("seed-*.json"))[5]
r = json.loads(f.read_text())
print(list(r.keys()))
print({k: (type(v).__name__, (list(v.keys()) if isinstance(v, dict) else len(v) if isinstance(v, list) else v)) for k, v in r.items() if k != "source"})
print(json.dumps(r["discrepancies"][0], indent=1)[:2500] if r["discrepancies"] else "no discrepancies")
print(json.dumps(r["findings"][0], indent=1)[:1500] if r["findings"] else "no findings")
