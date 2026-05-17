# ADR: Immutable Experiment Type

## Status

Accepted.

## Date

2026-05-17

## Group

Experiment model.

## Context

An experiment is defined by four orthogonal axes: sample form,
scattering type, beam mode, and radiation probe. Changing those axes
after creation can require replacing categories, calculators, data
collections, and validation rules.

## Decision

Experiment type is set at creation time and is immutable afterwards.

Factory and CIF-loading code may set the type through private
construction methods, but users cannot mutate the type axes on an
existing experiment.

## Consequences

The model avoids partial transformations between fundamentally different
experiment configurations. Runtime switching remains available for
category implementations, such as background or peak profile, where the
state replacement is bounded and explicit.
