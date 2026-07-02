# 102. Drop Compute-and-Ignore `result_kind` Validation in CIF Restore

**Priority:** `[priority] low`

**Type:** Dead code / clarity **Source:** Review 8 finding F7.
**Recommended:** fold into the emcee-minimizer plan.

`_restore_persisted_fit_state`
([serialize.py:595-611](../../../../src/easydiffraction/io/cif/serialize.py))
calls `FitResultKindEnum(result_kind_value)` purely for the warning side
effect; the result is discarded. After P1.10 absorbed the
Bayesian-specific categories there is nothing else to do per
`result_kind`.

**Fix:** replace with a validator helper that takes a string and logs
the warning, or move the warning into `fit_result.result_kind` setter so
invalid values are caught on read. Either removes the "compute and
ignore" pattern.

**Depends on:** nothing.
