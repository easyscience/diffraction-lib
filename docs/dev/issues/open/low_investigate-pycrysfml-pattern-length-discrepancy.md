# 23. Investigate PyCrysFML Pattern Length Discrepancy

**Priority:** `[priority] low`

**Type:** Correctness

CrysFML calculator adjusts pattern length post-calculation with a TODO
asking to investigate the origin of the off-by-one discrepancy. The same
epsilon workaround appears in the dict builder.

**TODOs:**

- [crysfml.py](../../../../src/easydiffraction/analysis/calculators/crysfml.py#L124)
- [crysfml.py](../../../../src/easydiffraction/analysis/calculators/crysfml.py#L253)

**Depends on:** nothing.
