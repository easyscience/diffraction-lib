# 33. Make `DatablockItem._update_categories` Abstract

**Priority:** `[priority] medium`

**Type:** Design

`DatablockItem._update_categories` has a TODO to make it abstract and
implement it in subclasses for structures (symmetry + constraints) and
experiments (calculation updates). Currently it is a concrete no-op.

**TODOs:**

- [datablock.py](src/easydiffraction/core/datablock.py#L39)

**Depends on:** related to issue 11.

**Recommended-priority note:** Part of the data `_update` refactor cluster (with #25 / #32): make `_update_categories` abstract. **Tier 4 (maintainability).**
