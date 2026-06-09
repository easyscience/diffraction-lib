# ADR: Lazy Pattern Recalculation

## Status

Proposed.

## Date

2026-06-09

## Group

Core model.

## Context

The calculated pattern of an experiment is exposed through the data
category as plain array properties — `intensity_calc`, `intensity_bkg`,
and the related totals — each built on access from the stored per-point
descriptors (for example `np.fromiter(p.intensity_calc.value for p in
_calc_items)`). Those stored values are only refreshed when something
calls `_update_categories()`: today that happens inside `fit()`, the new
`project.analysis.calculate()`, `as_cif`, and `display.pattern()`.

As a consequence, reading a computed array directly after changing a
model parameter returns **stale** values until the next explicit trigger:

```python
experiment.cell.length_a = 4.20      # model changed
y = experiment.data.intensity_calc   # still the OLD pattern
```

Normal user flows hide this because plotting and CIF export call
`_update_categories()` first, so they always render fresh data. The
stale read only surfaces when code bypasses those high-level operations
and reads the raw array — which is exactly the cross-engine verification
pattern, and the reason `project.analysis.calculate()` was introduced as
an explicit trigger.

A more convenient API would recompute automatically when the data is
read after a change, removing the need to remember an explicit call.

## Decision (proposed)

Introduce a per-experiment **dirty flag** for the calculated pattern:

- Any change to a parameter that affects the pattern — cell, atom sites,
  instrument, peak profile, linked-phase scale, calculator type,
  constraints, aliases — marks the owning experiment's pattern dirty.
- The **first** access to any computed array in the data category
  (`intensity_calc`, `intensity_bkg`, totals, …) while the experiment is
  dirty triggers a single full pattern recalculation, caches all computed
  arrays, and clears the dirty flag.
- **Subsequent** accesses to any computed array return the cached result
  with no recalculation, until the next parameter change re-marks the
  pattern dirty.

The compute-once-per-change rule is the core requirement: needing both
the calculated points and the background points (two array reads from the
same data category) must trigger **one** recalculation, not two — only
the first read after a change recomputes.

`project.analysis.calculate()` remains available as an explicit trigger
(and the explicit name documented in tutorials), but becomes optional:
reading a computed array is always fresh on its own.

## Consequences

- Reading a computed array always reflects the current model; no explicit
  `calculate()` call is required.
- Robust dirty propagation is mandatory and is the hard part: **every**
  pattern-affecting setter across structure, experiment, instrument,
  peak, linked phases, constraints, and aliases must flip the flag. A
  missed setter yields silently stale results — the worst failure mode in
  a refinement tool — while over-flagging recomputes too often.
- A property getter can now trigger an expensive diffraction calculation;
  the per-change caching above keeps repeated reads cheap, but the cache
  must stay coherent with the calculators' own internal caching.
- Structure changes are shared across experiments through linked phases,
  so a structure edit must mark every linked experiment dirty.

## Alternatives Considered

- **Explicit `project.analysis.calculate()` (current).** Simple,
  predictable, and consistent with `fit()`, but the user must remember to
  call it before reading the raw array. Kept regardless of this ADR.
- **Recompute on every array access (no caching).** Removes the dirty
  flag but recomputes redundantly when several arrays are read in
  sequence (calculated points then background) — too expensive.
- **Lazy recompute with per-change caching (this proposal).**

## Deferred Work / Open Questions

- Where the dirty flag lives and how setters reach it: a hook on the
  `Parameter`/descriptor base that notifies its owning experiment, versus
  category-level invalidation.
- Granularity: a single per-experiment pattern-dirty flag versus
  finer-grained invalidation (for example structure-factor vs profile
  terms).
- Interaction with constraints and aliases, which mutate parameters
  indirectly during `_update_categories()`.
- Coordination with the existing calculator-level caches so the two
  layers do not fight or double-cache.
