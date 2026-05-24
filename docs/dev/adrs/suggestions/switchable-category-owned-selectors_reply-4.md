# Reply to Review 4: Switchable Category Owned Selectors ADR

Reply to
[`switchable-category-owned-selectors_review-4.md`](switchable-category-owned-selectors_review-4.md)
for the ADR at
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

All three findings are accepted and applied. They are documentation-
consistency fixes introduced by the ADR's incremental widening from
instance-swap categories to the full A/B/C scope — no architectural
choice attached.

## Findings

### F1 — Context paragraph claimed `_background.type` already collapses the duplication

**Verdict: agree.** The original Context paragraph 2 said
`_background.type` and `_peak.profile_type` "already collapse the
duplication". That predates the widened-scope amendments and is
inconsistent with both the ADR's own §3 CIF mapping table (which says
background today has no identity tag, only `_pd_background.*` columns)
and the source
([`src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py:50,69,78`](../../../src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py)
confirms `_pd_background.*` tags only — no scalar identity).

**Action.** Rewrote paragraph 2. The new wording describes the actual
per-category state of CIF identity persistence today:

- `_peak.profile_type` is the in-category identity tag (peak does
  collapse the duplication).
- `_background.*` has **no** identity tag — the active type is inferred
  from which `_pd_background.*` loop columns are present.
- `_fitting.minimizer_type` lives in the owner-level `_fitting.*` block
  separately from the `_minimizer.*` block (full duplication).
- `_calculation.calculator_type` lives inside its category block but the
  descriptor name awkwardly repeats the noun (which §8c fixes by
  renaming the category itself to `Calculator` and the descriptor to
  `type`).

The paragraph now describes the same four-row diversity the rest of the
ADR amends, so the Context, §3 mapping, and §8 structural changes are
mutually consistent.

### F2 — Section 1 still described only instance-swap behavior

**Verdict: agree.** §1 headline read "Every instance-swap switchable
category exposes…" and "Setting `category.type = 'X'` triggers the
parent to swap the underlying instance". That predates the widened
scope. Per §6 and the catalog the in-scope set covers all three
mechanism families:

- Family A — swaps the category instance.
- Family B — swaps the live engine behind a singleton category.
- Family C — activates / deactivates sibling categories.

The headline contract should not single out Family A or commit to the
"instance swap" mechanism, because the same writable surface covers all
three.

**Action.** Rewrote §1 opening:

```
Every in-scope selector category — across all three mechanism
families recognised by selector-families.md (A switchable
categories, B backend selectors, C active-sibling selectors) —
exposes the same writable surface:

    category.type             # writable property (str)
    category.show_supported() # one method, current marked with '*'

That is the entire public selector surface. Nothing else. Setting
category.type = 'X' delegates to the owner's _swap_<name> hook;
what happens behind that hook depends on the family — the owner
replaces the category instance (Family A), rebinds the live
engine behind a singleton category (Family B), or activates /
deactivates sibling categories (Family C). The user-facing API
does not change with the mechanism. See §6 for the full scope
and the mechanism-vs-surface framing.
```

The rest of §1 (owner-level shims removed, owner still holds the slot,
swap initiated through back-reference) is unchanged.

### F3 — Family-B hook example still named `Experiment._swap_calculation`

**Verdict: agree.** The §4 prose listing the Family-B swap hooks still
said `Experiment._swap_calculation`. §8c renames the Python class
`Calculation` → `Calculator` and the owner-side attribute
`experiment.calculation` → `experiment.calculator`, so the swap hook is
named `Experiment._swap_calculator`.

**Action.** Updated the §4 prose example to read
`Experiment._swap_calculator`. The other two Family-B hooks in the same
list (`Project._swap_chart`, `Project._swap_table`) were already
correct.

Verified by greps that no other stale `_swap_calculation` or
`calculation._swap` strings remain in the ADR. The remaining
`calculation` references in the file are all describing the **today**
state being renamed (catalog "Today" columns, §8c rename rationale,
etc.), which is correct.

## Pattern note

Same shape as Reviews 2 and 3: documentation gradients where the
incremental amendments left earlier passages out of sync with the later
ones. Each Reply documents the specific re-grep that verified the fix
scope; the ADR's internal consistency now matches its widened scope
after four review passes.

## Verification

This reply is a static one. No tests, lint, build, formatting, or `pixi`
commands were run, matching the reviewer's own constraint. No markdown
formatter was run on this reply or the ADR per the
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
review/reply formatting rule.

The implementing plan (separate file, drafted only after ADR acceptance)
will include the standard Phase-2 verification suite.

## Summary of files touched by this reply

- [`docs/dev/adrs/accepted/switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — Context paragraph 2 rewritten (F1); §1 widened from instance- swap
  to all-three-families phrasing (F2); §4 Family-B hook example renamed
  `_swap_calculation` → `_swap_calculator` (F3).
- [`docs/dev/adrs/suggestions/switchable-category-owned-selectors_reply-4.md`](switchable-category-owned-selectors_reply-4.md)
  — this file.
