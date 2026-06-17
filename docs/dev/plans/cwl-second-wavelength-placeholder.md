# Plan: Second-Wavelength (Kα₁/Kα₂) Placeholder on the CWL Instrument

Follows [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions to
those instructions.

## ADR

No new ADR is required. This adds two parameters to an existing
`CategoryItem` (the constant-wavelength instrument) and serialises them
through the established CIF machinery; it introduces no new category,
factory, switchable-category wiring, or datablock. It touches CIF
serialisation only by populating the **already-scaffolded**
`_diffrn_radiation_wavelength` loop, so it stays within
[`edstar-project-persistence`](../adrs/accepted/edstar-project-persistence.md)
(which documents the existing `_instrument.setup_wavelength` ↔
`_diffrn_radiation_wavelength.value` mapping). If review decides the
collision/precedence rules below deserve a recorded decision, promote
this section to a short ADR before the PR.

That ADR carries a persisted-field **inventory** (its CWL-instrument
rows and the per-attribute Edi-name table), so adding two persisted
fields makes the ADR stale unless it is updated in lockstep. This plan
therefore includes a Phase 1 step (P1.3) to update those inventory rows
— it amends the inventory, not the decision (Review 1, F3).

## Summary of the change

Constant-wavelength instruments today carry a single `setup_wavelength`.
Laboratory X-ray sources (and the FullProf X-ray reference under
`docs/docs/verification/fullprof/pd-xray-pbso4/`) use a Cu Kα₁/Kα₂
**doublet**: a second wavelength with a fixed relative intensity.
FullProf encodes this as `Lambda1 Lambda2 Ratio`; the future crysfml CFL
reads it as `LAMBDA λ₁ λ₂ ratio`; CIF core encodes it as a looped
`DIFFRN_RADIATION_WAVELENGTH` with per-row `value` + `wt`.

This change adds a **placeholder** for that doublet on the CWL
instrument category: two new parameters that can be set, read, and
round-trip through CIF. **Binding to the calculation engines is out of
scope** — no calculator reads these values yet, so a doublet experiment
calculates exactly as today (single wavelength). cryspy has no
second-wavelength support and is explicitly not addressed; the eventual
consumer is a future crysfml build via the `LAMBDA` CFL directive.

New public settings on `CwlInstrumentBase`, both **non-refinable**
`NumericDescriptor`s (see Decision "Non-refinable by construction"):

- `setup_wavelength_2` — the second wavelength λ₂ (Å). Default `0.0`
  meaning "no second component" (monochromatic, today's behaviour).
- `setup_wavelength_2_to_1_ratio` — the relative intensity of the second
  component to the first, **I(wavelength_2) / I(wavelength)**. The
  `_2_to_1_` ordering names the direction explicitly (numerator =
  component 2, denominator = component 1). Default `0.0` (second
  component contributes nothing). This is the FullProf `Ratio` column,
  the CFL `LAMBDA` third value, and the CIF `wt` of the second loop row
  (with the first row's `wt` normalised to 1).

### Reachable states (all four are publicly settable)

The two fields are set independently, so every combination is reachable.
The semantics are fully specified — there are no undefined mixed states:

| `setup_wavelength_2` | `…_2_to_1_ratio` | Meaning                                                                        | CIF / output                                                  |
| -------------------- | ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| `0`                  | `0`              | Monochromatic (default, today)                                                 | single row / scalar                                           |
| `> 0`                | `0`              | Second λ recorded but **disabled** — matches the CFL `LAMBDA … 0.0` convention | single row / scalar; λ₂ value preserved on edi-CIF round-trip |
| `> 0`                | `> 0`            | **Active doublet**                                                             | 2-row `_diffrn_radiation_wavelength` loop                     |
| `0`                  | `> 0`            | **Invalid**: a relative intensity for a wavelength that does not exist         | export raises a clear `ValueError`                            |

So "active doublet" ≡
`setup_wavelength_2 > 0 and setup_wavelength_2_to_1_ratio > 0`;
"disabled" is governed by `ratio == 0` (any λ₂); the incomplete pair
`(λ₂ == 0, ratio > 0)` is a boundary user-input error and is rejected,
not silently dropped.

## Decisions

- **Names.** `setup_wavelength_2` and `setup_wavelength_2_to_1_ratio`,
  chosen in conversation. The ratio name encodes numerator/denominator
  direction so it cannot be misread as `λ/λ₂` vs `λ₂/λ`.
- **Scope.** Settings **plus CIF round-trip**; no engine binding.
- **Non-refinable by construction (Review 1, F1).** Both fields are
  `NumericDescriptor`s, **not** `Parameter`s. A `NumericDescriptor` has
  no `free` flag, so the fitter — which collects only free `Parameter`s
  (`src/easydiffraction/analysis/fitting.py:103`) and syncs them back
  each residual evaluation (`…/fitting.py:479`) — can never pick these
  up. This removes the silent no-op a refinable but engine-unbound value
  would create: a scientist cannot mark a doublet setting `free` and
  watch the optimiser move a value that changes nothing. They follow the
  existing editable-but-non-refinable pattern used for the CWL
  data-range bounds (`…/categories/data_range/cwl.py`). When engine
  binding lands, a follow-up can promote them to `Parameter`.
- **Mixed states are fully specified (Review 1, F2).** See the
  "Reachable states" table above. `ratio == 0` means _disabled_
  (single-row output, λ₂ preserved), matching the CFL `LAMBDA … 0.0`
  convention; `ratio > 0 and λ₂ == 0` is an incomplete pair and is
  **rejected at export time** with a clear `ValueError` (via the
  project's `log.error(..., exc_type=ValueError)` pattern) rather than
  silently emitting a single row and dropping the ratio.
- **Ratio is a relative intensity, not a wavelength ratio.** Range
  `[0, 1]` (matches CIF `wt` `_enumeration.range 0.0:1.0`). Documented
  in the docstring and field description.
- **edi-CIF round-trip is automatic.** `category_item_to_cif` writes
  each field by its **`edi_name`** (`io/cif/serialize.py:189`), and
  `category_item_from_cif` reads by the union `read_names`
  (`io/cif/handler.py` `read_names`); `NumericDescriptor`s serialise
  through this same path (the CWL data-range bounds prove it). Distinct
  `edi_names` (`_instrument.setup_wavelength_2`,
  `_instrument.setup_wavelength_2_to_1_ratio`) give a clean scalar
  round-trip with **no extra serialise code** — the placeholder persists
  the moment the fields exist.
- **IUCr/pdCIF export uses the loop.** The strict export
  (`io/cif/iucr_writer.py` → `WavelengthTransformer`) emits the proper
  `_diffrn_radiation_wavelength` loop when the doublet is active and
  keeps today's single-row scalar output otherwise. The transformer
  already has an `items()` path and an unused `loop()` stub
  (`io/cif/iucr_transformers.py:107`) reserved for exactly this.
- **Avoid the shared-tag collision.** `setup_wavelength` already lists
  `_diffrn_radiation_wavelength.value` in its `cif_names`. The two new
  fields' `cif_names` contain **only** their edi-CIF short names
  (`_instr.wavelength_2`, `_instr.wavelength_2_to_1_ratio`) — they do
  **not** list any `_diffrn_radiation_wavelength.*` tag, so the generic
  scalar writer/reader can never emit or consume a duplicate bare
  `_diffrn_radiation_wavelength.value`/`.wt`. The IUCr `value`/`wt`
  pairing is produced solely by the loop transformer, which
  disambiguates components by row `id`. (`setup_wavelength`'s existing
  tags are left unchanged.)

## Open questions

1. **IUCr loop _import_.** This plan round-trips through **edi-CIF**
   (the project-persistence format) and additionally _exports_ the IUCr
   loop. Reading a 2-row `_diffrn_radiation_wavelength` loop back from a
   strict-IUCr file into the two parameters is **not** in scope — the
   generic scalar reader only sees the first row. Flag for a follow-up
   if strict-IUCr import of doublets is wanted. (Recommended: defer.)
2. **`xray_symbol` / `type` metadata.** CIF core also offers
   `_diffrn_radiation_wavelength.xray_symbol` (e.g. `K-L~3~`/`K-L~2~`)
   and `.type`. Out of scope for the placeholder; note as deferred.
3. **TOF instruments.** The doublet is a CWL concept; no change to
   `instrument/tof.py`. Confirm reviewers agree the fields live on
   `CwlInstrumentBase` only.
4. **Where the incomplete-pair guard lives.** The plan raises the
   `(λ₂ == 0, ratio > 0)` error at IUCr export (in the transformer),
   because the two fields are set independently and a set-time check
   would trip on the transient half-set state. Reviewers may prefer an
   additional validation hook; export-time is proposed as the single
   enforced boundary for the placeholder. (Recommended: export-time
   only.)

## Deferred work — engine binding and its performance note

Engine binding is out of scope here, but recording the trade-off so the
follow-up starts informed:

- **Two ways to compute the doublet.** (a) *Calculator-independent* —
  edi calls the engine once at λ₁ and once at λ₂ and weight-sums the two
  patterns; works for any engine (and is the only option for cryspy,
  which has no native doublet). (b) *Native crysfml* — a future build
  computes both lines in one pass via the `LAMBDA λ₁ λ₂ ratio` CFL
  directive.
- **(a) is expected to be slower, bounded by ~2× the single-wavelength
  cost.** In crysfml's `cw_powder_pattern_profile`
  (`tmp/crysfml/Src/CFML_Utilities/Utilities_Patterns.f90`) the
  per-reflection structure factors `ref(i)%fc(2)**2` are computed
  **once** before the reflection loop; a native doublet extends that
  same loop to lay down a second peak at the λ₂ position scaled by
  `ratio`, reusing the same |F|². So native pays 1× structure-factors +
  1× reflection generation + ~2× profile summation + 1× call overhead,
  whereas the two-pass approach repeats **all** of that. The gap is
  small when profile summation dominates (fine grid / broad peaks) and
  approaches the full 2× when structure-factor / reflection-generation /
  marshalling dominate; it compounds across a fit's many residual
  evaluations.
- **Caveats.** The crysfml routine wired into easydiffraction today is
  itself single-wavelength (uses `Lambda(1)`, ignores the `twowaves`
  flag set in `Format_CFL.f90`), so even the native path needs the
  future build. Because Kα₁/Kα₂ differ by ~0.25%, |F|² is effectively
  identical for both lines — so a smarter calculator-independent variant
  could compute reflections/|F|² once and place only the second peak set
  itself, matching native's "compute once, place twice", at the cost of
  edi owning profile generation (a larger change than this placeholder).

## Concrete files likely to change

- `src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`
  — add the two `NumericDescriptor`s on `CwlInstrumentBase` with
  getter/setter properties (mirroring the `data_range/cwl.py`
  non-refinable pattern), distinct `edi_names`, range `ge=0.0` /
  `[0, 1]` validators, and `TagSpec`s carrying only the `_instr.*` short
  `cif_names` per the collision decision.
- `src/easydiffraction/io/cif/iucr_transformers.py` — make
  `WavelengthTransformer.items()` return the single row when
  monochromatic-or-disabled (`ratio == 0`) and `None` when the doublet
  is active (so the writer falls through to `loop()`); implement
  `loop()` to emit the 2-row `_diffrn_radiation_wavelength` loop (`id`,
  `value`, `wt`) when active; and raise a clear `ValueError` for the
  incomplete pair `(λ₂ == 0, ratio > 0)`.
- `src/easydiffraction/io/cif/iucr_writer.py` —
  `_write_wavelength_section` already prefers `items()` then `loop()`
  (lines 247-269); verify it needs no change once `items()`/`loop()`
  cooperate. Adjust only if the fall-through guard
  (`if wavelength is None`) interferes.
- `docs/dev/adrs/accepted/edstar-project-persistence.md` — extend the
  CWL-instrument inventory row (~line 633) and the per-attribute Edi
  name table (~line 847) with the two new fields and their `_instr.*` /
  `_instrument.*` names and the IUCr loop note (F3).
- Tests (Phase 2):
  - `tests/unit/easydiffraction/datablocks/experiment/categories/instrument/test_cwl.py`
    — defaults are off; set/get; range validation; monochromatic
    behaviour unchanged; **non-refinable** (the field is a
    `NumericDescriptor` with no `free`, so it is never collected by the
    fitter).
  - `tests/unit/easydiffraction/io/cif/test_iucr_transformers.py` and
    `test_iucr_writer.py` — scalar output when monochromatic and when
    disabled (`ratio == 0`, `λ₂ > 0`); 2-row loop when active; clear
    `ValueError` for the incomplete pair `(λ₂ == 0, ratio > 0)`.
  - edi-CIF round-trip: a `setup_wavelength_2`/ratio set on an
    experiment (including the disabled `ratio == 0`, `λ₂ > 0` state)
    survives `as_cif` → `from_cif` (extend the nearest existing
    serialize round-trip test under
    `tests/unit/easydiffraction/io/cif/`).
- Docs: no tutorial change. The `docs/docs/verification/pd-xray-pbso4`
  page stays a `known_discrepancy` (engine binding is still absent), so
  it is untouched by this plan.

## Branch and PR notes

- Flat-slug implementation branch off `develop`:
  `cwl-second-wavelength-placeholder` (created by `/draft-impl-1`, not
  now). PR targets `develop`.
- Each Phase 1 step is staged with explicit paths and committed locally
  before the next step (per `AGENTS.md` §Commits). Atomic,
  single-purpose commits.

## Implementation steps (Phase 1)

- [x] **P1.1 — Add the two placeholder fields to `CwlInstrumentBase`.**
      In `instrument/cwl.py`, add `_setup_wavelength_2`
      (`NumericDescriptor`, default `0.0`, `RangeValidator(ge=0.0)`,
      units `angstroms`) and `_setup_wavelength_2_to_1_ratio`
      (`NumericDescriptor`, default `0.0`,
      `RangeValidator(ge=0.0, le=1.0)`, dimensionless) with getter
      properties and value setters following the non-refinable
      `data_range/cwl.py` pattern. Give them distinct `edi_names`
      (`_instrument.setup_wavelength_2`,
      `_instrument.setup_wavelength_2_to_1_ratio`) and `cif_names`
      containing only the `_instr.*` short names (collision decision
      above). Docstrings state the ratio direction and the `[0, 1]`
      range. No tests yet (Phase 1 is code + docstrings only). Commit:
      `Add second-wavelength placeholder fields to CWL instrument`

- [x] **P1.2 — Emit the IUCr wavelength loop and guard mixed states.**
      In `iucr_transformers.py`, update `WavelengthTransformer.items()`
      to return the single-row items when monochromatic **or disabled**
      (`ratio == 0`, any λ₂) and `None` when the doublet is active;
      implement `loop()` to return an `IucrLoop` of
      `_diffrn_radiation_wavelength.{id,value,wt}` with rows
      `(1, λ₁, 1.0)` and `(2, λ₂, ratio)` when active; and raise a clear
      `ValueError` (project `log.error(..., exc_type=ValueError)`
      pattern) for the incomplete pair `(λ₂ == 0, ratio > 0)`. Verify
      `_write_wavelength_section` in `iucr_writer.py` routes correctly;
      adjust the guard only if required. Commit:
      `Emit diffrn_radiation_wavelength loop for CWL doublet`

- [x] **P1.3 — Update the Edi persistence inventory ADR.** In
      `docs/dev/adrs/accepted/edstar-project-persistence.md`, add the
      two new fields to the CWL-instrument inventory row (~line 633) and
      the per-attribute Edi-name table (~line 847), with their
      `_instr.*` and `_instrument.*` names and an IUCr-loop note.
      Inventory amendment only; the decision is unchanged. Commit:
      `Record CWL second-wavelength fields in persistence ADR`

- [x] **P1.4 — Phase 1 review gate.** No-code step. Mark complete and
      commit the checklist update alone. Commit:
      `Reach Phase 1 review gate`

## Verification (Phase 2)

Run in order; capture output with the zsh-safe pattern when analysis is
needed:

```bash
pixi run fix
pixi run check > /tmp/edi-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/edi-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/edi-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 100 /tmp/edi-unit.log; exit $unit_tests_exit_code
pixi run integration-tests
pixi run script-tests
```

Phase 2 adds the tests listed under _Concrete files_:

- CWL instrument: defaults off, set/get, range validation, monochromatic
  output unchanged, and **non-refinable** (field is a
  `NumericDescriptor` with no `free`; never collected by the fitter).
- IUCr transformer/writer: scalar when monochromatic and when disabled
  (`ratio == 0`, `λ₂ > 0`); 2-row loop when active; `ValueError` for the
  incomplete pair `(λ₂ == 0, ratio > 0)`.
- edi-CIF round-trip of both new fields, including the disabled state.

## Status checklist

- [x] P1.1 — placeholder fields added (non-refinable
      `NumericDescriptor`s)
- [x] P1.2 — IUCr loop emitted when active; mixed states guarded
- [x] P1.3 — Edi persistence inventory ADR updated
- [x] P1.4 — Phase 1 review gate
- [ ] Phase 2 — tests added and all five `pixi run` tasks clean

## Suggested Pull Request

**Title:** Support a second X-ray wavelength (Kα₁/Kα₂) on
constant-wavelength instruments

**Description:** Constant-wavelength instruments can now record a second
incident wavelength and its relative intensity — the Kα₁/Kα₂ doublet
typical of laboratory X-ray sources. The new `setup_wavelength_2` and
`setup_wavelength_2_to_1_ratio` settings are saved and restored with the
project and exported in standard CIF. This is a data-model step: the
values are stored and shared but not yet used in pattern calculation, so
existing single-wavelength experiments are unaffected.
