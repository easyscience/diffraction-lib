# Plan: extract `refln` into a dedicated experiment category

## Problem

The `_refln` CIF category is currently split across two ownership
models:

- single-crystal Bragg experiments expose reflections through
  `experiment.data` via
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py`
- powder Bragg experiments expose measured pattern points through
  `experiment.data` and calculated reflections through
  `experiment.refln` via
  `src/easydiffraction/datablocks/experiment/categories/data/refln_pd.py`

This is inconsistent with the domain model and with the architecture
rule that categories are flat sibling children of the experiment. The
target state is:

- single-crystal Bragg experiments own **only** `refln`
- powder Bragg experiments own both `data` and `refln`
- all reflection implementations live under a dedicated
  `categories/refln/` package

## Assumptions

- This is a **hard API transition** for single-crystal Bragg
  experiments: callers move from `experiment.data` to
  `experiment.refln`. No compatibility alias is planned.
- Total-scattering powder experiments remain unchanged.
- The pending powder `refln` refresh fix should be folded into the move,
  so `refln` collection semantics are corrected in the new package
  rather than patched twice.

## Target architecture

1. Add a new
   `src/easydiffraction/datablocks/experiment/categories/refln/` package
   with explicit `__init__.py` imports and a `ReflnFactory`.
2. Move both current reflection implementations into that package:
   - single-crystal `Refln` / `ReflnData`
   - powder `PowderReflnBase`, `PowderCwlReflnData`,
     `PowderTofReflnData`, and related item classes
3. Make `refln` a first-class experiment sibling category:
   - `ScExperimentBase` owns `_refln`
   - `BraggPdExperiment` owns `_refln`
4. Keep `data` focused on measured point collections only:
   - powder Bragg and total scattering still use `data`
   - single-crystal Bragg no longer uses `DataFactory`
5. Generalize calculator-support discovery so it does not assume
   `experiment._data` always exists.

## Status checklist

- [x] Phase 1 — create `categories/refln/` package and factory
- [x] Phase 1 — move single-crystal reflection classes out of `data/`
- [x] Phase 1 — move powder reflection classes out of `data/`
- [x] Phase 1 — rewire experiment bases so SC owns `refln` and powder
      owns `data` + `refln`
- [x] Phase 1 — update calculator-support lookup, CIF loading, and
      runtime consumers to the new ownership model
- [x] Phase 1 — fold the powder `refln` refresh/index-parent fix into
      the migrated implementation
- [x] Phase 1 — update docs, tutorials, and code references from
      single-crystal `experiment.data` to `experiment.refln`
- [x] Phase 1 — stop for review before verification work
- [ ] Phase 2 — add/update tests for factories, experiment wiring, CIF
      round-trip, plotting, and migrated regressions
- [ ] Phase 2 — run `pixi run fix`
- [ ] Phase 2 — run `pixi run check`
- [ ] Phase 2 — run `pixi run unit-tests`
- [ ] Phase 2 — run `pixi run integration-tests`
- [ ] Phase 2 — run `pixi run script-tests`

## Phase 1 — Implementation

### 1. Create the dedicated `refln` category package

Create a new package under `categories/refln/` following the repo’s
factory-based category pattern. The package should include:

- `factory.py` with `ReflnFactory`
- `__init__.py` importing all concrete classes to trigger registration
- concrete modules for single-crystal and powder reflection collections
- shared base helpers only where reuse is real

The exact file split should mirror existing category packages rather
than leaving all implementations in one large module.

### 2. Move single-crystal reflections out of `data`

Extract `Refln` and `ReflnData` from `categories/data/bragg_sc.py` into
the new `categories/refln/` package. Preserve:

- CIF names (`_refln.*`)
- compatibility metadata
- calculator support metadata
- category identity (`category_code == 'refln'`)

After the move, `data/bragg_sc.py` should no longer define the
single-crystal reflection collection.

### 3. Move powder reflections out of `data`

Extract `refln_pd.py` into the new `categories/refln/` package and keep
the current powder-specific distinction between CWL and TOF reflection
collections. While touching this code, implement the already-identified
refresh fix so replacement:

- detaches old item parents
- attaches new item parents
- rebuilds the keyed collection index

### 4. Rewire experiment ownership

Update experiment bases so ownership matches the domain model:

- `ScExperimentBase` creates `_refln` via `ReflnFactory` and exposes a
  public read-only `refln` property
- `ScExperimentBase` stops creating `_data` for Bragg single-crystal
  experiments
- `BraggPdExperiment` creates `_refln` via `ReflnFactory` instead of
  importing powder reflection classes directly
- powder experiments keep their existing `data` ownership unchanged

### 5. Generalize calculator-support and runtime consumers

The current calculator-selection path reads support from `self._data`.
That must be generalized so single-crystal Bragg experiments still
resolve supported calculators after `data` is removed. Likely update
points:

- `ExperimentBase._supported_calculator_tags()`
- any helper that assumes every experiment has `.data`
- single-crystal ASCII loaders in `item/bragg_sc.py`
- plotting paths that currently use `experiment.data` for both powder
  and single crystal

The goal is to make single-crystal code read from `experiment.refln`
everywhere, while powder code keeps using `experiment.data` for pattern
arrays and `experiment.refln` for reflection metadata.

### 6. Sweep docs, tutorials, and imports

Update code, tests, and tutorial scripts so they reflect the new public
API and package locations. This includes:

- import paths moving from `categories.data.*` to `categories.refln.*`
- factory tests that currently expect `DataFactory` to own the
  single-crystal Bragg reflection collection
- single-crystal experiment tests and tutorials that refer to
  `experiment.data`
- any docs that describe experiment category ownership

At the end of Phase 1, stop for review before creating or updating
verification tests.

## Phase 2 — Verification

Add or update tests to cover the migration end-to-end:

- new `ReflnFactory` behavior and registrations
- single-crystal experiment wiring (`refln` present, `data` no longer
  used for Bragg SC)
- powder experiment wiring (`data` plus `refln`)
- CIF round-trip for both powder and single-crystal reflection
  categories
- plotting paths that now consume single-crystal `experiment.refln`
- migrated regression coverage for powder `refln` refresh semantics

Then run:

- `pixi run fix`
- `pixi run check`
- `pixi run unit-tests`
- `pixi run integration-tests`
- `pixi run script-tests`

## Likely files

- `src/easydiffraction/datablocks/experiment/categories/refln/__init__.py`
- `src/easydiffraction/datablocks/experiment/categories/refln/factory.py`
- `src/easydiffraction/datablocks/experiment/categories/refln/...`
- `src/easydiffraction/datablocks/experiment/categories/data/__init__.py`
- `src/easydiffraction/datablocks/experiment/categories/data/factory.py`
- `src/easydiffraction/datablocks/experiment/item/base.py`
- `src/easydiffraction/datablocks/experiment/item/bragg_pd.py`
- `src/easydiffraction/datablocks/experiment/item/bragg_sc.py`
- `src/easydiffraction/display/plotting.py`
- `tests/unit/easydiffraction/datablocks/experiment/categories/...`
- `tests/unit/easydiffraction/datablocks/experiment/item/...`
- `docs/docs/tutorials/ed-14.py`
- `docs/docs/tutorials/ed-15.py`

## Suggested branch

`feature/refln-category-extraction`
