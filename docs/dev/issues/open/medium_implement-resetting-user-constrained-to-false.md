# 40. Implement Resetting `.user_constrained` to `False`

**Priority:** `[priority] medium`

**Type:** Correctness

`ConstraintsHandler` has a TODO to implement changing the
`.user_constrained` attribute back to `False` when constraints are
removed.

**Concrete consequence (raises this above cosmetic):** because
`_user_constrained` is never reset on constraint/alias removal, a
parameter that was once user-constrained stays excluded from
`fittable_parameters` (`datablock.py` `fittable_parameters` filter) for
the rest of the session even after the alias/constraint is deleted — so a
parameter the user expects to refine again is silently held fixed. This
is a persisted/live-state correctness gap, not just a missing feature.

**TODOs:**

- [singleton.py](src/easydiffraction/core/singleton.py#L37)

**Depends on:** nothing.
