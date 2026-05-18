# ADR: Guarded Public Properties

## Status

Accepted.

## Date

2026-05-17

## Group

Core model.

## Context

Most EasyDiffraction domain objects inherit from `GuardedBase`.
Descriptors and parameters are stored privately and exposed through
public properties. The public API needs a clear rule for whether a user
can assign to an attribute, and internal construction code still needs a
way to populate read-only values.

## Decision

Treat the presence of a property setter as the public writability
contract.

- Public properties with setters are user-editable.
- Public properties without setters are read-only.
- Internal mutation of read-only properties uses explicit private
  methods such as `_set_sample_form`.
- Unknown public attributes are rejected by `GuardedBase.__setattr__`
  with diagnostics.

Do not add a public setter only for internal use, because that makes the
attribute user-writable.

## Consequences

The public API stays predictable: reading a property returns the live
descriptor or parameter object, and assigning to the property is allowed
only when the class explicitly declares that assignment as part of the
API. Internal loaders and factories remain greppable because private
mutator methods are named directly.
