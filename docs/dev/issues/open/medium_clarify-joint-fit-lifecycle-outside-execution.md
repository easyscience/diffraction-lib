# 121. Clarify `joint_fit` Lifecycle Outside Execution

**Priority:** `[priority] medium`

**Type:** Fragility

`joint_fit` is validated and auto-populated at `fit()` time, but it does
not react when experiments are later renamed or removed.

**Fix:** decide whether `joint_fit` should stay passive until execution,
or listen for experiment lifecycle changes and prune or warn earlier.

**Depends on:** nothing.
