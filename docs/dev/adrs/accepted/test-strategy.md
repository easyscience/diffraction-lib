# ADR: Test Strategy

## Status

Accepted.

## Date

2026-05-17

## Group

Quality.

## Context

EasyDiffraction combines core model logic, factories, calculators,
display helpers, tutorials, notebooks, and filesystem persistence.
Regressions can appear at several levels.

## Decision

Use layered tests:

- unit tests for isolated classes and functions
- functional tests for multi-component workflows without heavy external
  dependencies
- integration tests for end-to-end behavior with real calculation
  engines and data
- script tests for tutorial `.py` files
- notebook tests for generated tutorials

The unit-test tree mirrors the source tree where practical. The
`test-structure-check` script tracks expected test locations and known
aliases.

## Consequences

New features should add focused tests at the lowest useful layer and
broader tests when behavior crosses module boundaries. The mirrored
structure makes missing coverage easier to spot.
