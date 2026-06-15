# 37. Rename Experiment `.type` Property

**Priority:** `[priority] low`

**Type:** Naming

`ExperimentBase.type` returns experimental metadata but the name shadows
the built-in `type`. A TODO suggests finding a better name.

**TODOs:**

- [base.py](src/easydiffraction/datablocks/experiment/item/base.py#L75)

**Depends on:** nothing.
