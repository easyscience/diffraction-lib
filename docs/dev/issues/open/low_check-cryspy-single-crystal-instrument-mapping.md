# 22. Check CrysPy Single-Crystal Instrument Mapping

**Priority:** `[priority] low`

**Type:** Correctness

`_cif_instrument_section` uses an empty `instrument_mapping` dict for
single crystal and a `TODO: Check this mapping!` marker.

**TODOs:**

- [cryspy.py](../../../../src/easydiffraction/analysis/calculators/cryspy.py#L506)

**Depends on:** nothing.
