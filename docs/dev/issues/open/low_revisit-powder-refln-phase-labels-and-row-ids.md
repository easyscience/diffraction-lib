# 94. Revisit Powder `refln` Phase Labels and Row IDs

**Priority:** `[priority] low`

**Type:** Naming / CIF UX

The implemented powder reflection category uses `phase_id` throughout
(`experiment.refln`, `PowderReflnRecord`, Bragg tick labels) and assigns
global sequential row ids. This matches the current implementation, but
the archived planning notes left two follow-up questions open:

1. whether `structure_id` would be clearer than `phase_id` in the public
   API / CIF output, and
2. whether phase-prefixed row ids would make CIF inspection and
   debugging easier than simple `1`, `2`, `3`, ...

**TODOs** (paths updated — reflection categories moved from
`categories/data/refln_pd.py` to `categories/refln/`):

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/refln/bragg_pd.py)
- [base.py](src/easydiffraction/display/plotters/base.py#L24)

**Note:** the EasyDiff persistence ADR proposes renaming powder
`refln.phase_id` → `structure_id`
([`edstar-project-persistence.md`](../adrs/suggestions/edstar-project-persistence.md)),
which resolves follow-up question 1; keep this issue scoped to the
row-id question (2) once that ADR lands.

**Depends on:** nothing.
