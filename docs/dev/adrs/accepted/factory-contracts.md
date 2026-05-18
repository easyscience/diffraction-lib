# ADR: Factory Contracts and Metadata

## Status

Accepted.

## Date

2026-05-17

## Group

Factories.

## Context

Many domain categories have multiple implementations, and some currently
have only one implementation but may gain more later. Construction,
default selection, compatibility filtering, and supported-option display
need a common contract.

## Decision

Every category that can be constructed by framework code is created
through a factory, even when it currently has only one implementation.

Concrete factory-created classes carry metadata appropriate to their
role:

- `type_info` for stable tag lookup and user descriptions.
- `compatibility` for experiment-axis compatibility where relevant.
- `calculator_support` for calculation-engine support where relevant.

Child rows that only exist inside a collection do not carry factory
metadata; the collection carries the metadata.

Factory registration is triggered by explicit imports in package
`__init__.py` files.

## Consequences

Construction, default resolution, support tables, and compatibility
filtering stay uniform. Single-implementation categories are ready for
future alternatives without changing the public construction pattern.
