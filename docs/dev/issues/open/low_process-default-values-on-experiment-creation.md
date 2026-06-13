# 24. Process Default Values on Experiment Creation

**Priority:** `[priority] low`

**Type:** Design

Default instrument/peak values for the CrysFML dict are filled in at
calculation time with inline fallbacks rather than being set at
experiment creation.

**TODOs:**

- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L233)

**Depends on:** nothing.
