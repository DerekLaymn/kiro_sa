for p in mypy ty pyright; do
  echo -n "$p latest on PyPI: "
  timeout 30 curl -s https://pypi.org/pypi/$p/json | python3 -c "import sys,json; d=json.load(sys.stdin); v=d['info']['version']; t=d['releases'][v][0]['upload_time_iso_8601']; print(v, t)"
done
echo -n "pyright latest on npm: "
timeout 30 curl -s https://registry.npmjs.org/pyright/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"
