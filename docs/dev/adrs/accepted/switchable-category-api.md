# ADR: Switchable Category API

## Status

Accepted.

## Date

2026-05-17

## Group

User-facing API.

## Context

Some categories have multiple concrete implementations that users can
switch at runtime, such as background, peak profile, extinction, and the
analysis minimizer. Other categories are fixed by experiment type or
have only one current implementation.

## Decision

This ADR is amended by
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md).
The current public selector contract is:

- the owner exposes the category object only, for example
  `analysis.minimizer` or `experiment.background`
- the category exposes the writable `type` property
- the category exposes `show_supported()`, with the active row marked by
  `*`
- fixed-at-creation categories and single-implementation categories do
  not expose a public selector

The older owner-level surface below is historical context and is
superseded by that accepted ADR.

### Historical owner-level decision

For multi-type switchable categories, the original decision exposed the
selector on the owner:

```python
analysis.minimizer_type = 'bumps (dream)'
experiment.background_type = 'chebyshev'
experiment.peak_profile_type = 'pseudo-voigt'
```

The category object itself remained a read-only property. Switching the
owner-level type replaced the underlying category object.

The original design exposed `show_supported_<category>_types()` and
`show_current_<category>_type()` on the owner so supported choices could
be listed separately from the active choice.

Do not expose public `_type` selectors for fixed-at-creation categories
or single-implementation categories. Their factories and internal type
attributes may still exist for consistency.

## Consequences

Users can tell when a change replaces a whole category implementation.
The public API stays smaller for single-type categories while preserving
the internal factory pattern.
