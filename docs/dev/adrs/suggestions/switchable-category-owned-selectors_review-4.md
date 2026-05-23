# Review 4: Switchable Category Owned Selectors ADR

Reviewed ADR:
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)

Reviewed reply:
[`switchable-category-owned-selectors_reply-3.md`](switchable-category-owned-selectors_reply-3.md)

Previous review:
[`switchable-category-owned-selectors_review-3.md`](switchable-category-owned-selectors_review-3.md)

This review follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

No tests, lint, build, formatting, or verification commands were run.
This is a static re-review after Reply 3.

## Summary

Reply 3 resolves the three Review 3 findings: the peak CIF example now
uses the canonical tag, the renderer supported-type sketch is
implementable and includes `auto`, and the verbosity catalog row uses
the public `project.verbosity.fit` path.

The remaining findings are documentation consistency issues introduced
by the ADR's widened scope from instance-swap categories to all
selector-like `category.type` surfaces.

## Findings

### F1 - Context still claims `_background.type` already exists

The context says `_background.type` and `_peak.profile_type` "already
collapse the duplication" (`../accepted/switchable-category-owned-selectors.md:44`).
That is no longer consistent with the amended ADR or the current source.
The ADR's own CIF mapping table says background currently has no type
tag, only the `_pd_background.*` loop, and `_background.type` is the
replacement (`../accepted/switchable-category-owned-selectors.md:124`). The source
matches the table: background row descriptors use `_pd_background.*`
tags such as `_pd_background.id` and
`_pd_background.Chebyshev_order`
(`src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py:50`).

The context should be updated to say peak already has an in-category
identity tag, while background currently infers the active type from the
loop shape and gains `_background.type` through this ADR.

### F2 - Section 1 still describes only instance-swap behavior

Section 1 now conflicts with the widened scope. It says "Every
instance-swap switchable category" exposes `category.type` and that
setting it "triggers the parent to swap the underlying instance"
(`../accepted/switchable-category-owned-selectors.md:74`). Later sections make
Families B and C in scope too: backend selectors rebind live engines,
and fitting mode activates/deactivates sibling categories
(`../accepted/switchable-category-owned-selectors.md:495`).

If accepted as written, the headline contract would tell implementers
that `project.chart.type`, `project.table.type`,
`experiment.calculator.type`, and `analysis.fitting_mode.type` are
outside the primary contract or that they swap category instances. The
section should use the broader phrasing from §6, e.g. "Every in-scope
selector category exposes..." and "setting `category.type` delegates to
the owner hook, whose mechanism depends on the selector family."

### F3 - Family-B hook example still uses the pre-rename calculation name

The ADR renames `Calculation` to `Calculator`, moves
`experiment.calculation` to `experiment.calculator`, and says the
selector becomes `experiment.calculator.type`
(`../accepted/switchable-category-owned-selectors.md:631`). But the Family-B hook
example still names `Experiment._swap_calculation`
(`../accepted/switchable-category-owned-selectors.md:445`).

That should be `_swap_calculator` after the §8c rename; otherwise the
example contradicts the `_owner_attr_name` / `_swap_method_name`
convention and can lead the implementation plan to wire the old
category name back into the new API.

## Checks Skipped

Per reviewer instructions, no tests, lint, build, formatting, or `pixi`
commands were run. This review is limited to static reads of the ADR,
reply, and referenced source/documentation.
