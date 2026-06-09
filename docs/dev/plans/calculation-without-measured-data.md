# Plan: Calculation Without Measured Data

This plan follows [`AGENTS.md`](../../../AGENTS.md). No deliberate
exceptions to those instructions are taken. Where this plan touches
public API (`experiment.data_range`) and many files, it is the
"propose a plan and wait for approval" path required by
[`AGENTS.md`](../../../AGENTS.md) §Code Style.

## ADR

Implements [Calculation Without Measured
Data](../adrs/accepted/calculation-without-measured-data.md)
(promoted to `accepted/` in **P1.1** per
[`AGENTS.md`](../../../AGENTS.md) §Change Discipline, before the PR is
opened).

Related accepted ADRs this plan builds on:

- [Unified Pattern View](../adrs/accepted/pattern-display-unification.md)
  — `pattern()` renders whatever project state supports; this plan adds
  "calculated-only" as a supported state.
- [Switchable Category API](../adrs/accepted/switchable-category-api.md)
  — `data_range` is a fixed, single-type-per-experiment category, so it
  exposes **no** `type` selector.
- [Immutable Experiment Type](../adrs/accepted/immutable-experiment-type.md)
  — `data_range` mirrors how `instrument`/`data` are fixed by the
  experiment type at construction.
- [Guarded Public Properties](../adrs/accepted/guarded-public-properties.md)
  — the writable range attributes are guarded property setters.
- [IUCr CIF Tag Alignment](../adrs/accepted/iucr-cif-tag-alignment.md)
  and [Python and CIF Category
  Correspondence](../adrs/accepted/python-cif-category-correspondence.md)
  — CIF tag choices for the range.

## Branch and PR

- Branch: `calculation-without-measured-data` (flat slug off `develop`,
  no `feature/` prefix). Do not push until asked.
- PR targets `develop`, not `master`.

## Problem recap

`ExperimentFactory.from_scratch(...)` builds a documented "experiment
without measured data", but the calculation x-grid is sourced **only**
from measured points:

- `cryspy._cif_range_section` reads `experiment.data.x.min()/.max()`
  (`src/easydiffraction/analysis/calculators/cryspy.py:1134-1136`) →
  raises `ValueError: zero-size array to reduction operation minimum`
  on the empty array.
- `crysfml._update_experiment_dict_from_data` passes
  `experiment.data.x.tolist()` as the scan
  (`src/easydiffraction/analysis/calculators/crysfml.py:372-390`) → an
  empty scan.
- `data._update` builds `np.zeros_like(self.x)` over the measured grid
  (`.../categories/data/bragg_pd.py:468`).

So `project.display.pattern(expt_name=...)` fails for a never-measured
structure even though structure, instrument, peak, and background are
all present.

## Decisions already made (from the ADR)

1. **`data_range` category, type-determined, no `type` selector.** Flat
   sibling of `data`, per-type concrete classes via a factory, exposed
   uniformly as `experiment.data_range`. Mirrors the `instrument`
   category exactly (per-beam-mode classes, `@Factory.register`,
   `TypeInfo`/`Compatibility`).
2. **Stored truth = the natural input axis (writable):** CWL powder
   `two_theta_{min,max,inc}`; TOF powder `time_of_flight_{min,max,inc}`;
   single crystal `sin_theta_over_lambda_{min,max}` (no `inc`).
3. **sinθ/λ + d-spacing are derived shared views** (`sinθ/λ = 1/(2·d)`),
   plus `x_{min,max,step}` aliases onto the active axis. Recalibration
   keeps the stored axis window fixed and re-derives sinθ/λ.
4. **Writable, guarded by measurement.** Setter raises when a measured
   scan is present (range is then observed, not input); getter returns
   the measured-derived range in that case (subsuming
   `experiment.measured_range`) and the stored/default range otherwise.
5. **Defaults authored in d-spacing**, projected onto each axis through
   the instrument, so a `from_scratch` experiment is calculable with no
   manual setup and the TOF default stays well defined.
6. **No `simulate()` method.** The grid is serialisable model state.
   When no measured scan exists, the powder data grid is **generated
   from `data_range`** on the calculation/update pass, and calculators
   keep reading `experiment.data.x` unchanged (the data-points-define-
   the-grid invariant is preserved; calculators are intentionally not
   modified).
7. **Display extends the unified view:** drop the `measured_available`
   requirement from the `background` and `bragg` availability gates so a
   calculated-only powder shows its calculated curve + background +
   Bragg row. "No measurement" = **absent** intensities (no zero-filled
   phantom measured curve or residual).

## Scope decisions for this plan (see Open questions)

- **In scope, fully wired:** Bragg **powder** CWL and TOF — the original
  failure. Generated grid → calculate → display, end to end.
- **In scope, category + persistence only:** single-crystal `ScDataRange`
  (sinθ/λ bounds, CIF round-trip, `measured_range` subsumption). The
  **reflection-generation wiring** (cryspy `calc_hkl`) is **deferred**
  per the ADR's Deferred Work; until then a single-crystal
  calculate-without-measured-data attempt raises a clear, named
  "not yet supported" error rather than crashing.
- **Out of scope:** total scattering (`pdffit`, r-space PDF). The
  `total-pd` path keeps requiring measured data; a clear error is raised
  if a calculation is attempted without it. Recorded as deferred.

## Concrete files likely to change

New package `src/easydiffraction/datablocks/experiment/categories/data_range/`:

- `__init__.py` — explicit imports of all concrete classes (registration).
- `base.py` — `DataRangeBase(CategoryItem)`, `_category_code='data_range'`.
- `cwl.py` — `CwlPdDataRange` (`two_theta_{min,max,inc}`).
- `tof.py` — `TofPdDataRange` (`time_of_flight_{min,max,inc}`).
- `sc.py` — `ScDataRange` (`sin_theta_over_lambda_{min,max}`).
- `factory.py` — `DataRangeFactory(FactoryBase)` with `_default_rules`
  mapping `(beam_mode, sample_form)` → tag (both SC beam modes → the one
  `ScDataRange`).

Existing files:

- `src/easydiffraction/datablocks/experiment/item/base.py` — attach
  `_data_range` in `_attach_category_parents`; subsume `measured_range`
  via the `data_range` getter.
- `.../experiment/item/bragg_pd.py`, `.../item/total_pd.py`,
  `.../item/bragg_sc.py` — construct `_data_range` from the experiment
  type; expose `experiment.data_range`; add it to the `categories` list.
- `.../categories/data/bragg_pd.py` — generate the data-point grid from
  `data_range` when no measured scan exists, at the top of the calc
  pass (`_update` / `_phase_calculation_results`).
- `src/easydiffraction/analysis/calculators/cryspy.py`,
  `.../calculators/crysfml.py` — **expected unchanged** (they read the
  now-populated `experiment.data.x`); confirm and add the
  single-crystal/total "not yet supported" guards where the calc path
  has no grid source.
- `src/easydiffraction/project/display.py` — drop `measured_available`
  from `background_available` and `bragg_available` gates (~lines
  837-851); keep residual measured-gated.
- `src/easydiffraction/report/data_context.py:244` — keep
  `measured_range` working (now backed by the `data_range` getter).
- `docs/dev/adrs/suggestions/calculation-without-measured-data.md` →
  `docs/dev/adrs/accepted/...` (P1.1) and `docs/dev/adrs/index.md`.

## Implementation steps (Phase 1)

> **Commit discipline (required).** When an AI agent follows this plan,
> every completed Phase 1 step below must be staged with **explicit
> paths** and committed locally (per [`AGENTS.md`](../../../AGENTS.md)
> §Commits) **before** moving to the next step or to the Phase 1 review
> gate. Keep commits atomic and aligned 1:1 with these steps. Do not
> create or run tests in Phase 1 (tests are Phase 2). Do not stage
> unrelated dirty files.

- [x] **P1.1 — Promote the ADR to `accepted/`.**
  `git mv` the ADR from `suggestions/` to `accepted/`, set its
  `## Status` to `Accepted`, rewrite its internal `../accepted/…` links
  to same-directory links, add an "Experiment model / Accepted" row to
  `docs/dev/adrs/index.md` linking `accepted/…`, and fix any link that
  pointed at the old `suggestions/` path (`git grep -n
  calculation-without-measured-data`).
  Commit: `Promote calculation-without-measured-data ADR to accepted`

- [ ] **P1.2 — Add the `data_range` category package (no wiring).**
  Create `base.py`, `cwl.py`, `tof.py`, `sc.py`, `factory.py`, and
  `__init__.py` mirroring the `instrument` category: `DataRangeBase`
  with `_category_code='data_range'`; per-type classes with `TypeInfo`,
  `Compatibility`, `@DataRangeFactory.register`; numeric descriptors for
  the stored axis (`min`/`max`, plus `inc` for powder) with units,
  display handlers, validators, and CIF handlers (CWL reuses
  `_pd_meas.2theta_range_{min,max,inc}`; TOF/SC custom tags per the ADR
  CIF mapping). `__init__.py` imports every concrete class to trigger
  registration.
  Commit: `Add data_range category package`

- [ ] **P1.3 — Attach `data_range` to experiment items.**
  Construct `_data_range` from the experiment type in
  `PdExperimentBase`, `ScExperimentBase`, and the total/sc items
  (`DataRangeFactory.create(...)`); add `_data_range` to
  `_attach_category_parents`; add it to each item's `categories` list;
  expose the read-only `experiment.data_range` accessor. Update the
  category package `__init__.py` registration import site
  (`datablocks/experiment/categories/__init__.py` if it aggregates).
  Commit: `Expose data_range on experiment items`

- [ ] **P1.4 — Derived sinθ/λ and d-spacing views, axis aliases,
  defaults.** Add `sin_theta_over_lambda`, `d_spacing`, and
  `x_{min,max,step}` derived views on each `data_range` class
  (`sinθ/λ = 1/(2·d)`; CWL via `setup_wavelength`, TOF via
  `d_to_tof_*`). Author default ranges in d-spacing and project them
  onto each stored axis through the instrument so a `from_scratch`
  experiment has a usable default grid.
  Commit: `Add derived sinθ/λ and d-spacing views to data_range`

- [ ] **P1.5 — Measurement-guarded getter/setter; subsume
  `measured_range`.** Make the axis attributes guarded writable
  properties: the setter raises (clear, named error) when a measured
  scan is present; the getter returns the measured-derived range when
  measured data exists and the stored/default range otherwise. Route
  `experiment.measured_range` through this getter (keep the existing
  `report/data_context.py:244` consumer working). Loaders/restore seed
  values via a private `_set_`.
  Commit: `Guard data_range and subsume measured_range`

- [ ] **P1.6 — Generate the powder grid from `data_range`.**
  In the Bragg powder data collection
  (`categories/data/bragg_pd.py`), when `self._items` is empty and a
  `data_range` is available, build the data-point grid from the stored
  axis (`min`/`max`/`inc`) via the existing
  `_create_items_set_xcoord_and_id` path at the top of the calc pass
  (`_update` / `_phase_calculation_results`), so `self.x` is populated
  before `np.zeros_like(self.x)` and before the calculator runs.
  Calculated-only points have `intensity_meas` absent and
  `intensity_calc` filled.
  Commit: `Generate powder calculation grid from data_range`

- [ ] **P1.7 — Confirm calculators need no grid change; add guards.**
  Verify `cryspy._cif_range_section` and
  `crysfml._update_experiment_dict_from_data` work unchanged now that
  `experiment.data.x` is populated from the generated grid (the
  data-points-define-the-grid invariant holds). For the single-crystal
  and total-scattering calculate-without-measured-data paths (no grid
  source in this plan), add a clear, named "not yet supported without
  measured data" error instead of an empty-array/empty-scan crash.
  Commit: `Add calc-without-data guards for single crystal and total`

- [ ] **P1.8 — Relax display gates for calculated-only.**
  In `project/display.py`, drop the `measured_available` requirement
  from `background_available` and `bragg_available` so a calculated-only
  powder shows calculated curve + background + Bragg. Keep
  `residual_available` measured-gated. Ensure "no measurement" is
  represented as absent intensities (no phantom measured/residual
  drawn).
  Commit: `Show background and bragg for calculated-only patterns`

- [ ] **P1.9 — Docs touch-ups.** Update any developer docs that describe
  the experiment categories or the "experiment without measured data"
  state to mention `data_range` (no tutorial regeneration in Phase 1;
  tutorial/notebook updates, if any, are handled in Phase 2 with
  `pixi run notebook-prepare`). Update `docs/dev/issues/open.md` →
  `closed.md` if an existing issue tracks this.
  Commit: `Document data_range and calculated-only workflow`

- [ ] **P1.10 — Phase 1 review gate (no code).** Mark this step `[x]`
  and stop for the Phase 1 review.
  Commit: `Reach Phase 1 review gate`

## Open questions

1. **Single-crystal reflection generation scope.** This plan defers the
   cryspy `calc_hkl` wiring (per ADR Deferred Work) and raises a clear
   error for SC calculate-without-data. Confirm that deferral, or expand
   P1.7 to wire `calc_hkl` now.
2. **Total scattering.** This plan leaves `total-pd`/`pdffit` requiring
   measured data (clear error otherwise). Confirm total scattering stays
   out of scope.
3. **Default numeric ranges/steps per type** (P1.4). Proposed: author in
   d-spacing (e.g. a sensible d-min/d-max window) and project; exact
   numbers to be chosen during implementation. Confirm the d-spacing
   default approach and whether specific default numbers are required.
4. **CIF tags for TOF / sinθ/λ / d bounds** (P1.2). CWL reuses
   `_pd_meas.2theta_range_{min,max,inc}`; TOF/SC need custom tags. Final
   spellings to be fixed against IUCr alignment during P1.2 — flag if a
   specific convention is required.
5. **Grid-generation trigger location** (P1.6). Proposed at the top of
   the data collection's calc pass (`_update`). Confirm this over a
   property-getter side effect on `experiment.data.x`.

## Verification commands (Phase 2)

Run after Phase 1 is approved. Use the zsh-safe log-capture pattern
where saved output is needed:

```bash
pixi run fix
pixi run test-structure-check > /tmp/easydiffraction-structure.log 2>&1; structure_exit_code=$?; tail -n 100 /tmp/easydiffraction-structure.log; exit $structure_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

Phase 2 must also add mirrored unit tests for every new module
(`test_base.py`, `test_cwl.py`, `test_tof.py`, `test_sc.py`,
`test_factory.py` under
`tests/unit/easydiffraction/datablocks/experiment/categories/data_range/`)
and extend the existing calculator/data/display tests. `pixi run fix`
regenerates `docs/dev/package-structure/{full,short}.md` — do not edit
by hand.

## Status checklist

- [x] P1.1 Promote ADR to accepted
- [ ] P1.2 Add data_range category package
- [ ] P1.3 Attach data_range to experiment items
- [ ] P1.4 Derived sinθ/λ + d-spacing views and defaults
- [ ] P1.5 Guard data_range; subsume measured_range
- [ ] P1.6 Generate powder grid from data_range
- [ ] P1.7 Calculator guards (SC/total)
- [ ] P1.8 Relax display gates for calculated-only
- [ ] P1.9 Docs touch-ups
- [ ] P1.10 Phase 1 review gate
- [ ] Phase 2 verification (tests + `pixi run fix/check/*-tests`)

## Suggested Pull Request

**Title:** Calculate and plot a pattern without measured data

**Description:** You can now simulate a diffraction pattern straight
from a crystal structure and instrument settings — no measured data file
required. Set the calculation range (in 2θ for constant-wavelength or
time-of-flight for TOF instruments), or just accept the sensible
defaults, and EasyDiffraction will compute the pattern and show the
calculated curve together with its background and Bragg reflection
markers. This makes it easy to preview what a candidate structure should
look like, to teach, or to generate a synthetic pattern before any
measurement exists. Fitting still requires measured data, as before.
