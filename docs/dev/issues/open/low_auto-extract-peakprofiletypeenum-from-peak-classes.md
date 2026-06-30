# 34. Auto-Extract `PeakProfileTypeEnum` from Peak Classes

**Priority:** `[priority] low`

**Type:** Design

Three related TODOs in `enums.py` ask whether `PeakProfileTypeEnum`
values can be auto-extracted from the actual peak profile classes in
`peak/cwl.py`, `tof.py`, `total.py` instead of being hardcoded, and
whether the same pattern can be reused for other enums.

**TODOs:**

- [enums.py](../../../../src/easydiffraction/datablocks/experiment/item/enums.py#L153)
- [enums.py](../../../../src/easydiffraction/datablocks/experiment/item/enums.py#L157)
- [enums.py](../../../../src/easydiffraction/datablocks/experiment/item/enums.py#L158)

**Depends on:** related to issue 9.
