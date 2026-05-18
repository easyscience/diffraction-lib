# ADR: Enum-Backed Closed Value Sets

## Status

Accepted.

## Date

2026-05-17

## Group

Core model.

## Context

Many attributes accept a finite set of values: experiment axes, factory
tags, fit modes, calculators, minimizers, and rendering engines.
String-only dispatch is hard to grep and easy to mistype.

## Decision

Represent every finite closed set with a `(str, Enum)` class.

Use enum members as the internal source of truth for validation,
dispatch, default rules, and descriptions. User-facing setters may
accept either enum members or their string values, but internal code
compares against enum members.

## Consequences

Finite choices are discoverable, type-checkable, and greppable.
Validation can use enum membership instead of hand-written string
patterns.
