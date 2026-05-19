# ADR: Switchable Category API

## Status

Accepted.

## Date

2026-05-17

## Group

User-facing API.

## Context

Some categories have multiple concrete implementations that users can
switch at runtime, such as background, peak profile, and extinction.
Other categories are fixed by experiment type or have only one current
implementation.

## Decision

For multi-type switchable categories, expose the selector on the owner:

```python
experiment.background_type = 'chebyshev'
experiment.peak_profile_type = 'pseudo-voigt'
```

The category object itself remains a read-only property. Switching the
owner-level type replaces the underlying category object.

Expose `show_<category>_types()` on the owner so supported choices can
be filtered by the owner context.

Do not expose public `_type` selectors for fixed-at-creation categories
or single-implementation categories. Their factories and internal type
attributes may still exist for consistency.

## Consequences

Users can tell when a change replaces a whole category implementation.
The public API stays smaller for single-type categories while preserving
the internal factory pattern.
