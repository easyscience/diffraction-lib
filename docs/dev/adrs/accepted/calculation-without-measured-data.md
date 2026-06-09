# ADR: Calculation Without Measured Data

## Status

Accepted.

## Date

2026-06-06

## Group

Experiment model.

## Context

An experiment built with `ExperimentFactory.from_scratch(...)` has no
data points. The x-grid that every calculation runs on — the set of 2θ
or time-of-flight values — lives inside `experiment.data` and is only
ever populated by loading measured data
(`_create_items_set_xcoord_and_id`). With no grid, a calculation cannot
run:

- cryspy derives its scan range from `experiment.data.x.min()/max()`
  (`_cif_range_section`), which raises
  `ValueError: zero-size array to reduction operation minimum` on the
  empty array.
- crysfml passes `experiment.data.x.tolist()` as the scan, i.e. an empty
  scan.

So `project.display.pattern(expt_name=...)` fails for a structure that
has never been measured, even though everything needed to _calculate_ a
pattern (structure, instrument, peak shape, background) is present.

Scientists routinely want to **simulate** a pattern — or, for a single
crystal, per-reflection F² — from a structural model alone: choose a
range, calculate, and view the calculated curve with its background and
Bragg reflections, with no measurement to load or invent. This is also
how a saved project with no measured block should restore from the CLI.

Two existing decisions frame the solution:

- [Unified Pattern View](pattern-display-unification.md)
  already establishes that `pattern()` renders whatever the project
  state supports. "Only calculated data is available" should simply be
  one more supported state; today the display gates instead require
  measured data before background or Bragg can appear.
- The IUCr powder and core dictionaries already model an evenly-spaced
  scan **by range**: `_pd_meas.2theta_range_{min,max,inc}` and
  `_pd_proc.2theta_range_{min,max,inc}` are defined to be used "in place
  of the `2theta_scan` values" for constant-step data, and
  `_refln.sin_theta_over_lambda` / `_refln.d_spacing` are
  instrument-independent reciprocal coordinates shared by powder and
  single-crystal data.

## Decision

Introduce a `data_range` category that defines the reciprocal-space
region (and, for powder, the profile step) to calculate over, and let
the calculation and display paths fall back to it whenever no measured
scan exists.

1. **New category, type-determined.** `data_range` is a flat sibling of
   `data`, with per-type concrete classes created through a factory
   (`CwlDataRange`, `TofDataRange`, `ScDataRange`) and exposed uniformly
   as `experiment.data_range`. It is fixed by the experiment type, so it
   has **no** `type` selector — the same treatment
   [Switchable Category API](switchable-category-api.md)
   prescribes for fixed, single-type categories, and the same pattern
   `instrument` already uses for its per-beam-mode classes
   ([Immutable Experiment Type](immutable-experiment-type.md)).

2. **Stored truth is the natural input axis (writable).** The values a
   user sets and that serialise to CIF are the experiment's own axis:
   - CWL powder: `two_theta_{min,max,inc}`
   - TOF powder: `time_of_flight_{min,max,inc}`
   - Single crystal: `sin_theta_over_lambda_{min,max}` (no `inc`)

3. **sinθ/λ is the derived shared currency.** Every type also exposes
   `sin_theta_over_lambda` and `d_spacing` (related by
   `sinθ/λ = 1/(2·d)`, instrument-free), plus `x_{min,max,step}` aliases
   onto the active axis (mirroring the existing plotting x-array alias).
   Generic code — plotting and reflection generation — reads sinθ/λ. For
   CWL and TOF the sinθ/λ and d views derive from the stored axis
   through the instrument (λ for 2θ, DIFC/DIFA for TOF), so
   **recalibration keeps the stored axis window fixed and re-derives
   sinθ/λ**. For single crystal there is no measurement axis, so sinθ/λ
   is itself the stored truth.

4. **Bounds bound generation; step is powder-only.** `min`/`max` (as
   sinθ/λ) bound reflection generation — powder through the engine's
   2θ/TOF range, single crystal through cryspy
   `Crystal.calc_hkl(sthovl_max)`, which enumerates hkl with the space
   group's systematic absences applied. `inc` is the profile point
   spacing on the measurement axis and exists only for powder; a single
   crystal has bounds but no step.

5. **Writable, guarded by measurement.** Following
   [Guarded Public Properties](guarded-public-properties.md),
   the `data_range` axis attributes are writable public properties. The
   setter raises when a measured scan is present, because then the range
   is an _observed_ property of the data rather than an input; the
   getter returns the measured-derived range in that case (subsuming
   today's `experiment.measured_range`) and the stored or default range
   otherwise. Loaders and project restore seed values through a private
   `_set_`.

6. **Defaults authored in d-spacing.** Default ranges are stored in
   d-spacing and projected onto each axis through the instrument, so a
   `from_scratch` experiment is calculable with no manual setup and the
   TOF default — meaningless in absolute µs without calibration — stays
   well defined.

7. **No `simulate()` method.** Accessing or plotting `data` (powder) or
   `refln` (single crystal) with no measured scan builds the grid or
   reflection list from `data_range` and calculates on it. The grid is
   model state, not a one-shot action, so it is expressed as a
   serialisable category rather than a method call.

8. **Display extends the unified view.** Building on
   [Unified Pattern View](pattern-display-unification.md),
   `background` and `bragg` become available with calculated-only data —
   the measured-data requirement in their availability gates is dropped.
   "No measurement" is represented as _absent_ intensities (not a
   zero-filled array), so no phantom measured curve or residual is
   drawn. A calc-only powder view is the calculated curve plus
   background on the main panel and a Bragg row; a calc-only
   single-crystal view shows per-reflection calculated intensities.

9. **CIF mapping.** CWL bounds reuse the standard
   `_pd_meas.2theta_range_{min,max,inc}`. TOF, single-crystal, and the
   sinθ/λ–d bounds have no standard range tag, so custom tags are chosen
   in line with
   [IUCr CIF Tag Alignment](iucr-cif-tag-alignment.md) and
   [Python and CIF Category Correspondence](python-cif-category-correspondence.md).

## Consequences

- A structure-only experiment can be calculated and plotted with no data
  loaded: set `data_range` (or accept the defaults), then call
  `project.display.pattern(...)`. The original failure is resolved.
- One uniform `experiment.data_range` spans all experiment types;
  generic display and calculator code read the shared sinθ/λ view and
  need not branch on beam mode.
- `experiment.measured_range` is subsumed by the derived getter on
  `data_range`.
- The project is in beta, so this adds the category with no
  compatibility shim; tutorials and tests adopt it directly.
- New code spans a `data_range` category, factory, and per-type classes;
  calc-on-access grid and reflection generation; single-crystal hkl
  generation via `calc_hkl`; and the display-gate relaxation plus a
  calc-only single-crystal view.

## Alternatives Considered

- **A single generic `data_range.min/max/inc`.** Rejected: a bare `min`
  is not self-explaining, because even for CWL a range may be thought of
  in 2θ, d-spacing, or sinθ/λ. Axis-named attributes that cross-convert
  read better and still expose the shared sinθ/λ view for generic code.
- **A custom `pd_calc.2theta_range_*`.** Rejected: `pd_calc` has no
  range in the dictionary (it is intensities, and reuses the meas/proc
  point grid), so a custom calc range would lose interoperability with
  no clear benefit over the standard `pd_meas` range plus the universal
  `refln` reciprocal coordinates.
- **An input/output split** — a writable "requested range" input plus a
  read-only derived output — mirroring
  [Minimizer Input/Output Split](minimizer-input-output-split.md).
  Rejected as heavier than needed here; a single guarded writable
  property covers both roles.
- **A `simulate(x_min, x_max, x_step)` method.** Rejected: the range is
  persistent, restorable model state, which a method call is not.
- **A range read directly by the calculators, with no data points.**
  Rejected: it is more invasive (both engines plus plotting) and breaks
  the invariant that the data points define the grid.

## Deferred Work

- Single-crystal reflection-generation wiring (the cryspy `calc_hkl`
  path and validation of absence handling); crysfml single-crystal
  structure-factor support is expected soon and adopts the same path.
- Final custom CIF tag names for the TOF, sinθ/λ, and d-spacing bounds.
- Concrete default numeric ranges and steps per experiment type.
- The calc-only single-crystal plot specifics.
