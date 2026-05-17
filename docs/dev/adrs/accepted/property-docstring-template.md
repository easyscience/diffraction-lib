# ADR: Descriptor Property Docstring Template

## Status

Accepted.

## Date

2026-05-17

## Group

Documentation.

## Context

Public properties backed by `Parameter`, `NumericDescriptor`, or
`StringDescriptor` need consistent documentation and type hints.
Duplicating free-form text across docstrings and descriptor descriptions
creates drift.

## Decision

Use descriptor `description` fields as the source of truth for property
docstrings. Public properties follow the architecture template for:

- getter summary text
- writable versus read-only getter body
- getter return annotation
- setter value annotation

Setter docstrings are omitted because they are not rendered by the API
documentation pipeline.

## Consequences

Generated API documentation stays consistent with descriptor metadata.
The `param-consistency` tool can validate and repair property docstrings
mechanically.
