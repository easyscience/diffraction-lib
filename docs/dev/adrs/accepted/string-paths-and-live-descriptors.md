# ADR: String Paths and Live Descriptors

## Status

Accepted.

## Date

2026-05-17

## Group

User-facing API.

## Context

Some APIs refer to persisted CIF-style fields, while other APIs refer to
one concrete live model parameter. Accepting both forms everywhere would
make call sites ambiguous and harder to validate.

## Decision

Use CIF-style string paths for setup-time, schema-level, and
cross-experiment selectors:

```python
sequential_fit_extract.create(target='diffrn.ambient_temperature')
project.display.fit.series(
    param=structure.cell.length_a,
    versus='diffrn.ambient_temperature',
)
```

Use live descriptor or parameter objects when the call targets one exact
model quantity and needs its `unique_name`, description, units, or
runtime value.

Do not add new APIs that accept both a string path and a live descriptor
unless a later ADR defines a stronger reason.

## Consequences

Persisted fields and live model parameters stay distinct. APIs that
operate across experiments can round-trip through CIF paths, while APIs
that operate on one fitted parameter keep direct object references.
