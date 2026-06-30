# 39. Improve `_update_priority` Handling in Categories

**Priority:** `[priority] low`

**Type:** Design

`CategoryItem` and `CategoryCollection` both define
`_update_priority = 10` with a TODO to set different defaults and use
them during CIF serialisation. The duplicated `_update` no-op methods
are also marked.

**TODOs:**

- [category.py](../../../../src/easydiffraction/core/category.py#L21)
- [category.py](../../../../src/easydiffraction/core/category.py#L23)
- [category.py](../../../../src/easydiffraction/core/category.py#L32)
- [category.py](../../../../src/easydiffraction/core/category.py#L174)
- [category.py](../../../../src/easydiffraction/core/category.py#L199)

**Depends on:** related to issues 10, 11.
