#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
timeout 30 grep -n -i "total_ordering" campaign/day[3-8]-*.md typediff/data/known_upstream.json < /dev/null | cut -c1-300 | head -30
echo ----
cat runs/hits/d3p_inheritance_mro_total_ordering_inherited_lt.py
