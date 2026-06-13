# 48. Fix CrysPy TOF Instrument Default

**Priority:** `[priority] low`

**Type:** Bug workaround

`TofInstrument.calib_d_to_tof_quad` defaults to `-0.00001` because
CrysPy does not accept `0`.

**TODOs:**

- [tof.py](src/easydiffraction/datablocks/experiment/categories/instrument/tof.py#L95)

**Depends on:** upstream CrysPy fix.
