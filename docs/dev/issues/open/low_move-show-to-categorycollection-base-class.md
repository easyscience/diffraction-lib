# 53. Move `show()` to `CategoryCollection` Base Class

**Priority:** `[priority] low`

**Type:** Maintainability

`ExcludedRegions.show()` and `BackgroundBase.show()` duplicate table-
rendering logic. The TODO suggests moving it to the base class.

**TODOs:**

- [default.py](../../../../src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L166)
- [base.py](../../../../src/easydiffraction/datablocks/experiment/categories/background/base.py#L19)

**Depends on:** nothing.
