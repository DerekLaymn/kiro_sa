#!/bin/bash
# verbatim copies of the 8 strong-evidence programs of campaign/day9-triage.txt
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=$K/campaign/day9/phase6/repro
G=$K/runs/day9/gen
mkdir -p $R
cp $G/constructors_metaclasses/gen1_c86958a8.py $R/p_meta_c86958a8.py
cp $G/typevartuple_unpack/gen1_4d7d067f.py $R/p_tvt_4d7d067f.py
cp $G/inheritance_mro/d3p_inheritance_mro_total_ordering_inherited_lt__mut0_73c4aa3f.py $R/p_totord_73c4aa3f.py
cp $G/constructors_metaclasses/d4v_metaclass_reflected_op__mut0_dcb547ed.py $R/p_reflmeta_dcb547ed.py
cp $G/typevartuple_unpack/d3p_typevartuple_unpack_paramspec_default_after_tvt__mut0_49d4094b.py $R/p_tvtps_49d4094b.py
cp $G/typevartuple_unpack/d3p_typevartuple_unpack_paramspec_default_after_tvt__mut0_df958820.py $R/p_tvtps_df958820.py
cp $G/typevartuple_unpack/d3p_typevartuple_unpack_paramspec_default_after_tvt__mut0_9940d14a.py $R/p_tvtps_9940d14a.py
cp $G/gradual_any/gen5_ade5dcc3.py $R/p_any_ade5dcc3.py
ls $R
ls /home/derek/.config/kiro-hooks/
