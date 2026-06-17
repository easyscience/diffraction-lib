# ADR: X-ray CW Polarization Optics

## Status

Proposed.

## Date

2026-06-17

## Group

Experiment model.

## Context

This ADR follows the conventions in
[`AGENTS.md`](../../../../AGENTS.md).

Constant-wavelength X-ray powder calculations need the same
Lorentz-polarization controls that FullProf exposes on the PCR
`Lambda1 Lambda2 Ratio Bkpos Wdt Cthm muR AsyLim Rpolarz 2nd-muR`
line. The two relevant values are:

| FullProf field | Backend field | Meaning |
| -------------- | ------------- | ------- |
| `Rpolarz`      | Cryspy `_setup_K` | Polarization coefficient in the CW Lorentz-polarization factor. |
| `Cthm`         | Cryspy `_setup_cthm` | `cos²(2θm)`, where `2θm` is the pre-specimen monochromator angle. |

These names are calculator-oriented and should not become the public
EasyDiffraction API. The IUCr powder dictionary uses the physical
monochromator angle:

- `_pd_instr.2theta_monochr_pre`
- `_pd_instr.monochr_pre_spec`

The core dictionary has polarization provenance fields:

- `_diffrn_radiation.polarisn_ratio`
- `_diffrn_radiation.polarisn_norm`

However, `_diffrn_radiation.polarisn_ratio` is not an exact alias for
FullProf `Rpolarz` / Cryspy `K`, so the first implementation persists
the EasyDiffraction polarization coefficient under the experiment-tier
short instrument namespace (`_instr.*`, like every other instrument
field) rather than silently claiming strict IUCr equivalence. The IUCr
items above are recorded as provenance and become report-export
candidates, consistent with
[`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md)
(experiment tier keeps short UX names in the default save; IUCr/
`_easydiffraction_*` forms are a report-export concern).

### Backend support already present

The Cryspy `Setup` item already declares both fields as optional,
non-refinable descriptors (`C_item_loop_classes/cl_1_setup.py`):
`k` (CIF `_setup_K`) and `cthm` (CIF `_setup_cthm`), with defaults
`k = 0.0` and `cthm = 0.91`. Neither is in Cryspy's refinable-attribute
set, so binding them is a value-injection task, not a backend
extension. (Note the FullProf diagnostic below uses `Cthm = 0.8`, which
differs from Cryspy's `0.91` default — defaults must be set explicitly,
not inherited from the backend.) CrysFML's current Python wrapper has no
equivalent declared field (see Decision 5).

The existing CW instrument category is a single class,
`CwlPdInstrument` (factory tag `cwl-pd`,
`src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`),
serving **both** neutron and X-ray, **both** `bragg` and `total`
scattering, across the `cryspy`, `crysfml`, and `pdffit` calculators.
The recent second-wavelength fields (`setup_wavelength_2`,
`setup_wavelength_2_to_1_ratio`) on `CwlInstrumentBase` are the closest
precedent for adding fixed, non-refinable instrument descriptors and are
the model this ADR follows for declaration style.

### Diagnostic evidence

`docs/docs/verification/pd-xray-pbso4-single-polarized-wdt48.py`
adds a focused diagnostic reference generated from
`pbsox_single_polarized_wdt48.pcr`:

- `Lambda1 = Lambda2 = 1.540560`
- `Ratio = 0`
- `Wdt = 48`
- `Rpolarz = 0.5`
- `Cthm = 0.8`

The current EasyDiffraction adapters do not expose or bind these
optics fields. Against that FullProf reference the current results are:

| Engine | State | Profile diff | Max deviation | Area ratio | Correlation |
| ------ | ----- | ------------ | ------------- | ---------- | ----------- |
| cryspy | raw | 33.65 % | 33.54 % | 0.7537 | 0.9931 |
| cryspy | scale + U/V/W/Y refined | 10.20 % | 6.48 % | 1.1222 | 0.9950 |
| crysfml | raw | 36.18 % | 34.63 % | 0.6859 | 0.9895 |
| crysfml | scale + U/V/W/Y refined | 10.08 % | 6.69 % | 1.1156 | 0.9951 |

The large raw area mismatch is expected: the FullProf reference contains
an active X-ray polarization correction, while EasyDiffraction currently
uses the backend defaults. The residual ≈10 % profile difference after
profile refinement is not assigned solely to polarization because the
PbSO4 X-ray diagnostics also show anomalous-dispersion table differences
between FullProf and Cryspy/CrysFML.

## Decision

### 1. Keep the fields in `experiment.instrument`

These values describe incident-beam optics and the diffractometer
monochromator, not a peak-shape model. They belong on the CW powder
instrument category. This matches the rejection of a separate optics
category (see Alternatives).

### 2. Split CW powder instruments by radiation probe

The fields are useful for X-ray CW powder experiments and meaningless
for neutron CW powder experiments, where the polarization coefficient is
identically zero (unlike sample absorption, which is physically real for
both probes — so the
[`model-sample-absorption.md`](../accepted/model-sample-absorption.md)
single-shared-category precedent does not transfer cleanly here). Use the
existing `Compatibility.radiation_probe` axis and register separate
instrument classes:

- `CwlPdNeutronInstrument`
- `CwlPdXrayInstrument`

`CwlPdXrayInstrument` owns the X-ray optics fields. The neutron class
does not expose them.

**This is the first use of `radiation_probe` as a category-routing
discriminator in the codebase.** It therefore carries concrete,
non-trivial impact that the implementing plan must cover:

- `InstrumentFactory` default rules
  (`.../instrument/factory.py`) currently key only on
  `(beam_mode, sample_form)`. They must gain `radiation_probe`, and the
  single `cwl-pd` tag splits into `cwl-pd-neutron` / `cwl-pd-xray`
  (factory tags follow
  [`factory-tag-naming.md`](../accepted/factory-tag-naming.md)).
- The call site `BraggPdExperiment` (`.../experiment/item/bragg_pd.py`)
  builds the default instrument tag via
  `InstrumentFactory.default_tag(scattering_type, beam_mode,
  sample_form)` and must also pass `radiation_probe`.
- Renaming the persisted **instrument** tag is a breaking change to
  saved projects and to any test/tutorial CIF pinning the instrument
  `cwl-pd`. The project is in beta (no legacy shims), so the rename is
  acceptable. The plan should sweep with `git grep -n 'cwl-pd'` but
  **classify** the hits: only the instrument-category tag
  (`instrument/cwl.py`, `instrument/factory.py`, and instrument-tag
  references in `analysis/calculators/support.py` plus the instrument
  factory/support tests) is retired. The string `cwl-pd` is **also** an
  unrelated tag on the data-range category (`data_range/cwl.py:48`,
  `data_range/factory.py:21`, and `data_range/test_factory.py`); that is
  axis/range metadata, not incident-beam optics, and **must be left
  unchanged** — this ADR does not rename CW-powder category tags
  generally.

**Scope is powder-Bragg CW only, and total scattering needs no
migration.** Only two call sites instantiate an instrument through
`InstrumentFactory.default_tag(...)`: `BraggPdExperiment.__init__`
(`.../experiment/item/bragg_pd.py:61`) and `ScExperimentBase.__init__`
(`.../experiment/item/base.py:505`). `TotalPdExperiment`
(`.../experiment/item/total_pd.py`) delegates to `PdExperimentBase` and
**never builds an instrument via the factory**, so the `total`/`pdffit`
PDF path does not route through `cwl-pd` and is untouched by the split.
(The `TOTAL`/`PDFFIT` entries in `CwlPdInstrument.compatibility` are
unused aspirational metadata, not a live routing path.) The routing
matrix the plan must implement:

| scattering | beam_mode | sample_form | radiation_probe | default tag |
| ---------- | --------- | ----------- | --------------- | ----------- |
| bragg | constant wavelength | powder | neutron | `cwl-pd-neutron` |
| bragg | constant wavelength | powder | xray | `cwl-pd-xray` |
| bragg | constant wavelength | single crystal | (any) | `cwl-sc` (unchanged) |
| bragg | time of flight | powder | (any) | `tof-pd` (unchanged) |
| total | constant wavelength | powder | (any) | no factory instrument (unchanged) |

Single crystal (`cwl-sc`) and TOF (`tof-pd`/`tof-sc`) stay
probe-neutral: this ADR scopes X-ray optics to powder-Bragg CW, where
the FullProf LP line lives. The `InstrumentFactory` rule for the
powder-Bragg CW slot is the only one that gains a `radiation_probe`
discriminator, and the **instrument** `cwl-pd` tag is the only retired
tag — the identically named data-range tag is out of scope (see the
classification note above).

**Neutron-neutral defaults — no change to existing results until
opt-in.** Even on `CwlPdXrayInstrument`, the polarization coefficient
defaults to `0.0` (and the monochromator term is then inert, since the
Lorentz-polarization factor reduces to the neutron form when `k = 0` —
see Decision 4). Existing X-ray verification numbers therefore do **not**
change until a user explicitly sets the coefficient. Picking a non-zero
characteristic-radiation default is deferred (see Deferred Work).

### 3. Use physical public names, non-refinable

Expose two fixed, non-refinable `NumericDescriptor`s (mirroring the
second-wavelength fields — no `Parameter.free` flag, so the fitter never
touches them):

```python
experiment.instrument.setup_polarization_coefficient
experiment.instrument.setup_monochromator_twotheta
```

Do not expose public names `setup_k`, `setup_cthm`, `K`, or `Cthm`.

`setup_polarization_coefficient` is a dimensionless fixed descriptor.
It maps directly to FullProf `Rpolarz` and Cryspy `_setup_K`. It is a
polarization fraction, so the value is constrained to `[0, 1]` and
**defaults to `0.0`** (no correction — the pure opt-in default of
Decision 2):

```python
NumericDescriptor(
    name='polarization_coefficient',
    units='',
    value_spec=AttributeSpec(
        default=0.0,
        validator=RangeValidator(ge=0.0, le=1.0),
    ),
    tags=TagSpec(
        edi_names=['_instrument.setup_polarization_coefficient'],
        cif_names=['_instr.polarization_coefficient'],
    ),
)
```

`setup_monochromator_twotheta` is a fixed descriptor in degrees. Its
IUCr provenance is the physical item `_pd_instr.2theta_monochr_pre`. It
**defaults to `0.0` degrees**, which the conversion in Decision 3
(below) maps to `cthm = cos²(0) = 1.0` — i.e. "no pre-sample
monochromator", the correct neutral starting point (and a no-op while
the coefficient is `0.0`). The value is constrained to `[0, 180)`
degrees:

```python
NumericDescriptor(
    name='monochromator_twotheta',
    units='degrees',
    value_spec=AttributeSpec(
        default=0.0,
        validator=RangeValidator(ge=0.0, lt=180.0),
    ),
    tags=TagSpec(
        edi_names=['_instrument.setup_monochromator_twotheta'],
        cif_names=['_instr.monochromator_twotheta'],
    ),
)
```

Neither field inherits a value from the Cryspy backend defaults
(`k = 0.0`, `cthm = 0.91`); both are set explicitly here so an opt-in
user gets the EasyDiffraction default, not a hidden backend value. The
`@typechecked`/`RangeValidator` boundary rejects out-of-range or
wrong-type user input (a `typeguard.TypeCheckError` for type, a range
error for value), keeping the user-input edge case explicit.

Backend adapters convert the public angle to the backend value:

```python
cthm = cos(radians(setup_monochromator_twotheta)) ** 2
```

because the public value is the monochromator `2θ` angle and the
backend wants `cos²(2θm)`. This mirrors the established public→backend
conversion pattern (`_march_r_to_cryspy_g1` in
`analysis/calculators/cryspy.py`, where the public March coefficient is
inverted before it reaches Cryspy).

### 4. Bind Cryspy directly

The Cryspy CW Lorentz factor is:

```python
hh = 1 - k + k * cthm * cos(two_theta) ** 2
lorentz = hh / (sin(theta) * sin(two_theta))
```

where `k = 0` for neutrons, `k = 0.5` for characteristic X-ray
radiation, and `cthm = cos²(2θm)`. Note `k = 0` collapses `hh` to `1`,
which is why the neutron path and the as-yet-unset X-ray path are both
no-ops.

Because Cryspy already declares `k`/`cthm` (see Context), the Cryspy
adapter only needs to inject values for `CwlPdXrayInstrument`:

- emit `_setup_K` and `_setup_cthm` in the generated CIF;
- patch the cached Cryspy dictionaries with `k` and `cthm` (the same
  cached-dict update path used for other instrument scalars) so
  minimizer iterations do not recompute against stale values;
- include these fields in the cache-invalidation surface.

Cryspy thus applies the LP factor **internally**, on its own
`two_theta` grid — it does **not** consume the EasyDiffraction `hh`
multiplier at runtime. The only EasyDiffraction code on the Cryspy path
is the angle→`cthm` conversion (the input it is fed). See Decision 5 for
exactly what is shared and what is not.

### 5. Bind CrysFML through the CFL path or a shared adapter correction

The current CrysFML Python wrapper exposes `patterns_simulation(strings)`
around a CFL parser, and the adapter maps instrument scalars through
`_INSTRUMENT_ATTRIBUTE_MAP` in `analysis/calculators/crysfml.py`. The
bundled CFL examples document `LAMBDA`, `UVWXY`, `ASYM`, `WDT`, and
`Zero_Sy`, but they do not show `Cthm` or `Rpolarz` condition lines.

Implementation must first verify whether the active CrysFML CFL grammar
accepts a native polarization/monochromator line. If it does, the
CrysFML adapter should emit that line.

If no native CFL input exists, the CrysFML adapter applies the same
pointwise multiplier as Cryspy's `hh` term after CrysFML returns the
powder pattern:

```python
hh = 1 - k + k * cthm * cos(two_theta) ** 2
y_corrected = hh * y_crysfml
```

This fallback is acceptable because it is a smooth
Lorentz-polarization envelope on the calculated CW powder pattern.

**What is shared vs. what is not.** Cryspy binds natively (Decision 4)
and CrysFML uses the fallback multiplier, so the two engines do **not**
run the same multiplier code path. The shared surface is therefore split
into two precisely scoped, unit-tested pieces, not one "helper consumed
by both adapters":

1. **Angle→`cthm` conversion** — a single
   `monochromator_cthm(twotheta_deg) -> cos²(radians(twotheta))` helper
   used by **both** adapters to derive the backend input (Cryspy emits
   the result as `_setup_cthm`; the CrysFML fallback feeds it into the
   envelope). This is the only runtime code shared by both paths.
2. **LP envelope oracle** — a single
   `lp_factor(two_theta, k, cthm) -> hh` reference implementing
   `hh = 1 - k + k·cthm·cos²(2θ)`. It is the CrysFML fallback's runtime
   multiplier **and** the oracle a verification test uses to assert that
   Cryspy's native `_setup_K`/`_setup_cthm` output matches the same
   formula. Cryspy's runtime path stays native; the oracle guards
   against the two engines drifting without injecting EasyDiffraction
   code into Cryspy.

This keeps a single source of truth for the formula (the absorption
shared-envelope discipline of
[`model-sample-absorption.md`](../accepted/model-sample-absorption.md),
Decision 5) while honoring Cryspy's native binding.

### 6. Keep Wdt separate

`Wdt` is a peak-window/truncation setting, not beam optics. It should be
handled by a separate open issue for CrysFML peak-shape window control,
not by this ADR. No such issue file exists yet under
`docs/dev/issues/open/`; the implementing plan should file one so the
deferral is tracked rather than lost.

## Concrete files likely to change

- `src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`
  — split `CwlPdInstrument` into neutron/X-ray classes; declare the two
  descriptors and their properties on the X-ray class.
- `.../instrument/factory.py` — add `radiation_probe` to the default
  routing rules; new tags `cwl-pd-neutron` / `cwl-pd-xray`.
- `.../instrument/__init__.py` — register the new concrete classes
  (every concrete class is imported to trigger `@Factory.register`).
- `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` — pass
  `radiation_probe` into `InstrumentFactory.default_tag(...)`.
- `src/easydiffraction/analysis/calculators/cryspy.py` — emit `_setup_K`
  / `_setup_cthm` (via the shared angle→`cthm` helper), patch cached
  dicts; native LP, no runtime envelope.
- `src/easydiffraction/analysis/calculators/crysfml.py` — CFL line or the
  shared `lp_factor` post-pattern multiplier.
- A new shared module (alongside the existing calculator helpers)
  holding the two pieces from Decision 5: `monochromator_cthm` (angle→
  `cthm`, used by both adapters) and `lp_factor` (the `hh` envelope; the
  CrysFML fallback multiplier and the Cryspy-vs-formula test oracle).
- Tests/tutorials/docs referencing the `cwl-pd` tag.

## Consequences

- Neutron CW powder users do not see inactive X-ray optics fields.
- X-ray CW powder users can reproduce FullProf/Cryspy
  Lorentz-polarization inputs with discoverable names.
- The codebase gains its first `radiation_probe`-routed category, and
  the persisted CW-powder instrument tag changes from `cwl-pd` to
  probe-specific tags (a beta-acceptable breaking change).
- Existing X-ray results are unchanged until a user opts in by setting a
  non-zero polarization coefficient.
- Project persistence stores the physical monochromator angle and the
  polarization coefficient under short `_instr.*` tags; the IUCr items
  (`_pd_instr.2theta_monochr_pre`, `_diffrn_radiation.polarisn_ratio`)
  are recorded as provenance and remain report-export candidates.
- Verification remains split: optics binding must be tested separately
  from the known X-ray scattering-table discrepancy.

## Open Questions

- **Split vs. shared category.** Splitting `CwlPdInstrument` by probe is
  the first `radiation_probe` routing and the larger refactor; the
  alternative (one shared class, fields inert for neutrons via the
  `k = 0` default) is a smaller change but clutters the neutron surface
  with always-zero X-ray knobs. This ADR recommends the split because
  the fields are physically inapplicable (not merely defaulted-off) for
  neutrons; reviewers should confirm this is worth the routing
  precedent. See Alternatives.
- **Default X-ray coefficient.** Keep the default at `0.0` (pure opt-in,
  no result change) until an explicit incident-source model exists, or
  pick `0.5` for characteristic radiation now? Recommendation: keep
  `0.0` until the source model lands (see Deferred Work).

## Alternatives Considered

### Expose `setup_k` and `setup_cthm`

Rejected. These names are backend/PCR implementation details and are
not discoverable for non-programmer users.

### Keep one `CwlPdInstrument` with neutron-neutral defaults

Seriously considered — it is the smaller change and mirrors the
single-shared-category mechanism of
[`model-sample-absorption.md`](../accepted/model-sample-absorption.md)
(fields present everywhere, inert by default). Rejected as the primary
decision because the polarization coefficient is physically *zero* for
neutrons, not merely defaulted-off (sample absorption, by contrast, is
real for neutrons), so showing the knob on neutron experiments invites
meaningless tuning. Recorded as an Open Question because it avoids the
first-ever `radiation_probe` routing and the tag rename; if reviewers
judge the routing precedent too costly for two fields, this is the
fallback.

### Add a new optics category now

Rejected for now. There are only two fields and one concrete use case;
`experiment.instrument` is the natural category, and introducing an
optics abstraction before a second use case violates the
"don't introduce abstractions before a concrete second use case"
guidance in [`AGENTS.md`](../../../../AGENTS.md).

## Deferred Work

- Decide X-ray defaults once EasyDiffraction has an explicit incident
  source model (`laboratory characteristic`, `synchrotron`, etc.).
- Confirm whether `_diffrn_radiation.polarisn_ratio` can safely map to
  the EasyDiffraction polarization coefficient or whether it should stay
  under the short `_instr.*` namespace permanently.
- File the separate CrysFML peak-shape window (`Wdt`) control issue
  referenced in Decision 6.
- Extend the verification matrix after the scattering-table discrepancy
  is resolved or explicitly gated.
