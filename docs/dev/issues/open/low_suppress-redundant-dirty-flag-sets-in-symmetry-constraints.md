# 13. Suppress Redundant Dirty-Flag Sets in Symmetry Constraints

**Priority:** `[priority] low`

**Type:** Performance

Symmetry constraint application (cell metric, atomic coordinates, ADPs)
goes through the public `value` setter for each parameter, setting the
dirty flag repeatedly during what is logically a single batch operation.

No correctness issue — the dirty-flag guard handles this correctly. The
redundant sets are a minor inefficiency that only matters if profiling
shows it is a bottleneck.

**Fix:** introduce a private `_set_value_no_notify()` method on
`GenericDescriptorBase` for internal batch operations, or a context
manager / flag on the owning datablock to suppress notifications during
a batch.

**Depends on:** nothing, but low priority.
