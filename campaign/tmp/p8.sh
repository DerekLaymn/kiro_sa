#!/usr/bin/env bash
H=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/seeds/harvested
C=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/tmp/chk.sh
bash $C $H/gradual_any/mypy__check_newsemanal__testNewAnalyzerTypeArgValueRestriction.py
bash $C $H/enums_literals/pyright__literalForLoop1.py
bash $C $H/gradual_any/pyright__typeCheckOnly1.py
