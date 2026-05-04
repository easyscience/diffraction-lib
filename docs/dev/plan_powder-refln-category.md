# Plan: Powder Refln Category

Add a powder Bragg `refln` category that records calculated reflection
metadata per linked phase. The category will be populated when powder
patterns are calculated and will provide the data source for hoverable
Bragg ticks in the existing three-panel powder plot.

- Plan file: `docs/dev/plan_powder-refln-category.md`
- Feature name: `powder-refln-category`
- Feature branch: `feature/powder-refln-category`

## Status

- [x] Record design decisions below.
- [x] Create and switch to branch `feature/powder-refln-category`.
- [x] Phase 1: implement code and documentation changes only.
- [x] Stop for user review after Phase 1 is complete.
- [x] Phase 2: add/update tests and run verification commands after user
      approval.
- [x] Final clean-up: update this plan, confirm commits, and summarize
      remaining risks.

## Execution Protocol

- Work independently through Phase 1 until all implementation checklist
  items are complete. Do not add tests or run tests during Phase 1
  unless the user explicitly asks.
- Mark each checklist item from `[ ]` to `[x]` when it is completed.
- Commit after every completed implementation step. Stage only the files
  modified for that step and avoid staging unrelated user changes.
- Do not push commits unless the user explicitly asks.
- Do not commit data files, project files, CIF files, or other generated
  artifacts created by integration tests, script tests, or notebook
  execution unless the user explicitly asks to update those artifacts.
- After Phase 1, stop and ask the user to review the implementation.
  Continue to Phase 2 only after user approval.

## Implementation Checklist

### Phase 1 — Implementation

- [x] Step 1: Create branch `feature/powder-refln-category` from the
      current working branch. Suggested commit: no commit; branch setup
      only.
- [x] Step 2: Add the powder `Refln` item and collection, including
      `phase_id`, `f_calc`, `f_squared_calc`, beam-mode x fields, array
      accessors, and `_replace_from_records(...)`. Suggested commit:
      `Add powder Refln category`
- [x] Step 3: Wire `experiment.refln` into `BraggPdExperiment` as a
      read-only sibling category and include it in CIF serialization.
      Suggested commit: `Wire powder Refln into Bragg experiments`
- [x] Step 4: Add calculator-side reflection record extraction for
      Cryspy, reusing values from the powder pattern calculation output
      when available. Suggested commit:
      `Extract Cryspy powder reflection records`
- [x] Step 5: Update `PdDataBase._update()` so every calculation clears
      and repopulates `experiment.refln` in sync with
      `data.intensity_calc`. Suggested commit:
      `Populate powder Refln during calculation`
- [x] Step 6: Update plotting to consume `experiment.refln`, group by
      `phase_id`, use the selected x-axis space, and show `phase_id`,
      `(index_h index_k index_l)`, `f_squared_calc`, and `f_calc` in
      Bragg tick hover content. Suggested commit:
      `Use powder Refln for Bragg ticks`
- [x] Step 7: Update documentation and any affected developer plans so
      they refer to `experiment.refln` and `phase_id`. Suggested commit:
      `Document powder Refln Bragg ticks`
- [x] Step 8: Review Phase 1 diffs, update this checklist, and stop for
      user review before adding tests or running verification. Suggested
      commit: `Update powder Refln implementation plan`

### Phase 2 — Verification

- [x] Step 9: Add/update focused unit tests for the powder `Refln` item,
      collection replacement, `BraggPdExperiment` wiring, Cryspy record
      extraction, data update population, plotting, and CIF round-trip.
      Suggested commit: `Test powder Refln category`
- [x] Step 10: Run targeted unit tests for the changed areas and fix any
      failures. Suggested commit: `Fix powder Refln test failures`
- [x] Step 11: Run project formatting, linting, unit tests, integration
      tests, and script tests listed below. Do not commit generated
      data, project, or CIF artifacts from those runs. Suggested commit:
      `Verify powder Refln implementation`
- [x] Step 12: Update this plan with completed verification results and
      any remaining risks. Suggested commit:
      `Finalize powder Refln plan`

## Clarification Questions

All known questions have been answered and recorded in
`Decisions Recorded`. If new ambiguity appears during implementation,
pause only when the ambiguity changes public API, scientific semantics,
data persistence, or removes/replaces existing behavior.

## Current Context

- Single-crystal reflection data lives in
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py`.
  Its `Refln` item owns `_refln.id`, `_refln.d_spacing`,
  `_refln.sin_theta_over_lambda`, Miller indices, measured/calculated
  intensity fields, and wavelength.
- Powder Bragg measured/calculated pattern points live in
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`.
  `PdDataBase._update()` loops over `experiment.linked_phases`, calls
  the active calculator once per linked phase, scales each phase
  pattern, and stores the summed pattern in `data.intensity_calc`.
- Powder experiments expose linked phases through `_pd_phase_block.id`
  in
  `src/easydiffraction/datablocks/experiment/categories/linked_phases/default.py`.
  The runtime identity used to find structures is
  `linked_phase._identity.category_entry_name`, which currently resolves
  to `linked_phase.id.value`.
- The three-panel plot plan in
  `docs/dev/plan-threePanelPowderPlot.prompt.md` already added a
  display-side Bragg tick DTO and a temporary extractor that looks for a
  future `experiment.bragg_peaks` category. This implementation should
  replace that future placeholder with the real `experiment.refln`
  category.

## Proposed Category Shape

Implement a powder-specific reflection item that inherits from the
single-crystal `Refln` item and adds the requested powder fields.

Recommended common item fields:

| Public property         | CIF name                       | Type    | Meaning                                                            |
| ----------------------- | ------------------------------ | ------- | ------------------------------------------------------------------ |
| `id`                    | `_refln.id`                    | string  | Stable row identifier, unique within the experiment.               |
| `phase_id`              | `_refln.phase_id`              | string  | Identifier of the linked phase that produced this reflection.      |
| `d_spacing`             | `_refln.d_spacing`             | numeric | Reflection d-spacing, used to derive plot x positions when needed. |
| `sin_theta_over_lambda` | `_refln.sin_theta_over_lambda` | numeric | Reflection sin(theta)/lambda value.                                |
| `index_h`               | `_refln.index_h`               | numeric | Miller h index.                                                    |
| `index_k`               | `_refln.index_k`               | numeric | Miller k index.                                                    |
| `index_l`               | `_refln.index_l`               | numeric | Miller l index.                                                    |
| `f_calc`                | `_refln.f_calc`                | numeric | Calculated structure-factor amplitude `\|F_calc\|`.                |
| `f_squared_calc`        | `_refln.f_squared_calc`        | numeric | Raw calculated structure-factor amplitude squared `\|F_calc\|^2`.  |

Recommended beam-mode-specific item fields should mirror the active
powder `data` category so Bragg ticks are always rendered in the same x
space as the main chart:

| Beam mode | Public property  | CIF name basis                           | Meaning                                                 |
| --------- | ---------------- | ---------------------------------------- | ------------------------------------------------------- |
| CWL       | `two_theta`      | same convention as `data.two_theta`      | Reflection position on the constant-wavelength 2θ axis. |
| TOF       | `time_of_flight` | same convention as `data.time_of_flight` | Reflection position on the time-of-flight axis.         |

Implementation notes:

- Add the item as `Refln` in a powder Bragg module and inherit from
  `easydiffraction.datablocks.experiment.categories.data.bragg_sc.Refln`.
  Alias the imported single-crystal class locally to avoid a name clash.
- Add `phase_id`, `f_calc`, and `f_squared_calc` descriptors in the
  subclass `__init__()` after `super().__init__()`.
- Although the public/CIF field is named `phase_id`, its value should be
  copied exactly from `linked_phase.id.value`.
- Add CWL and TOF powder `Refln` variants or mixins so `refln` stores
  the same native x-coordinate field as the active powder `data`
  category: `two_theta` for CWL and `time_of_flight` for TOF.
- Keep `self._identity.category_code = 'refln'` from the base class.
- Keep `f_calc` and `f_squared_calc` non-negative real numeric values.
  `f_calc` is `|F_calc|`; `f_squared_calc` is raw `|F_calc|^2` and must
  not include linked-phase scale or powder intensity factors.
- Add a collection class, for example `PowderReflnData`, with typed
  array properties for `phase_id`, `d_spacing`, `sin_theta_over_lambda`,
  `index_h`, `index_k`, `index_l`, `f_calc`, `f_squared_calc`, and the
  active beam-mode x coordinate.
- Add a private replacement method such as `_replace_from_records(...)`
  so calculators can atomically clear and repopulate all reflection rows
  after a successful pattern calculation.
- Use globally unique row ids, likely `1`, `2`, ... in calculation
  order, while preserving phase grouping with `phase_id`. Add a future
  note to reconsider phase-prefixed ids if CIF inspection or debugging
  needs it.

## Experiment Wiring

Add the category as an additional category on `BraggPdExperiment`, not
as a replacement for `experiment.data`.

Steps:

1. Instantiate the powder `refln` collection in
   `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` during
   `BraggPdExperiment.__init__()`.
2. Add a read-only `refln` property on `BraggPdExperiment`.
3. Set the collection update priority after powder `data` updates, for
   example `_update_priority = 110`, and keep its own `_update()` a
   no-op unless a later design moves calculation ownership into the
   category.
4. Let normal datablock category traversal serialize the new collection
   to CIF, since `experiment_to_cif()` already emits all category
   collections stored on the experiment.
5. Avoid adding `refln` to `PdExperimentBase` unless total-scattering
   powder experiments also need it later.

If strict factory-backed category construction is desired, add a small
`refln` category factory package and create the powder Bragg collection
through that factory. If the project prefers the smallest local change,
instantiate the collection directly from the powder Bragg experiment.

## Calculation Population

The existing powder calculation flow should remain the single source of
truth for both the calculated pattern and the reflection table.

Recommended implementation path:

1. Define a small internal reflection-record container for calculator
   output, containing `phase_id`, `d_spacing`, `sin_theta_over_lambda`,
   `index_h`, `index_k`, `index_l`, `f_calc`, `f_squared_calc`, and the
   active beam-mode x coordinate.
2. Extend the calculator abstraction with an explicit powder-reflection
   extraction path. Two possible designs are viable:
   - Return a typed result object from powder pattern calculation, such
     as `PowderPatternResult(intensity, reflections)`. This is the
     cleanest long-term API but touches every calculator implementation
     and every caller of `calculate_pattern()`.
   - Keep `calculate_pattern()` returning the pattern array and add an
     optional calculator method such as `last_powder_refln_records(...)`
     or `calculate_powder_refln(...)`. This keeps the first diff smaller
     but requires careful cache/lifecycle handling so reflection data
     comes from the same calculation state as the pattern.
3. Update `PdDataBase._update()` so it collects reflection records while
   looping over valid linked phases. After all phases are processed,
   call `experiment.refln._replace_from_records(records)` once.
4. If a linked phase is skipped because its structure id is missing, do
   not emit rows for that phase.
5. If the calculator cannot provide reflection metadata, clear
   `experiment.refln` and log a clear warning. Do not leave stale rows
   from a previous calculation.
6. Treat phase scale consistently. The plotted pattern should keep using
   `linked_phase.scale * structure_calc`; the `refln` structure-factor
   fields remain raw values from the calculator: `f_calc = |F_calc|` and
   `f_squared_calc = |F_calc|^2`.
7. Treat `refln` like the calculated columns in `data`: every powder
   calculation updates the category and clears stale rows rather than
   preserving previous calculation output.

Calculator-specific notes:

- Cryspy likely already computes `refln`-style arrays during powder
  pattern calculation. The implementation should extract h/k/l,
  d-spacing or sin(theta)/lambda, `f_calc`, and `f_squared_calc` from
  the same `dict_in_out` result used by `calculate_pattern()`. Start
  with Cryspy and reuse values from the pattern calculation rather than
  making explicit extra structure-factor calls if the required data are
  already returned.
- CrysFML currently returns only the calculated powder pattern through
  the EasyDiffraction wrapper. The implementation must either add a real
  reflection extraction path for CrysFML or explicitly warn and leave
  `refln` empty when CrysFML is active.
- The calculator base API and all concrete calculators must agree on the
  same record shape, even when a calculator returns no records.

## Plotting Integration

Replace the temporary display contract from `experiment.bragg_peaks` to
the real powder `experiment.refln` category.

Steps:

1. Update `Plotter._extract_bragg_tick_sets()` in
   `src/easydiffraction/display/plotting.py` to read from
   `experiment.refln`.
2. Group tick rows by raw `refln.phase_id` values and stringify only
   when constructing display labels. This preserves numeric ids and
   matches the earlier powder plot review fix.
3. Use Miller indices from `index_h`, `index_k`, and `index_l` for hover
   text.
4. Hover text must show `phase_id`, `(index_h index_k index_l)`,
   `f_squared_calc`, and `f_calc`.
5. Resolve tick x positions from the selected plot x axis:
   - `d_spacing`: use `refln.d_spacing` directly.
   - `two_theta`: use `refln.two_theta` for CWL experiments.
   - `time_of_flight`: use `refln.time_of_flight` for TOF experiments.
6. The Bragg tick row should always use the same coordinate space as the
   main chart. If the plot asks for a derived x axis, the tick extractor
   must select or derive the corresponding `refln` array before
   filtering.
7. Keep existing safeguards from the three-panel plot work: normalize
   `x_min`/`x_max`, return no tick sets for empty filtered main ranges,
   and tolerate an empty `refln` category without rendering stray rows.
8. Rename display DTO fields from `structure_id` to `phase_id` for this
   feature so the display layer matches the `refln` category. Add a note
   to reconsider `structure_id` later if the API needs to emphasize the
   structural datablock rather than the linked phase row.

## CIF And Documentation

1. Ensure `refln.as_cif` writes a loop containing the inherited
   `_refln.*` fields plus `_refln.phase_id`, `_refln.f_calc`, and
   `_refln.f_squared_calc`.
2. Ensure CIF loading can populate the new fields if a saved experiment
   contains them. If loaded rows are calculation outputs, they should be
   replaced on the next calculation rather than merged.
3. Add or update user-guide parameter documentation if generated docs do
   not pick up the new fields automatically.
4. Update the three-panel plot plan or display docs to say the Bragg
   ticks now consume `experiment.refln`, not a future `bragg_peaks`
   category.

## Tests

Phase 2 should add focused tests before running the full verification
commands.

Recommended unit tests:

1. `tests/unit/easydiffraction/datablocks/experiment/categories/data/test_bragg_pd.py`
   or a new mirrored `test_refln.py`: defaults for the powder `Refln`
   item, inherited field availability, new descriptor defaults, and
   category code `refln`.
2. Collection tests for `_replace_from_records(...)`, array properties,
   clearing stale rows, row id generation, and mixed `phase_id`
   grouping.
3. `BraggPdExperiment` tests proving `experiment.refln` exists, is
   read-only, serializes as `_refln`, and does not appear on total
   powder experiments unless explicitly chosen.
4. Calculator tests with fake calculators proving powder calculation
   populates `refln` for multiple linked phases and clears it when a
   calculator returns no records.
5. Cryspy adapter tests using small mocked `dict_in_out` payloads rather
   than real engine calculations.
6. Plotting tests updating fake `bragg_peaks` fixtures to fake `refln`
   fixtures, verifying grouping by `phase_id`, x filtering, hover
   fields, and empty-category behavior.
7. CWL/TOF coordinate tests proving Bragg ticks use the same x axis as
   the main chart for `two_theta`, `time_of_flight`, and `d_spacing`.
8. CIF round-trip tests for `_refln.phase_id`, `_refln.f_calc`, and
   `_refln.f_squared_calc`.

Suggested verification commands for Phase 2:

```bash
pixi run unit-tests tests/unit/easydiffraction/datablocks/experiment/categories/data/
pixi run unit-tests tests/unit/easydiffraction/datablocks/experiment/item/test_bragg_pd.py
pixi run unit-tests tests/unit/easydiffraction/display/
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

## Decisions Recorded

1. Use `_refln.phase_id` / `phase_id` for the phase-link field. Add a
   future note to consider switching to `structure_id` if that proves
   clearer for users or CIF interoperability.
2. Store `linked_phase.id.value` exactly in `phase_id`.
3. Store `f_calc` as the real non-negative amplitude `|F_calc|`.
4. Store `f_squared_calc` as raw `|F_calc|^2`, without linked-phase
   scale or powder intensity factors.
5. Bragg tick hover text must show `phase_id`,
   `(index_h index_k index_l)`, `f_squared_calc`, and `f_calc`.
6. Make `refln` beam-mode dependent like `data`: CWL rows store
   `two_theta`, TOF rows store `time_of_flight`, and all rows expose
   `d_spacing`. Bragg ticks must appear in the same x coordinate space
   as the main chart, including when the user plots with
   `x='d_spacing'`.
7. Start with Cryspy population. Reuse structure-factor values returned
   during the powder pattern calculation when Cryspy provides them;
   avoid explicit extra structure-factor calls unless inspection shows
   they are required.
8. Treat CIF-loaded `refln` rows as cached calculation output. Every
   calculation updates this category, similar to calculated columns in
   `data`.
9. Rename display internals from `structure_id` to `phase_id` for
   consistency with the category.
10. Use global sequential reflection row ids for now. Add a future note
    to reconsider phase-prefixed ids if debugging or CIF inspection
    would benefit.

## Phase 1 Outcome

- Completed implementation commits: `8a3c24d71`, `97e70268d`,
  `dfb380da9`, `d92dc6f90`, `b5d55e38a`.
- `experiment.refln` now exists on Bragg powder experiments, is updated
  together with `data.intensity_calc`, and drives Bragg tick extraction
  through `phase_id`, h/k/l, `f_squared_calc`, `f_calc`, and the active
  powder x coordinate.
- Cryspy populates reflection rows from the same powder-pattern
  calculation payload. Backends without reflection metadata currently
  clear `experiment.refln` and warn instead of leaving stale rows.

## Phase 2 Outcome

- Added focused tests for the powder `refln` item/collection,
  `BraggPdExperiment` wiring, Cryspy record extraction, plotting, and
  CIF round-trip.
- Targeted verification for the changed areas passed after fixing one
  directly coupled issue: the powder data update warning path now
  imports `log` before clearing `experiment.refln`.
- `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
  `pixi run integration-tests`, and `pixi run script-tests` completed
  successfully.
- `pixi run fix` also reformatted affected source files and regenerated
  package-structure documentation under `docs/architecture/`.
- No remaining implementation-specific risks are known beyond the
  unrelated tutorial worktree changes left untouched during this phase.

## Suggested Commit Message

```text
Finalize powder Refln plan
```
