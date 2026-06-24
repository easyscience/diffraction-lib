# 165. cryspy Backend Hardcodes `flag_only_nuclear` (No Magnetic Structures)

**Priority:** `[priority] low`

**Type:** Engine limitation

The cryspy calculator hardcodes `flag_only_nuclear = True` for all
structures, so magnetic structures cannot be calculated through this
backend. This is an undocumented capability gap a user can hit by
supplying a magnetic model.

**Fix:** thread the nuclear/magnetic flag from the structure model, and
surface a clear "magnetic structures not yet supported" message until
the backend path is implemented.

**TODOs / locations:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L176)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L264)

**Depends on:** nothing.
