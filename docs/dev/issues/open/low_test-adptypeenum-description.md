# 186. Test `AdpTypeEnum.description()`

**Priority:** `[priority] low`

**Type:** Testing

`AdpTypeEnum.description()`
(`src/easydiffraction/datablocks/structure/categories/atom_sites/enums.py:24`)
returns per-member human-readable text but is never exercised. The
enum's members and `.default()` are tested, but `description()` is not —
inconsistent with sibling enums (`SampleFormEnum`,
`PeakProfileTypeEnum`), which do test it.

**Fix:** add a parametrized test (in the `test_atom_sites.py` rollup, or
a dedicated enum test) iterating `AdpTypeEnum` members and asserting
`description()` returns a non-empty `str` for each.

**Depends on:** nothing.
