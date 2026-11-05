#!/bin/bash
uv venv /tmp/d7pd/ty98 --python 3.13 2>&1 | tail -2
uv pip install --python /tmp/d7pd/ty98/bin/python ty==0.0.98 2>&1 | tail -3
/tmp/d7pd/ty98/bin/ty --version
curl -s https://pypi.org/pypi/ty/json | python3 -c "
import sys,json
d=json.load(sys.stdin)
for v in ['0.0.97','0.0.98']:
    print(v, [f['upload_time'] for f in d['releases'].get(v,[])][:1])
"
