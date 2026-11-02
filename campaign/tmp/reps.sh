#!/usr/bin/env bash
H=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/seeds/harvested
C=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/tmp/chk.sh
export CHK_OUT=10 CHK_LINES=40
for n in ty__exception__control_flow__80 ty__narrow__conditionals__in__16 ty__narrow__aliased_conditions__9 pyright__typeIs11 pyright__tupleLiteralInference5; do
  F=$(ls $H/*/$n.py | head -1)
  bash $C $F
done
