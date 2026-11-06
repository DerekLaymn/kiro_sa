#!/bin/bash
D=/tmp/d3v-master/lib/python3.13/site-packages/mypy
grep -n "with\b\|With\|swallow\|suppress" $D/partially_defined.py | head -40
echo ---- messages
grep -rn "swallow\|suppress" $D/partially_defined.py $D/checker.py | head -20
