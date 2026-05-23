# ADR: Selector Families

## Status

Accepted.

## Date

2026-05-17

## Group

User-facing API.

## Context

Several public names use a selector-like shape, but they do not all mean
the same thing. Treating every `<name>_type` as a switchable category
would blur distinct concepts.

## Decision

Recognize three selector families:

| Family                       | User intent                     | Examples                                                                          |
| ---------------------------- | ------------------------------- | --------------------------------------------------------------------------------- |
| Backend selector             | Pick an execution backend       | `calculation.calculator_type`, `rendering.chart_engine`                           |
| Switchable-category selector | Swap a category implementation  | `analysis.minimizer_type`, `experiment.background_type`, `experiment.peak_profile_type` |
| Active-sibling selector      | Pick the active sibling surface | `analysis.fitting_mode_type`                                                      |

Backend selectors live on dedicated configuration categories.
Switchable-category selectors live on the host because they replace a
category instance. Active-sibling selectors live on the owner and decide
which sibling categories are visible, authoritative, and serialized.

## Consequences

Selector names stay familiar without forcing one implementation pattern
onto different concepts. Future selectors should declare which family
they belong to before adding API.
