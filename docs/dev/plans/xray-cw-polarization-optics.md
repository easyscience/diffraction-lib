# Implementation Plan: X-ray CW Polarization Optics

This plan follows the conventions in [`AGENTS.md`](../../../AGENTS.md).
No deliberate exceptions to those instructions are taken. Per the
two-phase workflow, **Phase 1 is code + docs only** (no test creation
unless explicitly requested); tests and the five `pixi` verification
tasks run in **Phase 2**. When an AI agent executes this plan, **every
completed Phase 1 step must be staged with explicit paths and committed
locally before the next step** (atomic, single-purpose commits per
§Commits), and the agent stops at the Phase 1 review gate.

## ADR

Implements
[`docs/dev/adrs/accepted/xray-cw-polarization-optics.md`](../adrs/accepted/xray-cw-polarization-optics.md)
(Status: Accepted). The ADR was promoted to `accepted/` during P1.1 per
§Change Discipline. This plan uses the same slug as the ADR.

Related accepted ADRs consulted:

- [`model-sample-absorption.md`](../adrs/accepted/model-sample-absorption.md)
  — the precedent for a CW-powder physics correction applied as a shared
  pointwise multiplier after the engine returns (`absorption.apply`).
- [`immutable-experiment-type.md`](../adrs/accepted/immutable-experiment-type.md)
  — `radiation_probe` is a creation-time axis, persisted in
  `_expt_type.radiation_probe` and restored before the instrument is
  rebuilt.
- [`iucr-cif-tag-alignment.md`](../adrs/accepted/iucr-cif-tag-alignment.md)
  — experiment-tier fields keep short `_instr.*` names in the default
  save.

## Branch and PR

- Flat-slug implementation branch off `develop`:
  `xray-cw-polarization-optics` (created/checked out by `/draft-impl-1`).
- PR targets `develop`, not `master`. Do not push unless asked.

## Dependencies

No new runtime or dev dependencies. Cryspy already declares `k`/`cthm`
on its `Setup` item (defaults `k=0.0`, `cthm=0.91`), so binding is value
injection, not a backend extension. No `pyproject.toml` / `pixi.toml` /
`pixi.lock` changes are expected.

## Decisions (already made in the ADR)

1. The two values live on `experiment.instrument` (not a new optics
   category, not a peak-shape model).
2. The CW **powder Bragg** instrument splits by `radiation_probe`:
   `CwlPdInstrument` (tag `cwl-pd`) becomes `CwlPdNeutronInstrument`
   (`cwl-pd-neutron`) and `CwlPdXrayInstrument` (`cwl-pd-xray`). The
   X-ray class owns the optics fields; the neutron class does not. Single
   crystal (`cwl-sc`), TOF (`tof-pd`/`tof-sc`), and total-scattering PDF
   are unchanged. The identically named **data-range** `cwl-pd` tag is
   out of scope and stays. Both new classes carry the full **Bragg-only**
   compatibility tuple — `sample_form={POWDER}`,
   `scattering_type={BRAGG}`, `beam_mode={CONSTANT_WAVELENGTH}`, plus
   their `radiation_probe` — and `calculator_support={CRYSPY, CRYSFML}`.
   The old class's `TOTAL` / `PDFFIT` metadata is dropped because
   total-scattering PDF never routes through this instrument (the ADR
   calls those entries unused aspirational metadata); empty
   `Compatibility` axes mean "any", so the tuple must be stated in full
   to avoid silently matching every sample form / beam mode.
3. Public names are physical and non-refinable (`NumericDescriptor`):
   - `setup_polarization_coefficient` — dimensionless, default `0.0`,
     range `[0, 1]` → cryspy `_setup_K` / FullProf `Rpolarz`.
   - `setup_monochromator_twotheta` — degrees, default `0.0`, range
     `[0, 180)` → backend `cthm = cos²(radians(2θm))` (default `0.0°`
     ⇒ `cthm = 1.0`, "no monochromator").
4. **cryspy binds natively**: emit `_setup_K` / `_setup_cthm` in the
   generated CIF (and patch the cached dict like other instrument
   scalars). cryspy applies the Lorentz-polarization factor internally;
   the EasyDiffraction multiplier is **not** applied to cryspy output.
5. **crysfml binds via a post-pattern multiplier**, but only *after*
   the ADR Decision 5 gate is satisfied: the implementer first verifies
   (static source/CFL-grammar inspection) whether a native
   polarization/monochromator CFL line exists. If one does, that native
   line is emitted (and the ADR/plan updated); otherwise — the expected
   outcome from the bundled CFL examples — `y *= lp_factor(two_theta, k,
   cthm)` is applied after the engine returns, in a shared, unit-tested
   helper. Two shared pieces:
   `monochromator_cthm(angle)` (used by both adapters to produce the
   backend `cthm`) and `lp_factor(two_theta, k, cthm)` (crysfml runtime
   multiplier + the oracle that verifies cryspy's native output).
   P1.5 inspection found lower-level CrysFML Lorentz routines with
   optional `cthm`/`rkk` arguments, but the Python
   `cw_powder_pattern_from_dict` wrapper reads no dictionary keys for
   them, so the planned fallback multiplier is used.
6. Defaults are neutron-neutral: with the coefficient at `0.0`,
   `hh = 1` and results are unchanged until a user opts in.

## Open questions

1. **Verification reference data (P1.6).** Resolved in P1.6: no new
   FullProf polarized reference data was present, so the implementation
   used the plan's lighter demonstration path in
   `docs/docs/tutorials/simulate-nacl-xray.py` and regenerated the
   matching notebook.
2. **cryspy cached-dict keys (P1.4).** Resolved in P1.4: the CIF-build
   path emits `_setup_K` and `_setup_cthm`, the cached working dict is
   patched when `k`/`cthm` keys are exposed, and polarization settings
   are part of the cache-invalidation key so releases without those
   patch keys rebuild from CIF on value changes.

## Concrete files likely to change

Phase 1 (code + docs):

- `src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`
  — split `CwlPdInstrument` into `CwlPdInstrumentBase` +
  `CwlPdNeutronInstrument` + `CwlPdXrayInstrument`; declare the two
  descriptors and their properties on the X-ray class.
- `.../instrument/factory.py` — replace the single powder-CW rule with
  two `radiation_probe`-keyed rules.
- `.../instrument/__init__.py` — import/register the two new concrete
  classes (drop the old `CwlPdInstrument` import).
- `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` — pass
  `radiation_probe=self.experiment_type.radiation_probe.value` into
  `InstrumentFactory.default_tag(...)`.
- `src/easydiffraction/analysis/calculators/polarization.py` — **new**
  shared helper: `monochromator_cthm`, `lp_factor`, `apply`.
- `src/easydiffraction/analysis/calculators/cryspy.py` — emit
  `_setup_K` / `_setup_cthm` in `_cif_instrument_section`; optional
  cached-dict patch in `_update_experiment_in_cryspy_dict`.
- `src/easydiffraction/analysis/calculators/crysfml.py` — apply
  `polarization.apply(y, experiment)` on the return path (~line 170).
- A tutorial/verification source `.py` (P1.6, pending open question 1)
  plus its regenerated notebook via `pixi run notebook-prepare`.
- ADR move to `accepted/` + `docs/dev/adrs/index.md` row.

Phase 2 (tests + verification):

- `tests/unit/.../instrument/test_factory.py`,
  `tests/unit/.../analysis/calculators/test_support.py`,
  `tests/unit/.../instrument/test_cwl.py`, and a new
  `tests/unit/.../analysis/calculators/test_polarization.py`.
- `docs/dev/package-structure/{full,short}.md` (regenerated by
  `pixi run fix`).

## Implementation steps (Phase 1)

- [x] **P1.1 — Promote the ADR to `accepted/`.** The ADR was moved into
  `docs/dev/adrs/accepted/`, its status was set to `Accepted`, the
  existing **Experiment model** row in `docs/dev/adrs/index.md` was
  repointed to `accepted/xray-cw-polarization-optics.md`, this plan's
  `## ADR` link was updated, and remaining stale path references were
  cleared.
  Commit: `Promote xray-cw-polarization-optics ADR to accepted`

- [x] **P1.2 — Split the CW powder instrument by radiation probe.**
  In `cwl.py`, extract a `CwlPdInstrumentBase(CwlInstrumentBase)` holding
  the existing `calib_*` fields and properties. Add
  `CwlPdNeutronInstrument` (tag `cwl-pd-neutron`) and
  `CwlPdXrayInstrument` (tag `cwl-pd-xray`). Give **both** the full
  Bragg-only `Compatibility`:
  `sample_form=frozenset({SampleFormEnum.POWDER})`,
  `scattering_type=frozenset({ScatteringTypeEnum.BRAGG})`,
  `beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH})`, and
  `radiation_probe=frozenset({RadiationProbeEnum.NEUTRON})` /
  `{RadiationProbeEnum.XRAY})` respectively; and
  `calculator_support=CalculatorSupport(calculators=frozenset(
  {CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}))` — **no `PDFFIT`,
  no `TOTAL`**. On the X-ray class declare the two `NumericDescriptor`s
  (with `DisplayHandler`, `AttributeSpec` defaults/validators, and
  `TagSpec` exactly as ADR Decision 3) plus their getter/setter
  properties (mirror the `setup_wavelength_2` property style). In
  `factory.py` replace the `cwl-pd` rule with two rules keyed on
  `radiation_probe`. In `bragg_pd.py` pass `radiation_probe=...` to
  `default_tag(...)`. Update `instrument/__init__.py` registration. Leave
  the data-range `cwl-pd` tag untouched.
  Commit: `Split CW powder instrument by radiation probe`

- [x] **P1.3 — Add the shared Lorentz-polarization helper.**
  New module `analysis/calculators/polarization.py` mirroring
  `absorption.py`: `monochromator_cthm(twotheta_deg) -> float`
  (`cos²(radians(twotheta))`), `lp_factor(two_theta, k, cthm) ->
  np.ndarray` (`1 - k + k*cthm*cos²(two_theta)`), and `apply(y,
  experiment) -> np.ndarray` that no-ops unless the instrument exposes
  `setup_polarization_coefficient` with a non-zero value, otherwise
  multiplies `y` by `lp_factor` over the experiment's 2θ grid.
  Commit: `Add shared Lorentz-polarization helper`

- [x] **P1.4 — Bind cryspy natively.**
  In `cryspy.py` `_cif_instrument_section`, within the existing powder
  branch, when `hasattr(instrument, 'setup_polarization_coefficient')`
  append `_setup_K <coefficient>` and
  `_setup_cthm <monochromator_cthm(setup_monochromator_twotheta)>`
  (import `monochromator_cthm` from P1.3). Do **not** apply
  `polarization.apply` to cryspy output. If the cached working dict in
  `_update_experiment_in_cryspy_dict` exposes the keys, patch them with a
  presence guard (mirroring `offset_sycos`); otherwise document reliance
  on the CIF-build path + cache rebuild (open question 2).
  Commit: `Emit cryspy polarization setup for X-ray CW powder`

- [x] **P1.5 — Bind crysfml (verify native line first, then fall back).**
  Satisfy the ADR Decision 5 gate explicitly: statically inspect the
  active CrysFML CFL grammar / bundled examples for a native
  polarization or monochromator line. **If one exists**, emit that native
  line and update the ADR/plan to record it (or stop and ask if it
  reopens scope). **If none exists** (the expected outcome), apply
  `polarization.apply(y, experiment)` on the crysfml return path
  alongside the existing `absorption_correction.apply(...)`
  (~`crysfml.py:170`); no-op for neutron / zero coefficient. State the
  inspection result in the commit body.
  Commit: `Apply Lorentz-polarization envelope on crysfml CW powder`

- [x] **P1.6 — Demonstrate the new fields in docs.**
  Per open question 1: either add the
  `pd-xray-pbso4-single-polarized-wdt48.py` verification source (if the
  FullProf reference data is available) or set
  `setup_polarization_coefficient` / `setup_monochromator_twotheta` in an
  existing X-ray CW source and show the pattern responds. Edit the `.py`
  source only, then run `pixi run notebook-prepare` and commit the source
  plus regenerated notebook.
  Commit: `Document X-ray CW polarization optics fields`

- [x] **P1.7 — Phase 1 review gate.** No-code step. Mark complete and
  commit the checklist update alone.
  Commit: `Reach Phase 1 review gate`

## Phase 2 — Verification

Add/update tests, then run the five tasks. Capture logs with the
zsh-safe pattern where output is needed for analysis.

Tests to add/update:

- `test_factory.py` — `default_tag(..., radiation_probe=NEUTRON|XRAY)`
  resolves to `cwl-pd-neutron` / `cwl-pd-xray`; `create()` for both tags;
  remove `'cwl-pd'` instrument assertions.
- `test_support.py` — replace the `cwl-pd` calculator-support assertion
  with the two new tags, asserting **only** the Bragg engines
  (`{CRYSPY, CRYSFML}`) for `cwl-pd-neutron` / `cwl-pd-xray` (no
  `PDFFIT`).
- `test_cwl.py` — the X-ray class exposes both descriptors with correct
  defaults (`0.0`, `0.0`), range validation rejects out-of-range/wrong
  type (`typeguard.TypeCheckError`), and the neutron class does **not**
  expose them; CIF round-trip of `_instr.polarization_coefficient` /
  `_instr.monochromator_twotheta`.
- new `test_polarization.py` — `monochromator_cthm(0) == 1.0`, the
  `cos²` identity at a known angle, `lp_factor` reduces to `1` when
  `k == 0`, and `apply` is a no-op for the neutron instrument.
- Do **not** modify the data-range `test_factory.py` `cwl-pd` cases.

Commands:

```bash
pixi run fix
pixi run check > /tmp/edi-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/edi-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/edi-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/edi-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/edi-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/edi-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/edi-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/edi-script.log; exit $script_tests_exit_code
```

`pixi run fix` regenerates `docs/dev/package-structure/{full,short}.md`;
include them only in the `pixi run fix` commit. Leave generated
`docs/dev/benchmarking/*.csv` untracked unless asked.

## Status checklist

- [x] P1.1 — Promote the ADR to `accepted/` and update `index.md`
- [x] P1.2 — Split the CW powder instrument by radiation probe
- [x] P1.3 — Add the shared Lorentz-polarization helper
- [x] P1.4 — Bind cryspy natively
- [x] P1.5 — Bind crysfml (verify native line first, then fall back)
- [x] P1.6 — Demonstrate the new fields in docs
- [x] P1.7 — Phase 1 review gate
- [ ] Phase 2 — tests added/updated and all five tasks pass

## Suggested Pull Request

**Title:** Match FullProf X-ray intensities with polarization and
monochromator settings

**Description:** Constant-wavelength X-ray powder experiments now expose
two incident-optics controls — a polarization coefficient and a
pre-sample monochromator angle — so calculated intensities can match the
Lorentz-polarization correction used by FullProf and other Rietveld
codes. The settings appear only on X-ray powder instruments and are
applied by both the CrysPy and CrysFML engines; neutron experiments are
unaffected, and existing X-ray results stay the same until you set a
polarization value. This closes a known gap behind the residual
intensity mismatch seen in the PbSO₄ X-ray verification.
