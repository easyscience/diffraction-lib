# ADR: Model Sample Absorption (Debye–Scherrer, μR)

## Status

Accepted.

## Date

2026-06-12

## Group

Experiment model.

## Context

This ADR follows the conventions in
[`AGENTS.md`](../../../../AGENTS.md).

The calculators (`cryspy`, `crysfml`) currently apply **no**
sample-absorption correction. For a cylindrical sample in Debye–Scherrer
geometry the transmission through the sample is an angle-dependent
factor that attenuates low-angle peaks more than high-angle peaks;
omitting it leaves an angle-dependent intensity residual that scales
with the sample's μR (linear absorption coefficient × radius).

This is not hypothetical. The verification reference
`pd-neut-cwl_tch-fcj_lab6` was refined in FullProf with **μR = 0.7**;
the unmodelled correction is the _entire_ intensity residual on the
companion `pd-neut-cwl_tch-fcj_abs_lab6` page (≈5 % profile difference),
while the μR = 0 page passes to corr 0.9999. See
[issue #119](../../issues/open/highest_model-sample-absorption-debye-scherrer-r.md).

### What the three reference sources provide

**FullProf** splits absorption into a refineable **magnitude** and a
**correction type**, on two different axes:

- **CW (and symmetric θ–2θ flat plate):** `muR` on the `.pcr` Lambda
  line — a single value (μ·R). In the LaB₆ reference it is **fixed**
  (the Lambda line carries no refinement codeword), confirming that
  absorption is typically entered as a known constant, not refined. A
  `2nd-muR` field on the same line models a second coaxial cylinder (the
  sample container / capillary wall); `Cthm` and `Rpolarz` on that line
  are **polarization**, not absorption, and are out of scope here.
- **TOF:** `Iabscor` selects the correction _form_ — `1` flat plate ⟂
  incident beam, `2` cylindrical, `3` exponential `A = exp(−ABS·λᶜ)`.
  TOF absorption is wavelength-dependent, not a pure function of 2θ.

**CrysFML08** (`Src/CFML_Powder/Pow_Lorentz_Absorption.f90`) already
implements the CW formulas in Fortran:

- `Lorentz_abs_CW(sinth, costh, postt, tmv, …, ilor, cabs, …)` with
  `tmv = μR`, `ilor` = geometry (`DBS`, `BB`, `TBG`, `TFX`, `FILMS`…)
  and `cabs ∈ {HEWAT, LOBANOV}`.
- `Powder_Lorentz_IntegInt_CW(…, muR, …)` — the bare Hewat form.

**However**, these routines are **not wrapped** in CrysFML's
`PythonAPI/`, and the high-level entry our backend actually calls
(`cw_powder_pattern_from_dict`) computes a plain Lorentz factor
`0.5/(sin²θ·cosθ)` with no absorption term. So the issue's claim that
absorption is "reachable via `Lorentz_abs_CW` through pycrysfml" is
**not true today** — it would require upstream wrapping or an upstream
call-site change we do not control.

**cryspy** has **no absorption code at all** (only Debye–Waller and
sphere _extinction_, which are different physics). CW intensity is
assembled in `procedure_rhochi/rhochi_pd.py` as
`0.5 · scale · Lorentz(θ) · |F|² · mult`, with no slot for an A(θ)
factor.

### Consequence of the source survey

Neither backend can apply the correction internally without changes we
do not own. The only way to get **identical** results across both
calculators is to compute A(θ) **ourselves in EasyDiffraction** and
apply it to the calculated pattern. This makes absorption a
**calculator-independent** correction — unlike `extinction`, which is
threaded into cryspy's own dict and is therefore `cryspy`-only.

### CIF dictionary support (`tmp/iucr-dicts`)

There is **no** standard data name for μR or for the Hewat coefficient.
The standard items cover the _physical provenance_ only:

| Quantity                  | Standard CIF item                                             | Units |
| ------------------------- | ------------------------------------------------------------- | ----- |
| Linear absorption μ       | `_exptl_absorpt.coefficient_mu`, `_pd_char.atten_coef_mu_*`   | mm⁻¹  |
| Sample radius / thickness | `_pd_spec.size_axial/_equat/_thick`                           | mm    |
| Sample shape              | `_pd_spec.shape` ∈ {`cylinder`, `flat_sheet`, `irregular`}    | code  |
| Correction type           | `_exptl_absorpt.correction_type` (incl. `cylinder`, `sphere`) | code  |
| Beam path                 | `_pd_spec.mount_mode` ∈ {`reflection`, `transmission`}        | code  |

So the refineable μR itself needs a **project-namespaced**
(`_easydiffraction_absorption.*`) tag, with the standard items available
later as optional provenance (see Deferred Work).

### Evidence from the FullProf example suite

A survey of all 68 `.pcr` files shipped with FullProf (`Examples/`)
shows that **every** absorption example — CW and TOF — is **cylindrical
(Debye–Scherrer)**; not one uses flat-plate or exponential absorption,
and the container term is never used:

- **CW (cylindrical `muR`):** `dy*`, `DyMnGe*`, `cuf1k`, `hocu`,
  `si3n4r`, `sin_3t2` — μR ∈ {0.068, 0.15, 0.40, 1.28}, all **fixed**
  (no refinement codeword on the Lambda line). Note μR reaches **1.28**,
  slightly past Hewat's nominal ≈1.0 validity — the practical motivation
  for the Lobanov form later.
- **TOF (`Iabscor`):** `Ceo2_PEARL`, `nac-osiris(n)`, `hrpd`, `arg_si`,
  `cecual`, `cecoal`, `lamn_pol` — **all `Iabscor = 2` (cylindrical)**,
  with `ABSCOR1` non-zero and **refined** (non-zero codewords).
- **Never observed:** `Iabscor = 1` (flat plate), `Iabscor = 3`
  (exponential), or a non-zero `2nd-muR` (container) in any file.

Two design consequences:

1. **Ship a single cylindrical type now.** The cylinder is the only
   geometry the reference toolchain actually exercises, so Phase 1
   builds `none` + `cylinder-hewat` only; everything else becomes a
   documented future extension (§Deferred Work) that plugs into the same
   switchable category without rework.
2. **Refineable, default-fixed.** CW practice fixes `muR`; TOF practice
   refines it. So `mu_r` is a normal refineable `Parameter` but ships
   `free = False` (matching the CW reference and the Biso degeneracy),
   not a constant.

## Decision

### 1. Add a switchable `absorption` category on the experiment

Introduce `experiment.absorption`, mirroring `experiment.extinction`: a
`SwitchableCategoryBase` whose concrete classes are registered with an
`AbsorptionFactory`, gated by `Compatibility` and `CalculatorSupport`.
It follows
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md):

```python
experiment.absorption.type             # writable selector (str)
experiment.absorption.show_supported() # supported types, active starred
```

The owner exposes only `experiment.absorption` and a private
`_swap_absorption` hook (Family A: the hook **replaces the category
instance** when `type` changes), exactly as `extinction` does today.

**Owner scope — Bragg powder experiments only.** The category is
attached only when the experiment type is `sample_form = powder` **and**
`scattering_type = bragg` (the cryspy/crysfml Bragg backends). Total-
scattering / pdffit experiments **do not expose `experiment.absorption`
at all** — there is no `none` instance, no `_absorption.*` block, and
accessing the attribute raises as for any absent category. This mirrors
`extinction`, which is attached only for single-crystal experiments and
is simply absent otherwise; attachment is governed by the same
`Compatibility` gate, not by a runtime no-op. Consequently the `none`
type's calculator list is `cryspy, crysfml` (the Bragg backends) and
deliberately excludes `pdffit`.

### 2. Application point — a pointwise envelope on the calculated pattern

Because A(θ) is a **slowly-varying smooth envelope** of sin²θ (its
fractional change across one peak FWHM is ≪ 1 for any realistic μR),
applying it per-reflection vs. pointwise to the summed pattern differs
only at second order in (FWHM · dA/dθ) — negligible. We therefore apply
it once, after pattern assembly, in **both** backends:

```
y_corrected(2θ_i) = A(θ_i) · y_calc(2θ_i)
```

This is a single shared helper
(`analysis/calculators/absorption.py::factor(two_theta, params)`) called
from the post-calculation step of both `cryspy.py` and `crysfml.py`. The
two backends thus stay bit-for-bit consistent on the absorption term,
and the helper is unit-testable in isolation against FullProf output
(validated to 4 decimals in the issue).

### 3. Supported types — the taxonomy

The `type` selector lists factory tags gated by `Compatibility` (sample
form, beam mode, scattering type, radiation) and `CalculatorSupport`.
**Phase 1 builds only the first two rows;** the rest are the planned
extension surface, designed here so they later plug into the same
category by registering a class (see Deferred Work).

| Tag                | Beam mode | Sample form | Radiation     | Calculators     | Parameters      | Status      |
| ------------------ | --------- | ----------- | ------------- | --------------- | --------------- | ----------- |
| `none`             | any       | any         | neutron, xray | cryspy, crysfml | —               | **Phase 1** |
| `cylinder-hewat`   | CWL       | powder      | neutron, xray | cryspy, crysfml | `mu_r`          | **Phase 1** |
| `cylinder-lobanov` | CWL       | powder      | neutron, xray | cryspy, crysfml | `mu_r`          | future      |
| `tof-cylinder`     | TOF       | powder      | neutron       | cryspy, crysfml | `mu_r` (λ-dep.) | future      |
| `flat-plate`       | CWL       | powder      | neutron, xray | cryspy, crysfml | `mu_t`          | future      |
| `tof-exponential`  | TOF       | powder      | neutron       | cryspy, crysfml | `coeff`, `exp`  | future      |

Notes:

- `none` is the **default** (A ≡ 1). The category exists for every
  **Bragg powder** experiment (see §1 "Owner scope") so the user can
  discover and switch it on via `show_supported()`; opting out is
  `type = 'none'`, not deleting the category. Total-scattering / pdffit
  experiments do not get the category at all (not even `none`), so the
  `any` in the `none` row's beam-mode/sample-form columns is bounded by
  that owner gate — it means "any Bragg-powder beam mode", not literally
  every experiment type.
- **Why a single built type is correct now:** the FullProf example suite
  uses only cylindrical absorption (§"Evidence from the FullProf example
  suite"), and our sole verification reference is CW cylindrical (LaB₆,
  μR = 0.7). Building `cylinder-hewat` alone closes the known gap with a
  tested oracle; the others would ship untested physics. This also
  respects [`AGENTS.md`](../../../../AGENTS.md) §Architecture ("don't
  introduce abstractions before a concrete second use case") — but the
  switchable-category contract is still required even for a single
  implementation (as `extinction` is today with only `becker-coppens`),
  which is what keeps the extension surface free.
- Radiation is **not** a discriminator for the cylindrical geometric
  envelope — the Hewat/Lobanov constants depend on geometry, not on
  neutron vs X-ray. X-ray simply tends to larger μ; the same formula
  applies. Both are supported.
- The future rows are designed (tags, parameters, CIF) but **not
  built**. They all share the stable category/swap contract; only the
  TOF rows additionally need a new calculation path — see §3a.

### 3a. Stable category contract vs. per-mode calculation contract

These two contracts are intentionally separate, so the switchable
category can be extended without churn while the calculation layer grows
only as physics demands:

- **Category/swap contract — stable across _all_ types.** Every type
  (CWL or TOF, Phase 1 or future) is a class registered on
  `AbsorptionFactory`, selected through `experiment.absorption.type`,
  swapped by the single `_swap_absorption` hook. Adding a type never
  changes the category, the hook, the selector surface, or the CIF
  identity tag. This is what the "no rework" claim refers to.
- **Calculation contract — per beam mode.** _How_ a type turns its
  parameters into an applied correction is **not** uniform:
  - **CWL types** (`cylinder-hewat`, `cylinder-lobanov`, `flat-plate`)
    share the §2 helper `factor(two_theta, params) → A(2θ)`, applied as
    a pointwise 2θ envelope. Adding a CWL form is just another branch in
    that helper.
  - **TOF types** (`tof-cylinder`, `tof-exponential`) are
    wavelength-dependent: at fixed scattering angle a TOF bin mixes
    wavelengths, so a pure A(2θ) envelope is wrong. They will need a
    distinct `factor_tof(...)` application path keyed on λ (or d-spacing
    / TOF). Phase 1 does **not** build this path; it is added with the
    first TOF type, behind the same category/swap contract.

So adding a TOF form leaves the category contract untouched (per the
first bullet) but **does** extend the calculation layer (a new
application path) — the Deferred Work note reflects exactly this split.

### 4. The μR parameter

The single refineable/settable quantity is **`mu_r`** (μ·R), matching
FullProf's `muR` and CrysFML's `tmv`. It is a `Parameter`
(`RangeValidator(ge=0.0)`, default `0.0`), **free=False by default**
(absorption is normally fixed, per the LaB₆ reference). Storing μ and R
separately is rejected (see Alternatives); they can be added later as
read-only provenance (Deferred Work).

**Out-of-range policy (boundary user input — no silent failure).** The
Hewat expansion is validated only to μR ≲ 1.5, yet `RangeValidator`
alone would silently evaluate it at any μR ≥ 0. Phase 1 therefore adds
an explicit, documented policy on `cylinder-hewat`:

- **Hard floor only in the validator:** `RangeValidator(ge=0.0)` — no
  hard upper bound. A hard ceiling is rejected because legitimate real
  examples reach μR = 1.28 (dy*, DyMnGe*; §"Evidence"), and a
  characterised sample may sit slightly higher; erroring would block
  valid use.
- **Warn above the validated ceiling:** when `mu_r` is set (or refined)
  above **1.5**, the category emits a single `log.warning` stating that
  μR exceeds the Hewat-validated range and that the (deferred)
  `cylinder-lobanov` form should be used once available. The pattern is
  still computed (extrapolated), so workflows do not break, but the user
  is never silently handed an out-of-range result.
- This warn-not-fail choice is the boundary-input handling required by
  [`AGENTS.md`](../../../../AGENTS.md) §Project Context, applied at the
  public-API edge; the 1.5 threshold is a single named constant so the
  future `cylinder-lobanov` type can raise/redirect coherently.

`flat-plate` uses `mu_t` (μ·thickness); the TOF exponential form uses
`coeff` and `exp` (`A = exp(−coeff·λ^exp)`).

### 5. Equations

**Hewat** (cylinder, validated to 4 decimals vs FullProf; fit range μR ≲
1.5):

```
A(θ) = exp( −(1.7133 − 0.0368·sin²θ)·μR + (0.0927 + 0.375·sin²θ)·μR² )
```

**Lobanov–Alte da Veiga** (cylinder, extends to μR ≈ 10 via a branch at
μR = 3; `s ≡ sinθ`):

```
μR ≤ 3:
  k1 = (25.99978 − 0.01911·s^0.25)·exp(−0.024514·s) + 0.109561·√s − 26.0456
  k2 = −0.02489 − 0.39499·s + 1.219077·s^1.5 − 1.31268·s² + 0.871081·s^2.5 − 0.2327·s³
  k3 =  0.003045 + 0.018167·s − 0.03305·s²
  A  = exp( −((k3·μR + k2)·μR + k1)·μR )      (normalised; k0 = 1.697653)

μR > 3:
  A  = k7 + (k4 − k7) / (1 + k5·(μR − 3))^k6   (k4…k7 polynomials in s)
```

(Lobanov constants transcribed from CrysFML08
`Pow_Lorentz_Absorption.f90`; the implementation will copy them verbatim
and unit-test against that source.)

**Flat plate, symmetric θ–2θ** (μt = μ·thickness):

```
A(θ) = exp( −2·μt / sinθ )            # transmission, symmetric reflection
```

**TOF exponential** (deferred; per FullProf `Iabscor = 3`):

```
A(λ) = exp( −coeff · λ^exp )
```

### 6. User-facing API

```python
# Discover what is available for this experiment (Phase 1)
experiment.absorption.show_supported()
# -> none (*), cylinder-hewat

# Turn on the cylindrical Debye–Scherrer correction
experiment.absorption.type = 'cylinder-hewat'
experiment.absorption.mu_r = 0.7          # fixed value from the beamline

# (Optional) refine it — off by default because it is near-degenerate
# with Biso and scale
experiment.absorption.mu_r.free = True
```

`experiment.absorption.type = 'none'` restores A ≡ 1.

### 7. CIF mapping

Project-namespaced block, one identity tag plus the magnitude:

```
_absorption.type   cylinder-hewat
_absorption.mu_r   0.7
```

IUCr-aligned export (per
[`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md))
uses `_easydiffraction_absorption.type` / `.mu_r`, and may additionally
emit the standard provenance `_exptl_absorpt.correction_type cylinder`.
`flat-plate` writes `_absorption.mu_t`; TOF forms write their own
fields. The `_absorption.type` tag is the single source of truth for the
active type (no owner-level selector tag), per
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

### 8. Cost

A(θ) is one vectorised `exp` over the 2θ grid per pattern evaluation —
microseconds, utterly dominated by the diffraction calculation itself.
Refining `mu_r` adds one parameter; each fit iteration recomputes the
envelope at negligible cost. There is no per-reflection loop and no
backend round-trip.

## Consequences

- **Closes the LaB₆ absorption residual.** The
  `pd-neut-cwl_tch-fcj_abs_lab6` verification page becomes the
  acceptance test: with `cylinder-hewat`, `mu_r = 0.7` it should reach
  the same corr as the μR = 0 page.
- **Calculator-consistent by construction.** Both backends call the same
  helper, so the absorption term can never drift between `cryspy` and
  `crysfml`. New backends inherit it for free.
- **No upstream dependency.** We do not wait on cryspy or CrysFML Python
  wrappers; nothing in `pyproject.toml` changes.
- **New switchable category to wire.** Owner attribute, `_swap_*` hook,
  factory, `__init__.py` registration, enums, CIF round-trip, and the
  `none` default — the full
  [`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  surface. Mitigated by mirroring `extinction` closely.
- **Degeneracy is documented, not hidden.** `mu_r.free = False` by
  default; help text warns that refining μR together with Biso/scale
  correlates strongly. Explicit modelling is preferred precisely so Biso
  is not biased by soaking up absorption.
- **Pointwise envelope is an approximation** (second order in
  FWHM·dA/dθ). Validated to 4 decimals against FullProf; acceptable and
  documented.

## Alternatives Considered

1. **Per-reflection multiply inside each backend.** More "correct" in
   principle, but cryspy has no slot (would need to patch its intensity
   loop) and crysfml's routine is in unwrapped Fortran. Two divergent
   code paths, an upstream dependency, and no measurable accuracy gain
   over the envelope. Rejected.
2. **Flat instrument parameter `instrument.mu_r`** (as the issue
   sketches). Simpler, but it cannot carry a correction-type selector
   (Hewat vs Lobanov vs flat-plate vs TOF), breaks the
   switchable-category uniformity the project standardised on, and has
   no natural home for TOF forms. Rejected in favour of the switchable
   category.
3. **Store μ and R separately, compute μR.** Matches the CIF items, but
   the two inputs are perfectly correlated for the correction and only
   their product matters; FullProf and CrysFML both parametrise by the
   product. Storing them separately invites a confusing two-knob UI for
   one degree of freedom. Deferred to optional provenance.
4. **Let Biso absorb it.** The status quo. Biases the thermal parameters
   and fails the `_abs_` verification page. Rejected — this ADR exists
   to avoid exactly that.

## Deferred Work

All of these are designed into the taxonomy and CIF tags above but **not
built in Phase 1**. Two contracts must be kept separate (see §3a "Stable
vs. calculation contract"):

- **Category/swap contract (stable for all future types):** each is a
  new class registered on the same `AbsorptionFactory`, gated by
  `Compatibility`/`CalculatorSupport`, with **no change to the category,
  the `_swap_absorption` hook, or the selector surface**.
- **Calculation contract (per beam mode):** CWL types reuse the shared
  2θ helper `factor(two_theta, params)`. **TOF types do not** — they
  require a separate wavelength-aware application path (§3a), so adding
  a TOF form _does_ extend the calculation layer even though it leaves
  the category/swap contract untouched.

None appears in the FullProf example suite (only the cylinder does), so
none is urgent; each should land **with a verification dataset**, not on
spec alone.

- **`cylinder-lobanov`** — extends valid μR to ≈10 (branch at μR = 3).
  Real CW neutron examples reach μR = 1.28, past Hewat's ≈1.0 validity,
  so this is a genuine eventual want, not hypothetical. Add when a
  high-μR reference exists; Hewat alone meets the current LaB₆ case.
- **TOF absorption** (`tof-cylinder`, `tof-exponential`): the
  λ-dependent forms (FullProf `Iabscor = 2 / 3`). The pointwise-2θ
  envelope does not transfer directly — needs its own application path.
  FullProf TOF examples all use `Iabscor = 2` (cylindrical) and refine
  it, so `tof-cylinder` is the natural next target.
- **`flat-plate`** (CW symmetric θ–2θ, `mu_t`) and other geometries
  (`Iabscor = 1`): present in the file formats but used by **zero**
  FullProf examples — lowest priority.
- **Optional (μ, R) provenance** mapped to
  `_exptl_absorpt.coefficient_mu` and `_pd_spec.size_*`, read-only, with
  `mu_r` remaining the single refineable knob.
- **Container / `2nd-muR`** (sample-in-holder coaxial cylinder): never
  used in any FullProf example; revisit only if a case needs it.
- **Single-crystal absorption** (different formalism entirely).
