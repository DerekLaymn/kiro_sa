#!/usr/bin/env bash
H=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/seeds/harvested
C=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/tmp/chk.sh
export CHK_OUT=8
bash $C $H/gradual_any/mypy__check_classes__testForwardReferencesInNewTypeMRORecomputed.py
bash $C $H/gradual_any/mypy__check_protocols__testSimpleProtocolOneMethodOverride.py
bash $C $H/callables/mypy__check_unions__testSimplifyUnionWithCallable.py
bash $C $H/gradual_any/mypy__check_newsemanal__testForwardBaseDeferAttr.py
