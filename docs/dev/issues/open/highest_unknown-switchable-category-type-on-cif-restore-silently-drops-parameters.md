# 139. Unknown Switchable-Category Type on CIF Restore Silently Drops Parameters

**Priority:** `[priority] highest`

**Type:** Robustness

On restore, `_restore_switchable_types` calls each swap hook with
`strict=False`; an unrecognized `_peak.type` / `_background.type` /
`_calculator.type` / `_extinction.type` (hand-edited or version-skewed
CIF) only logs a suppressible warning and leaves the **default**
implementation active. The subsequent `category.from_cif(block)` then
silently drops every parameter belonging to the intended implementation,
because those descriptors do not exist on the default — yielding a
quietly-wrong restored model. Persisted-state restore is a boundary
input per `AGENTS.md` and should fail loudly.

**Fix:** reject an unknown persisted type tag with a clear, non-
suppressible error during restore. This is exactly the contract the
Edifa persistence ADR's **Selector Validation Contract** proposes;
the current code is the concrete pre-ADR behaviour it would correct.

**TODOs / locations:**

- [base.py](src/easydiffraction/datablocks/experiment/item/base.py#L687)
  — `_replace_peak_profile` `strict=False` path
- [base.py](src/easydiffraction/datablocks/experiment/item/base.py#L350)
  — `_swap_calculator`
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L206)
  — background swap

**Depends on:** the Edifa persistence ADR
([`edstar-project-persistence.md`](../../adrs/accepted/edstar-project-persistence.md)),
which formalizes the reject-on-disagreement rule. Related to issues
120, 121.

**Recommended-priority note:** Promoted to **highest** by the 2026-06-13
audit: a confirmed robustness defect — an unknown persisted type
silently drops parameters on restore (silent wrong-science class).
