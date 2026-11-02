#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
mkdir -p $R/runs/hits
cp $R/seeds/harvested/gradual_any/mypy__check_newsemanal__testForwardBaseDeferAttr.py $R/runs/hits/s3r1_mypy_class_base_forward_ref.py
cp $R/seeds/harvested/narrowing_user/pyright__typeIs11.py $R/runs/hits/s3r1_ty_type_equality_narrowing_any.py
ls -la $R/runs/hits | tail -8
git -C $R check-ignore -v runs/hits/s3r1_mypy_class_base_forward_ref.py
