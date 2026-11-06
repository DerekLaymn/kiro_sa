import json
d = json.load(open('/tmp/d10p5/alone/out7/seed-18d4c7601dee.json'))
print(list(d.keys()))
print(json.dumps(d['discrepancies'][0], indent=1)[:2000])
print(json.dumps(d['findings'][0], indent=1)[:600])
