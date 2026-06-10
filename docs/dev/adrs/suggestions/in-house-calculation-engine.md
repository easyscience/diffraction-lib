# ADR: In-House Diffraction Calculation Engine

## Status

Proposed.

## Date

2026-06-10

## Group

Analysis and fitting.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It proposes a
> new, optional calculation backend authored inside this repository,
> implementing the existing `CalculatorBase` contract. It deliberately
> does **not** propose replacing the external backends (`cryspy`,
> `crysfml`, `pdffit2`); see **Decision 1** and **Alternatives
> Considered**.

## Context

All diffraction pattern calculation in EasyDiffraction is delegated to
external engines: `cryspy` and `crysfml` for Bragg scattering, `pdffit2`
for total scattering. Each is wrapped behind the
[`CalculatorBase`](../../../../src/easydiffraction/analysis/calculators/base.py)
contract and selected through the switchable `experiment.calculator`
category (`CalculatorEnum` in
`datablocks/experiment/item/enums.py`; the `.type` setter swaps the
engine via `CalculatorFactory.create()`).

Relying solely on external engines has recurring costs that this project
keeps paying:

1. **Upstream blocking.** New physics frequently waits on an unreleased
   third-party change. Current example: the sample-displacement /
   transparency (FullProf `SyCos`/`SySin`) corrections are wired on the
   EasyDiffraction side but cannot be verified or shipped because they
   depend on the unreleased `cryspy` PR #46 (open issue 131; the
   verification page is in `ci_skip.txt`).
2. **Corrections with no clean home.** Sample absorption
   (Debye–Scherrer `μR`, open issue 119) is a small, well-specified,
   angle-dependent intensity factor. Investigation shows **both**
   `cryspy` and `crysfml` return only a *finished, convolved profile* to
   our layer — `cryspy.calculate_pattern` returns
   `signal_plus + signal_minus`
   (`analysis/calculators/cryspy.py:264-276`) and
   `crysfml.calculate_pattern` returns `np.asarray(y)`
   (`analysis/calculators/crysfml.py:169`). The EasyDiffraction layer
   never receives per-reflection integrated intensities, so it can only
   ever apply an *approximate* point-wise correction; the exact
   per-reflection form requires owning the convolution, i.e. owning an
   engine.
3. **Divergence and opacity.** Cross-engine verification already records
   places where `cryspy` and `crysfml` disagree with FullProf and each
   other (open issues 130, 134). Debugging a black-box backend is
   harder than debugging code we own.
4. **Reproducibility and packaging.** External engines pin native
   builds, platform wheels, and version constraints. A pure-Python /
   NumPy engine is always importable, archival, and trivially
   reproducible.

At the same time, the external engines represent person-years of
validated physics (full profile models, scattering tables, magnetic and
polarized neutron support, extinction, total scattering). Re-deriving
all of that in-house would be a multi-year effort with no near-term
payoff.

The decisive enabling fact is that **the framework is already
engine-agnostic.** `CalculatorBase` is a five-member contract (`name`,
`engine_imported`, `calculate_structure_factors`, `calculate_pattern`,
optional `last_powder_refln_records`). A new engine registers with
`@CalculatorFactory.register`, declares a `CalculatorEnum` tag and its
`TypeInfo`/`Compatibility`/`CalculatorSupport`, and is imported in
`analysis/calculators/__init__.py`. Nothing in the fit loop, minimizers,
CIF I/O, or display needs to change. The cost of a new engine is
**entirely the physics inside `calculate_pattern`**, not its
integration.

## Decision (proposed — direction, not yet locked)

Build an **optional, in-repository calculation engine** that implements
`CalculatorBase`, grown **incrementally and verification-gated**, with a
deliberately bounded initial scope.

1. **Own the core; keep the backends for the frontier.** The native
   engine targets the common case — constant-wavelength and
   time-of-flight **neutron powder Bragg** Rietveld — first. It is
   **not** a replacement for `cryspy`/`crysfml`/`pdffit2`, which remain
   first-class backends for everything the native engine does not yet
   cover (magnetic, polarized, single-crystal extinction, total
   scattering, advanced profiles). Two code paths coexisting is an
   accepted, intended consequence, not a defect.

2. **Implement the existing contract; change no framework code.** The
   engine is a `CalculatorBase` subclass registered through
   `CalculatorFactory`, a new `CalculatorEnum` member, and one import in
   `analysis/calculators/__init__.py`, governed by the existing
   [Factory Contracts](../accepted/factory-contracts.md),
   [Factory Tag Naming](../accepted/factory-tag-naming.md),
   [Enum-Backed Closed Value Sets](../accepted/enum-backed-closed-values.md),
   and [Selector Families](../accepted/selector-families.md) (the
   calculator is a *backend selector*) ADRs. Being pure Python/NumPy, it
   is always `engine_imported = True` and therefore always available via
   `CalculatorFactory._supported_map`.

3. **Opt-in until it earns the default.** The native engine ships
   opt-in. `CalculatorFactory._default_rules` keeps `cryspy` (Bragg) and
   `pdffit` (total) as defaults. The engine becomes a candidate default
   **only** for an experiment-type subset on which it matches the
   reference codes within published tolerances (Decision 5).

4. **MVP calculation loop.** The first slice computes, for CWL neutron
   powder, one phase:
   `F(hkl) = Σ_j b_j · occ_j · exp(2πi h·r_j) · DW_j` → `|F|²` →
   `× (Lorentz–polarization × multiplicity)` → place peaks at the
   reflection `2θ_hkl` → convolve with a pseudo-Voigt → sum → add the
   existing EasyDiffraction background. `calculate_structure_factors`
   and `last_powder_refln_records` are implemented so the reflection
   table and structure-factor path work identically to the existing
   backends.

5. **Every feature is verification-gated.** No native-engine feature is
   "done" until a page under `docs/docs/verification/` compares it to
   `cryspy`/`crysfml`/FullProf within explicit tolerances, per the
   [Test Suite and Validation Strategy](../accepted/test-suite-and-validation.md).
   The existing cross-engine harness is the regression net; the native
   engine is added as another column.

6. **The engine is the right home for owned corrections.** Corrections
   currently blocked on or awkward in the backends — sample absorption
   (`μR`, issue 119), the exact per-reflection `SyCos`/`SySin`
   (issue 131), and basic preferred orientation — are implemented
   **inside** the native engine with the physically exact
   per-reflection math, since the engine owns the integrated
   intensities before convolution. (A backend-agnostic *point-wise*
   absorption approximation in the data layer remains available for the
   external backends and is orthogonal to this ADR.)

## Consequences

### Positive

- New physics no longer waits on third-party releases.
- Corrections like absorption gain an exact, owned implementation rather
  than a point-wise approximation.
- Engine disagreements become debuggable in our own code, against our
  own verification harness.
- Pure-Python/NumPy: always importable, archival, reproducible, and a
  strong teaching/onboarding surface.
- Zero framework churn — the engine slots into existing factory,
  selector, fit, CIF, and display machinery.

### Negative / cost

- A second (eventually third) calculation code path to maintain
  alongside the external backends, indefinitely.
- Matching reference codes to tight tolerance (e.g. profile models to
  <1% of FullProf) is the genuine, large cost; peak-shape physics (TCH
  pseudo-Voigt, FCJ asymmetry, TOF back-to-back exponentials) is where
  the effort concentrates.
- Scattering data (neutron scattering lengths, X-ray form factors) must
  be sourced — reused, vendored, or depended upon — a dependency
  decision (Open Questions).
- A naive NumPy implementation will be slower than the optimized native
  backends until profiled and vectorized; performance is its own work
  stream.
- Risk of scope creep toward full parity; the bounded scope
  (Decision 1) must be actively defended.

## Alternatives Considered

| # | Alternative | Verdict |
| --- | --- | --- |
| A | **Status quo** — depend entirely on `cryspy`/`crysfml`/`pdffit2`. | Rejected. Perpetuates upstream blocking (issue 131) and leaves corrections like absorption (issue 119) without an exact home. |
| B | **Fork or vendor an existing engine** (e.g. a `cryspy`/`crysfml` subset). | Rejected. Inherits the backend's complexity, build system, and licensing while still not being code we understand end to end. |
| C | **In-house engine targeting full parity** with the external backends. | Rejected. Multi-year effort; the long tail (magnetic, polarized, extinction, total scattering) has poor cost/benefit and is well served by the backends. |
| D | **In-house core + keep backends for the frontier** (this ADR). | **Chosen.** Owns the common 80% (neutron powder Rietveld), keeps backends for the rest, reuses all existing framework. |
| E | **Only point-wise corrections in the data layer**, no real engine. | Insufficient as a strategy. Solves the immediate absorption case approximately but does not generalize to structure factors or profiles, and does not remove upstream blocking. Complementary, not a substitute. |

## Deferred Work / Open Questions

1. **Scattering-data source.** Neutron scattering lengths and X-ray form
   factors: reuse `cryspy`'s tables, vendor a small dataset, or add a
   dependency (e.g. `periodictable`). This needs an explicit dependency
   decision per [`AGENTS.md`](../../../../AGENTS.md) §Architecture before
   any package is added.
2. **Engine tag / `CalculatorEnum` member name.** Candidates:
   `EASYDIFFRACTION` / `'easydiffraction'`, `NATIVE` / `'native'`,
   `EASY` / `'easy'`. To be fixed under
   [Factory Tag Naming](../accepted/factory-tag-naming.md).
3. **Profile-model coverage order.** Which peak shapes to implement and
   in what order (CWL pseudo-Voigt first; then TCH/FCJ; then TOF
   Jorgensen / Jorgensen–Von Dreele).
4. **Default-promotion threshold.** The concrete tolerance and
   experiment-type subset at which the native engine becomes a candidate
   default (Decision 3).
5. **Performance strategy.** Pure NumPy first; whether/when to add an
   accelerator (Numba, Cython) — itself a dependency decision.
6. **Explicitly out of initial scope.** Magnetic and polarized neutron
   scattering, single-crystal extinction/twinning, and total scattering
   (PDF) remain backend-only until separately revisited.
7. **Relationship to the point-wise absorption correction.** Whether to
   ship the backend-agnostic point-wise `A(2θ)` correction (issue 119)
   first as an independent change, and let the native engine later
   supersede it with the exact per-reflection form.
