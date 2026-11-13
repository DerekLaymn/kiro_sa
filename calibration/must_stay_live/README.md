# must_stay_live

Programs with a real discrepancy that NO dismissal may touch (`typediff calibrate` reports a dismissed one as a
violation, see `typediff/calibration.py`). The directory is empty on purpose. It held two programs in the early rounds
of the study (`ty_constant_fold_tuple_subclass.py`, `mypy_stale_alias.py`). Both turned out to be known duplicates of open
ty issues #2171 and #2792, and the decision was to close those shapes with narrow KB entries instead of keeping them
open. They moved to `../known_duplicates/`.

Put a program here when you want a standing guarantee that the pipeline never closes it.
