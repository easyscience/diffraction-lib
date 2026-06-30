# 50. Clarify `Cell._update` Usage of `called_by_minimizer`

**Priority:** `[priority] low`

**Type:** Cleanup

`Cell._update` deletes `called_by_minimizer` with a `TODO: ???`.

**TODOs:**

- [default.py](../../../../src/easydiffraction/datablocks/structure/categories/cell/default.py#L146)

**Depends on:** related to issue 11.

**Audit note (2026-06-23):** `Cell._update` accepts
`called_by_minimizer`, immediately `del`s it (`default.py:176-192`,
docstring "Currently unused"), yet the flag is threaded through the
whole update chain (`bragg_pd.py:786`, `total_pd.py:261`). Resolve by
either implementing the intended fast-path (skip the symmetry recompute
during fitting) or dropping the dead parameter from the chain.
