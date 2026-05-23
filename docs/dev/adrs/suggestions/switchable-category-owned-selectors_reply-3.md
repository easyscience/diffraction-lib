# Reply to Review 3: Switchable Category Owned Selectors ADR

Reply to
[`switchable-category-owned-selectors_review-3.md`](switchable-category-owned-selectors_review-3.md)
for the ADR at
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

All three findings are accepted and applied. They are example-
correctness fixes with no architectural choice attached, so the user
elected to apply them in one pass.

## Findings

### F1 — Peak CIF example persisted an alias, not the canonical tag

**Verdict: agree.** The ADR text says CIF persists the canonical
peak-profile tag (see §4 → "Aliases" and the §3 mixin sketch), but
the Example block at the bottom of the ADR still showed
`_peak.type 'pseudo-voigt'`. `'pseudo-voigt'` is a context-local
alias, not a canonical factory tag. Canonical tags per
[`src/easydiffraction/datablocks/experiment/item/enums.py:159-165`](../../../src/easydiffraction/datablocks/experiment/item/enums.py)
include `cwl-pseudo-voigt`, `cwl-pseudo-voigt-empirical-asymmetry`,
`cwl-thompson-cox-hastings`, `tof-pseudo-voigt`, etc.

The Example experiment "hrpt" is constant-wavelength, so the
canonical tag is `cwl-pseudo-voigt`.

**Action.** Updated the Example CIF block:

```
_peak.type                cwl-pseudo-voigt
```

Added a sentence to the surrounding prose noting that CIF stores
the canonical tag while the writable Python setter
`experiment.peak.type` accepts the alias too and canonicalizes
before persisting. The Python surface block keeps
`peak.type = 'pseudo-voigt'` because that is exactly the alias-
accepting behaviour the ADR proposes.

### F2 — Renderer Shape 2 template was unimplementable and omitted `auto`

**Verdict: agree on both counts.**

[`src/easydiffraction/display/base.py:138-141`](../../../src/easydiffraction/display/base.py)
defines `descriptions()` as returning `list[tuple[str, str]]`, not a
mapping; my sketch called `.get(engine, '')` on it, which would
raise `AttributeError`. Separately,
[`src/easydiffraction/project/categories/rendering/default.py:23-24`](../../../src/easydiffraction/project/categories/rendering/default.py)
defines the supported set as `[AUTO_ENGINE, *engine_enum_values]`,
with `'auto'` as the default value. Omitting `'auto'` from
`_supported_types()` means `show_supported()` cannot mark the
current row when the chart/table type is at its default.

**Action.** Rewrote the Shape 2 template:

```python
class ChartBase(CategoryItem, SwitchableCategoryBase):
    _auto_description: ClassVar[str] = (
        'Pick a backend automatically based on environment'
    )

    def _supported_types(self, filters):
        # PlotterFactory.descriptions() returns list[tuple[str, str]]
        # already in (engine, description) shape.
        return [('auto', self._auto_description), *PlotterFactory.descriptions()]
```

Three concrete corrections compared to the prior sketch:

1. `descriptions()` is used as a list (its actual return type), not
   a dict. Its rows are spliced directly into the result.
2. The `'auto'` sentinel is prepended as a row so it can be marked
   with `'*'` when it is the active value (it is the default).
3. The auto-row description lives on a `ClassVar` so `TableBase`
   inherits the same string by re-using the pattern with its own
   factory.

### F3 — Family-D catalog cited a non-public verbosity path

**Verdict: agree.** Row 7 of the Family-D out-of-scope table read
`project.config.verbosity.fit`. The public path is
`project.verbosity.fit`;
[`src/easydiffraction/project/project.py:199,317`](../../../src/easydiffraction/project/project.py)
stores `_config` privately and exposes `verbosity` directly on the
`Project`. A catalog that implementers use as a repo-wide migration
reference should not introduce a non-existent public path.

**Action.** Updated Family-D row 7 Python path to
`project.verbosity.fit`. The CIF tag (`_verbosity.fit`) and source
anchor were already correct.

## Pattern note

All three findings are the same shape: example-correctness slips at
the boundary between what the ADR proposes and what the source
actually exposes. This is the third consecutive review to surface a
batch of these (Reply 1 fix-up caught invented `_peak.broadening_*`
tags and missing `Calculator` rename; Reply 2 addendum caught the
`background.create(Chebyshev_order=...)` CIF-vs-Python keyword
mix-up). Each ADR example must be grepped against the source before
being committed.

## Verification

This reply is a static one. No tests, lint, build, formatting, or
`pixi` commands were run, matching the reviewer's own constraint.
No markdown formatter was run on this reply or the ADR per the
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
review/reply formatting rule.

The implementing plan (separate file, drafted only after ADR
acceptance) will include the standard Phase-2 verification suite.

## Summary of files touched by this reply

- [`docs/dev/adrs/accepted/switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — three small example/template corrections per F1, F2, F3.
- [`docs/dev/adrs/suggestions/switchable-category-owned-selectors_reply-3.md`](switchable-category-owned-selectors_reply-3.md)
  — this file.
