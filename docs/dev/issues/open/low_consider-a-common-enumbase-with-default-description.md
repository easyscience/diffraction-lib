# 36. Consider a Common `EnumBase` with `default()` / `description()`

**Priority:** `[priority] low`

**Type:** Design

`BackgroundTypeEnum` and other enums repeat the same `default()` /
`description()` method pattern. A shared `EnumBase` would reduce
boilerplate.

**TODOs:**

- [enums.py](../../../../src/easydiffraction/datablocks/experiment/categories/background/enums.py#L10)

**Depends on:** related to issue 9.
