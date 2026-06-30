# 49. Automate Space Group CIF Name Variants

**Priority:** `[priority] low`

**Type:** Maintainability

`SpaceGroup.name_h_m` lists multiple CIF tag variants (with `.` and
`_`). A TODO asks to keep only the dotted version and automate variant
generation.

**TODOs:**

- [default.py](../../../../src/easydiffraction/datablocks/structure/categories/space_group/default.py#L52)

**Depends on:** nothing.
