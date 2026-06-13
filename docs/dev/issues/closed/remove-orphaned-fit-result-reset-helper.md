# 105. Remove Orphaned Fit-Result Reset Helper

Closed (#183): `Analysis._clear_fit_result_projection` is no longer
orphaned — it is called by the undo-fit rollback path
(`analysis.py:1412`), resetting fit-result descriptors in place while
preserving the active instance. This matches the issue's allowed
"reintroduce a caller" resolution.
