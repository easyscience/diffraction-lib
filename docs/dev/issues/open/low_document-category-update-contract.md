# 11. Document Category `_update` Contract

**Priority:** `[priority] low`

**Type:** Maintainability

`_update()` is an optional override with a no-op default. A clearer
contract would help contributors:

- **Active categories** (those that compute something, e.g.
  `Background`, `Data`) should have an explicit `_update()`
  implementation.
- **Passive categories** (those that only store parameters, e.g. `Cell`,
  `SpaceGroup`) keep the no-op default.

The distinction is already implicit in the code; making it explicit in
documentation (and possibly via a naming convention or flag) would
reduce confusion for new contributors.

**Depends on:** nothing.
