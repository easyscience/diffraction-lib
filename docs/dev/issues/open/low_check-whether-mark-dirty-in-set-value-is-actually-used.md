# 41. Check Whether `_mark_dirty` in `_set_value` is Actually Used

**Priority:** `[priority] low`

**Type:** Cleanup

`GenericDescriptorBase._set_value` marks the parent datablock dirty with
a TODO questioning whether this path is exercised.

**TODOs:**

- [variable.py](../../../../src/easydiffraction/core/variable.py#L154)

**Depends on:** nothing.
