# ADR: Post-Calculation Corrections Package

## Status

Accepted.

## Date

2026-06-18.

## Group

Analysis and fitting.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It defines where
> calculator-independent corrections live, separate from the calculation
> backends. It does not change any public API or any correction's
> behaviour; it is a placement and naming decision.

## Context

`analysis/calculators/` holds the diffraction calculation backends —
`crysfml`, `cryspy`, `pdffit` — each a `CalculatorBase` subclass that
computes a pattern from a structure and experiment. Its own package
docstring describes it as the home of the calculation *backends*.

Two modules accumulated in that same package that are **not** backends:

- `absorption.py` — Debye–Scherrer `μR` intensity factor (issue 119).
- `polarization.py` — X-ray CW Lorentz–polarization factor.

Both *adjust an already-calculated pattern* rather than computing one.
Each exposes a module-level `apply(y, experiment) -> y` (plus internal
`factor(...)` helpers) and is called by `crysfml.py` and `cryspy.py`
**after** the backend returns its convolved profile, so the two backends
stay bit-for-bit consistent on the correction term. Neither is exported
from any `__init__.py`; they are imported by full module path.

Mixing post-calculation corrections into the backends package conflates
two roles (compute vs. adjust) and gives no obvious home for the further
point-wise corrections the
[in-house calculation engine ADR](../suggestions/in-house-calculation-engine.md)
anticipates (per-reflection `SyCos`/`SySin`, preferred orientation).

## Decision

1. **Move corrections to a sibling package `analysis/corrections/`.**
   `absorption.py` and `polarization.py` move out of
   `analysis/calculators/` into `analysis/corrections/`. `calculators/`
   stays purely about engines; `corrections/` holds adjustments applied
   on top of an engine's output. The unit tests mirror the move to
   `tests/unit/easydiffraction/analysis/corrections/`.

2. **Keep the informal `apply(y, experiment)` contract; no base class
   yet.** Each correction module exposes `apply(y, experiment) -> y`,
   returning `y` unchanged when the correction does not apply. Two plain
   functions sharing a signature do not justify a `CorrectionBase`
   abstraction; one is introduced only when a third correction shows a
   concrete shared need (per [`AGENTS.md`](../../../../AGENTS.md)
   §Architecture).

3. **No public-API or behaviour change.** The modules were never
   re-exported, so the move is import-path-only for the two backend
   consumers and the tests. Each correction's math is unchanged.

4. **Corrections stay backend-agnostic; they are not relocated into a
   future native engine.** External backends still need the point-wise
   forms, so `analysis/corrections/` is their permanent home. The native
   engine reimplements the *exact per-reflection* forms on its own code
   path rather than moving these modules (see the in-house engine ADR).

## Consequences

### Positive

- `calculators/` is unambiguously the engines package; `corrections/`
  names the post-calculation layer and gives future point-wise
  corrections an obvious, scalable home.
- The shared `apply(y, experiment)` contract is discoverable in one
  place.
- Contained change: no public API, no behaviour, no framework churn.

### Negative / cost

- A one-time import-path update for the two backends and the moved
  tests, plus refreshed path references in two existing ADRs.

## Alternatives Considered

| #   | Alternative                                              | Verdict                                                                                                                  |
| --- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| A   | **`analysis/corrections/` sibling package** (this ADR).  | **Chosen.** Clean split between compute and adjust; scalable home for the growing correction family.                    |
| B   | **Nested `analysis/calculators/corrections/`.**          | Rejected. Keeps corrections under the `calculators` name they do not belong to; the conceptual conflation remains.       |
| C   | **Keep them in `analysis/calculators/`.**                | Rejected. Mixes non-engine modules into the backends package; no home for further corrections.                          |
| D   | **Introduce a `CorrectionBase` class now.**              | Deferred. Premature abstraction for two plain `apply()` functions; revisit when a third correction lands.               |
