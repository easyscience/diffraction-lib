# 21. Clarify CrysPy TOF Background CIF Tag Names

**Priority:** `[priority] medium`

**Type:** Correctness / Naming

The CrysPy calculator uses TOF background CIF tags
(`_tof_backgroundpoint_time`, `_tof_backgroundpoint_intensity`) and
hardcoded `0.0` intensity values marked with `TODO: !!!!????`. The
mapping and the hardcoded defaults need verification.

**TODOs:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L734)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L735)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L738)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L739)

**Depends on:** nothing.
