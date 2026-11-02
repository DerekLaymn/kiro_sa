#!/usr/bin/env bash
export TYPEDIFF_LLM=null
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
PY=.venv/bin/python
S="$PY scripts/kbloop_sample.py runs/day2/out0"
SP="--split runs/day2/split"
echo "##### P1 reveal gradual"; $S reveal_mismatch gradual --n 8 $SP
echo "##### P2 reveal different"; $S reveal_mismatch different --n 8 $SP
echo "##### P3 reveal uncomparable"; $S reveal_mismatch uncomparable --n 8 $SP
echo "##### P4 only_mypy assignment"; $S only_mypy assignment --n 8 $SP
echo "##### P5 only_mypy assert-type"; $S only_mypy assert-type --n 8 $SP
echo "##### P6 only_ty type-assertion-failure"; $S only_ty type-assertion-failure --n 8 $SP
echo "##### P7 reveal ty_more_precise"; $S reveal_mismatch ty_more_precise --n 8 $SP
echo "##### P8 only_ty unresolved-reference"; $S only_ty unresolved-reference --n 8 $SP
