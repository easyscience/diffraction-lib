# EasyDiffraction — Closed Issues

Issues that have been fully resolved. Kept for historical reference.

---

## Dirty-Flag Guard Was Disabled

**Resolution:** added `_set_value_from_minimizer()` on `GenericDescriptorBase`
that writes `_value` directly (no validation) but sets the dirty flag on the
parent `DatablockItem`. Both `LmfitMinimizer` and `DfolsMinimizer` now use it.
The guard in `DatablockItem._update_categories()` is enabled and skips redundant
updates on the user-facing path (CIF export, plotting). During fitting the guard
is bypassed (`called_by_minimizer=True`) because experiment calculations depend
on structure parameters owned by a different `DatablockItem`.
