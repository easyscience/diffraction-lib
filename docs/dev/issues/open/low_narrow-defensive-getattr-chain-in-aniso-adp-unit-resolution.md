# 159. Narrow Defensive getattr-Chain in Aniso ADP Unit Resolution

**Priority:** `[priority] low`

**Type:** Maintainability

`_owning_adp_type` walks
`param → aniso item → collection → structure → atom_sites → atom.adp_type`
entirely through `getattr(..., None)` plus a `try/except`, which is the
kind of defensive padding for internal states `AGENTS.md` discourages.
The docstring justifies it as a display path that can resolve before
wiring completes, so it is borderline-acceptable, but the broad tolerance
could mask a genuine wiring bug (silently returning declared units).

**Fix:** assert the chain in non-display contexts, or narrow the
tolerated cases.

**TODOs / locations:**

- [default.py](src/easydiffraction/datablocks/structure/categories/atom_site_aniso/default.py#L62)

**Depends on:** nothing.
