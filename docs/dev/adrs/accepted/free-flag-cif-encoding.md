# ADR: Free-Flag CIF Encoding

## Status

Accepted.

## Date

2026-05-17

## Group

Persistence.

## Context

Fitting needs to persist whether a parameter is fixed or free. A
separate free-parameter list would duplicate state already attached to
individual parameter values and could become stale.

## Decision

Encode a parameter's free/fixed status in the CIF value uncertainty
syntax:

```text
3.89     fixed
3.89(2)  free with estimated standard deviation
3.89()   free without estimated standard deviation
```

Do not persist a separate list of free parameters as the source of
truth.

## Consequences

Each parameter carries its own fit-state information in the same place
as the value. CIF round-trips are simpler because there is no separate
state table to reconcile.
