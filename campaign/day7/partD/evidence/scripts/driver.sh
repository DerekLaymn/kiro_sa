#!/bin/bash
cd /tmp/d7/w
for f in "$@"; do
  timeout 600 bash /tmp/d7/runall.sh /tmp/d7/w/$f.py > /tmp/d7/r_$f.txt 2>&1
  echo "done $f" >> /tmp/d7/driver.log
done
echo ALLDONE >> /tmp/d7/driver.log
