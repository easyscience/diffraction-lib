# Plan: Powder Refln Category

Add a powder Bragg `refln` category that records calculated reflection
metadata per linked phase. The category will be populated when powder
patterns are calculated and will provide the data source for hoverable
Bragg ticks in the existing three-panel powder plot.

## Status

- [ ] Confirm open questions below.
- [ ] Phase 1: implement code and documentation changes only.
- [ ] Phase 2: add/update tests and run verification commands.

## Current Context

- Single-crystal reflection data lives in
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py`.
  Its `Refln` item owns `_refln.id`, `_refln.d_spacing`,
  `_refln.sin_theta_over_lambda`, Miller indices, measured/calculated
  intensity fields, and wavelength.
- Powder Bragg measured/calculated pattern points live in
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`.
  `PdDataBase._update()` loops over `experiment.linked_phases`, calls the
  active calculator once per linked phase, scales each phase pattern, and
  stores the summed pattern in `data.intensity_calc`.
- Powder experiments expose linked phases through `_pd_phase_block.id` in
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

Recommended item fields:

| Public property | CIF name | Type | Meaning |
| --- | --- | --- | --- |
| `id` | `_refln.id` | string | Stable row identifier, unique within the experiment. |
| `linked_phase_id` | `_refln.linked_phase_id` | string | Identifier of the linked phase that produced this reflection. |
| `d_spacing` | `_refln.d_spacing` | numeric | Reflection d-spacing, used to derive plot x positions when needed. |
| `sin_theta_over_lambda` | `_refln.sin_theta_over_lambda` | numeric | Reflection sin(theta)/lambda value. |
| `index_h` | `_refln.index_h` | numeric | Miller h index. |
| `index_k` | `_refln.index_k` | numeric | Miller k index. |
| `index_l` | `_refln.index_l` | numeric | Miller l index. |
| `f_calc` | `_refln.f_calc` | numeric | Calculated structure-factor amplitude. |
| `f_squared_calc` | `_refln.f_squared_calc` | numeric | Calculated structure-factor amplitude squared. |

Implementation notes:

- Add the item as `Refln` in a powder Bragg module and inherit from
  `easydiffraction.datablocks.experiment.categories.data.bragg_sc.Refln`.
  Alias the imported single-crystal class locally to avoid a name clash.
- Add `linked_phase_id`, `f_calc`, and `f_squared_calc` descriptors in
  the subclass `__init__()` after `super().__init__()`.
- Keep `self._identity.category_code = 'refln'` from the base class.
- Keep `f_calc` and `f_squared_calc` non-negative unless the answer to
  the open questions requires complex structure factors.
- Add a collection class, for example `PowderReflnData`, with typed array
  properties for `linked_phase_id`, `d_spacing`, `sin_theta_over_lambda`,
  `index_h`, `index_k`, `index_l`, `f_calc`, and `f_squared_calc`.
- Add a private replacement method such as `_replace_from_records(...)`
  so calculators can atomically clear and repopulate all reflection rows
  after a successful pattern calculation.
- Use globally unique row ids, likely `1`, `2`, ... in calculation order,
  while preserving phase grouping with `linked_phase_id`.

## Experiment Wiring

Add the category as an additional category on `BraggPdExperiment`, not as
a replacement for `experiment.data`.

Steps:

1. Instantiate the powder `refln` collection in
   `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` during
   `BraggPdExperiment.__init__()`.
2. Add a read-only `refln` property on `BraggPdExperiment`.
3. Set the collection update priority after powder `data` updates, for
   example `_update_priority = 110`, and keep its own `_update()` a no-op
   unless a later design moves calculation ownership into the category.
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
   output, containing `linked_phase_id`, `d_spacing`,
   `sin_theta_over_lambda`, `index_h`, `index_k`, `index_l`, `f_calc`,
   and `f_squared_calc`.
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
4. If a linked phase is skipped because its structure id is missing,
   do not emit rows for that phase.
5. If the calculator cannot provide reflection metadata, clear
   `experiment.refln` and log a clear warning. Do not leave stale rows
   from a previous calculation.
6. Treat phase scale consistently. The plotted pattern should keep using
   `linked_phase.scale * structure_calc`; the `refln` fields should store
   either raw structure-factor values or phase-scaled values depending
   on the decision in the open questions.

Calculator-specific notes:

- Cryspy likely already computes `refln`-style arrays during powder
  pattern calculation. The implementation should extract h/k/l,
  d-spacing or sin(theta)/lambda, `f_calc`, and `f_squared_calc` from
  the same `dict_in_out` result used by `calculate_pattern()`.
- CrysFML currently returns only the calculated powder pattern through
  the EasyDiffraction wrapper. The implementation must either add a
  real reflection extraction path for CrysFML or explicitly warn and
  leave `refln` empty when CrysFML is active.
- The calculator base API and all concrete calculators must agree on the
  same record shape, even when a calculator returns no records.

## Plotting Integration

Replace the temporary display contract from `experiment.bragg_peaks` to
the real powder `experiment.refln` category.

Steps:

1. Update `Plotter._extract_bragg_tick_sets()` in
   `src/easydiffraction/display/plotting.py` to read from
   `experiment.refln`.
2. Group tick rows by raw `refln.linked_phase_id` values and stringify
   only when constructing display labels. This preserves numeric ids and
   matches the earlier powder plot review fix.
3. Use Miller indices from `index_h`, `index_k`, and `index_l` for hover
   text.
4. Use `f_squared_calc` as the default hover intensity unless the open
   questions choose `f_calc` or a phase-scaled intensity instead.
5. Resolve tick x positions from the selected plot x axis:
   - `d_spacing`: use `refln.d_spacing` directly.
   - `two_theta`: derive from `d_spacing` and the experiment wavelength.
   - `time_of_flight`: derive from `d_spacing` and TOF calibration
     coefficients.
6. Add inverse conversion utilities if they do not already exist, for
   example `d_to_twotheta()` and `d_to_tof()`, with invalid-domain values
   mapped to `NaN` and filtered out before plotting.
7. Keep existing safeguards from the three-panel plot work: normalize
   `x_min`/`x_max`, return no tick sets for empty filtered main ranges,
   and tolerate an empty `refln` category without rendering stray rows.
8. Decide whether to rename display DTO fields from `structure_id` to
   `phase_id`/`linked_phase_id`. A rename is clearer but touches more
   tests; keeping the internal DTO name is a smaller diff.

## CIF And Documentation

1. Ensure `refln.as_cif` writes a loop containing the inherited
   `_refln.*` fields plus `_refln.linked_phase_id`, `_refln.f_calc`, and
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
   clearing stale rows, row id generation, and mixed `linked_phase_id`
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
   fixtures, verifying grouping by `linked_phase_id`, x filtering,
   default intensity field, and empty-category behavior.
7. Conversion utility tests for `d_to_twotheta()` and `d_to_tof()` if
   those helpers are added.
8. CIF round-trip tests for `_refln.linked_phase_id`, `_refln.f_calc`,
   and `_refln.f_squared_calc`.

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

## Open Questions

1. Should the CIF name for the phase-link column be exactly
   `_refln.linked_phase_id`, or should it follow an existing CIF/pdCIF
   convention such as `_refln.phase_id`?
2. Should `linked_phase_id` store `linked_phase.id.value` exactly, or a
   different internal structure identifier when those ever diverge?
3. Should `f_calc` be a real non-negative amplitude `|F_calc|`, or do
   you need the complex calculated structure factor? The proposed
   descriptor supports only a real numeric value.
4. Should `f_squared_calc` store raw per-reflection `|F_calc|^2`, or a
   value already scaled by the linked phase scale and/or other powder
   intensity factors?
5. For Bragg tick hover intensity, should the plot display `f_calc`,
   `f_squared_calc`, or a separately named phase-scaled contribution?
6. Should the `refln` category store explicit powder x coordinates
   (`two_theta` / `time_of_flight`) as persisted columns, or should
   plotting derive x positions from `d_spacing` and instrument settings?
7. Is it acceptable for the first implementation to populate powder
   `refln` for Cryspy and warn/leave it empty for CrysFML until a
   CrysFML reflection extraction API is wired?
8. Should loaded CIF `refln` rows be considered cached calculation
   output that is always replaced on calculation, or user-visible data
   that should survive until the next successful calculation only?
9. Should the display DTO and tests be renamed from `structure_id` to
   `linked_phase_id` now, or should that rename be kept out of the first
   implementation to minimize plotter churn?
10. Should reflection row ids be globally sequential within the
    experiment, or include phase information such as
    `<linked_phase_id>:<row_number>` for easier debugging and CIF
    inspection?

## Suggested Commit Message

```text
Add powder Refln category plan
```