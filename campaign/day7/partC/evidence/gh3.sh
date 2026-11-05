cd /tmp/d7
for n in 9283 9740 6178 6783 5139 4798 5090 11961; do
  echo "######## pyright#$n"
  gh issue view $n --repo microsoft/pyright --json title,state,closedAt,body,comments 2>&1 > /tmp/d7/pr$n.json
  python3 - <<EOF
import json
d = json.load(open('/tmp/d7/pr$n.json'))
txt = d['body'] + ' '.join(c['body'] for c in d['comments'])
print(d['title'][:100], d['state'], d.get('closedAt'))
import re
for kw in ('__get__', 'descriptor', 'decorat', 'typeUtils', 'retainTypeAlias'):
    print('  ', kw, len(re.findall(kw, txt)))
print(d['body'][:300].replace('\n', ' '))
EOF
done
for q in "except" "tuple unpacking" "partially"; do
  echo "######## ty :: $q"; gh search issues --repo astral-sh/ty --limit 15 --json number,title,state "$q narrowing" 2>&1 | head -c 2500; echo
done
