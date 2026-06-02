# ADR: Automatic Line-Segment Background Estimation

**Status:** Proposed **Date:** 2026-06-01

## Group

Experiment model.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It adds one new
> dependency, `pybaselines` (§4). The user approved it directly in the
> drafting conversation, which is the explicit approval
> [`AGENTS.md`](../../../../AGENTS.md) → **Architecture** requires. The
> implementation plan must still **name `pybaselines` explicitly** in
> its dependency-changing step (for example a
> `P1.x — Add pybaselines dependency` line): `/draft-impl-1` and
> `/draft-impl-2` are authorized to edit `pyproject.toml`, `pixi.toml`,
> and `pixi.lock` only by the accepted plan text naming the package, not
> by this drafting thread's approval alone. No other deliberate
> exception to those instructions is taken.

## Context

A line-segment background is a set of `(x, intensity)` control points
that are linearly interpolated across the pattern
([`line_segment.py:147`](../../../../src/easydiffraction/datablocks/experiment/categories/background/line_segment.py)).
Today the user must supply every point by hand —
`experiment.background.create(id='1', x=12.0, y=85.0)` in Python, or a
`_pd_background.*` loop in CIF. With no points, the model evaluates to
zero
([`line_segment.py:175`](../../../../src/easydiffraction/datablocks/experiment/categories/background/line_segment.py)).
There is no automatic estimation anywhere in the library.

Hand-placing points well is tedious and easy to get wrong, and the
audience is scientists who are often not programmers. Two rules make it
genuinely hard:

1. **Points must flank peaks, not sit on them.** A point placed on a
   peak shoulder pulls the interpolated background up _into_ the peak
   and steals intensity from the very quantity being refined.
2. **In strongly overlapped regions there is no true background point.**
   The pattern never returns to baseline between dense reflections, so
   the valley floor sits _above_ the real background. Naively picking
   local minima there inflates the background and biases integrated
   intensities low.

A third complication is specific to constant-wavelength (CWL) data and
to _when_ an automatic background is typically wanted. CWL peak width is
**not constant** — FWHM grows with angle (the Caglioti
`U·tan²θ + V·tanθ + W` trend) — so a single "peak width" is already an
approximation across the pattern. Worse, an automatic background is
usually reached for at the very **first** modelling step, when the
peak-profile parameters (`U`, `V`, `W` on `self._parent.peak`) are only
roughly set. Any width taken from that unrefined resolution model would
be badly wrong exactly when the feature is first used.

The resolution of that timing problem is to never derive the width from
the _model_: the **measured pattern already contains the true peak
widths**, and those are independent of how well the profile parameters
are set. Measuring the width directly from `data.intensity_meas` is
therefore reliable from step one. It also reframes the iterative
workflow the user described — _estimate a background, refine the rest of
the model, then re-estimate_ — correctly: re-running does **not**
improve the measured peak widths (the data does not change). What it
gains is the **fitted model**. After at least one calculation,
`data.intensity_calc` (the total model) and `data.intensity_bkg` are
populated
([`bragg_pd.py:574`](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py),
[`bragg_pd.py:582`](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py)),
so the peak-only model `intensity_calc − intensity_bkg` becomes
available. Subtracting it from the measured pattern removes the fitted
peaks while keeping the background, giving a peak-subtracted pattern on
which a second pass estimates the absolute background and places better
anchors — especially across overlapped clusters the data alone cannot
resolve. (§5 gives the exact array and shows why the emitted heights are
absolute background values, not residual corrections.) So re-estimation
is a first-class workflow, not just a convenience.

This is a well-studied problem in powder diffraction. The classic
peak-clipping methods (Sonneveld & Visser, 1975; Brückner, 2000) and the
SNIP algorithm estimate a smooth background _underneath_ the peaks, even
where the data never reaches it. The de-facto Python library is
`pybaselines` (50+ algorithms; its `classification` family also returns
a boolean mask of which points are baseline); notably, **GSAS-II's
automatic fixed-point background (`autoBkgCalc`) is a thin wrapper
around `pybaselines`** feeding exactly this fixed-point model.

Everything an estimator needs is already reachable from the category.
The existing `_update()` reads the live pattern through the parent
([`line_segment.py:172`](../../../../src/easydiffraction/datablocks/experiment/categories/background/line_segment.py)):
`self._parent.data` exposes `data.x`, `data.intensity_meas`,
`data.intensity_calc`, and `data.intensity_bkg` as NumPy arrays over the
**active** points — excluded regions are already filtered out
([`bragg_pd.py:539`](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py),
[`bragg_pd.py:679`](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py)).
The parent also carries the experiment-type axes
(`self._parent.type.beam_mode.value`).

The produced points are first-class and need no new persistence: each
point's `intensity` is a `Parameter` with a `free` flag
([`variable.py:447`](../../../../src/easydiffraction/core/variable.py))
persisted through the existing free/fixed CIF encoding
([`free-flag-cif-encoding.md`](../accepted/free-flag-cif-encoding.md)),
and the `_pd_background.*` loop already round-trips them. So an
auto-estimator's only job is to compute good `(x, intensity)` values and
write them into the collection; the user then reviews them and chooses,
per point, fixed or refinable.

`background` is a Family-A switchable category
([`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md));
`LineSegmentBackground` is the default type
([`factory.py`](../../../../src/easydiffraction/datablocks/experiment/categories/background/factory.py)).
Point-based estimation is specific to the line-segment model
(`ChebyshevPolynomialBackground` has coefficients, not points), so the
new behaviour attaches to the concrete line-segment class, not to the
shared switchable surface.

## Decision

### 1. A user-invoked `auto_estimate()`, never automatic

Add a public method to `LineSegmentBackground`:

```python
def auto_estimate(
    self,
    *,
    method: str = 'auto',
    width: float | None = None,
    smoothness: float | None = None,
    n_points: int | None = None,
    use_model: bool = True,
) -> None:
    """Detect background control points from the measured pattern."""
```

A bare `experiment.background.auto_estimate()` must work — no required
arguments, no manual tuning (§3 makes that real). It reads
`self._parent.data`, computes points, and writes them into the
collection. It is the seed of the iterative loop in §5, not a one-shot.
It returns `None` (it fills the collection, like other category
mutators) and logs a one-line summary — chosen method, width, and point
count — for the review step.

It is **explicitly on-demand**, never run inside `_update()` or at
calculation time. The library does not silently estimate or re-estimate
its own background while fitting — that would contradict the project's
"no runtime self-validation of generated output" stance and would
surprise a user who has hand-tuned points.

The method is discoverable via the category's `help()` per
[`help-discoverability.md`](../accepted/help-discoverability.md).
`method` is a keyword argument validated against a closed
`BackgroundEstimatorMethodEnum` with exactly four Phase-1 members —
`auto`, `snip`, `arpls`, `fabc` — per
[`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md).
`auto` is the default and a stable alias for "let the library choose";
in Phase 1 it resolves to the single default method, `arpls` (§3). The
argument selects an algorithm for _this call only_ — it is not a
persisted descriptor and appears in no CIF block; the generated points
are the sole persisted output. The remaining overrides are continuous
numbers or booleans. No `**kwargs` (per
[`AGENTS.md`](../../../../AGENTS.md) → **Code Style**).

### 2. Two-stage algorithm: estimate the curve, then place sparse anchors

The hard problem (overlap) and the easy problem (anchor placement) are
decoupled.

**Stage 1 — a peak-insensitive background curve `B(x)`.** Estimate a
smooth background over the whole grid using a method that reconstructs
the curve _under_ the peaks (peak-clipping / penalised least squares),
not the raw valley floor. This is what makes overlap regions correct:
even where the data never returns to baseline, `B(x)` is extrapolated
from the surrounding clipped trend.

**Stage 2 — thin `B(x)` to a minimal set of line segments.** Reduce the
dense curve to a sparse `(x, intensity)` set with
Ramer–Douglas–Peucker-style polyline simplification: many anchors where
the background curves, few on flat stretches, with the first and last
grid points always kept so interpolation covers the full range.
Optionally cap the count at `n_points`.

Two invariants protect peak intensities:

- **Anchor heights come from `B(x)`, never from the raw data.** This is
  the single most important rule against intensity inflation: even when
  an anchor lands in a shallow valley whose floor is above the true
  background, its height is the de-peaked `B(x)` value.
- **Each anchor's height is clipped to
  `0 ≤ intensity ≤ intensity_meas`** — always against the original
  measured intensities, in both the data-only and model-guided paths
  (never against the peak-subtracted array). A background cannot exceed
  the observation, and (for these probes) cannot be negative.

**Overlap is handled by abstention, stated honestly.** Inside a dense
multiplet there is no information to place a true background point from
the data alone, so the estimator deliberately does **not** force one
there — one segment spans the cluster, interpolating across it using the
de-peaked `B(x)` at the cluster's flanks. (A model-guided re-run, §5,
can do better because it knows where the peaks are.)

### 3. Auto-parameterization: adapt to the dataset and the experiment type

Every algorithm in Stage 1 keys off one length scale — the peak width in
data points. A fixed default (e.g. a 50-point window) is right for one
dataset and wrong for the next, because CWL 2θ steps, TOF time bins, lab
vs synchrotron resolution, and neutron vs X-ray all differ.
`auto_estimate()` therefore derives its parameters at call time:

- **Peak width `W` (in points) is measured from the data, not the
  model.** `scipy.signal.find_peaks` on the most prominent peaks then
  `scipy.signal.peak_widths`. Because CWL FWHM grows with angle
  (§Context), `W` is taken as a robust **upper** estimate (a high
  percentile of the measured widths), so the Stage-1 window/smoothness
  is large enough to clear the broadest peaks; mildly over-smoothing the
  background under the sharp low-angle peaks is harmless, since the
  background is smooth there anyway. The peak/resolution model
  (`self._parent.peak`) is **not** used by default — at the typical
  first-use moment its `U/V/W` are unrefined and would mislead. A future
  opt-in could consult it once refined, but the data-derived width is
  correct from step one and is the default.
- **Noise σ** — a robust estimate from the median absolute deviation of
  the second difference of the intensities (insensitive to peaks). Feeds
  the classification threshold and the RDP tolerance (`c · σ`), so the
  number of anchors follows the real background curvature rather than a
  magic count.
- **Window / smoothness / threshold** — derived from `W`, σ, and the
  point count `N`, then handed to the backend (§4).
- **Algorithm choice** — one method everywhere to start. A single robust
  penalised-least-squares default (proposed `arpls`, whose one global
  smoothness parameter handles both the CWL angular width spread and TOF
  curvature) is used for every experiment, with all per-dataset
  adaptation coming from the auto-derived width, noise, and tolerance
  above; `method=` selects a specific algorithm explicitly. A
  `beam_mode`- or `radiation_probe`-specific policy is **not**
  introduced on speculation — the single default and the exact constants
  are confirmed by benchmarking against the tutorial corpus (§Testing),
  and a per-type policy is added only if that corpus shows one method is
  not enough (§Deferred Work).

The whole path is deterministic (no RNG), so reruns on the same inputs
yield identical points. When width or peak detection degenerates (too
few points, no detectable peaks), the estimator falls back to a
conservative metadata-derived width and emits **one** clear
`log.warning` telling the user to inspect and adjust — it does not
silently emit a bad background.

### 4. Backend: `pybaselines` (approved dependency) plus an in-house layer

`pybaselines` is added as a project dependency (BSD-3; runtime deps
NumPy and SciPy, both already required) and supplies **Stage 1**: the
peak-insensitive curve `B(x)` (`snip`, `arpls`) and, for the
classification methods (`fabc`, `fastchrom`, `dietrich`), a boolean
baseline `mask` with a `min_length` guard that is a natural
candidate-anchor pool abstaining in overlap. This is the same library
GSAS-II's `autoBkgCalc` delegates to.

The in-house layer owns everything `pybaselines` cannot know about a
diffraction pattern: the §3 auto-parameterization (data-derived width,
noise, and resolving `method='auto'` to the single default), the Stage-2
thinning and `[0, measured]` clipping, the model-guided re-estimation
(§5), and the point lifecycle. `pybaselines`' library defaults are
deliberately generic and would be wrong per-dataset, so the value is in
feeding it the right parameters, not in calling it raw.

### 5. Re-estimation is a first-class workflow

The intended usage is a loop, and the API supports it directly:

1. `auto_estimate()` early, from the measured data alone (no model yet)
   — a fixed starting background.
2. Refine the rest of the model (cell, scale, peak profile, …), with the
   background fixed or, point-by-point, freed.
3. `auto_estimate()` **again**. Now `data.intensity_calc` is populated,
   so with `use_model=True` (default) the estimator forms the peak-only
   model array `intensity_calc − intensity_bkg` and passes the Stage-1
   helper the **peak-subtracted measured intensities**

   `y = intensity_meas − (intensity_calc − intensity_bkg)`

   — the measured pattern with the fitted peaks removed, **not** the fit
   residual `intensity_meas − intensity_calc`. Because only the
   peak-only model is subtracted (the current background stays in `y`),
   the baseline `B(x)` estimated from `y` is the **absolute**
   background, so the emitted control points are absolute
   `_pd_background` heights and no add-back of `intensity_bkg` is
   needed. The same peak-only model array also yields the model's peak
   positions (the existing `find_peaks` pass, run on it rather than on
   the raw data), which place anchors at better **x positions** — in
   genuine inter-peak gaps, including across overlapped clusters the
   data alone could not resolve. Everything comes only from the
   backend-independent `data.intensity_meas` / `data.intensity_calc` /
   `data.intensity_bkg` arrays, so the improvement is identical for
   every calculator (Cryspy, CrysFML); it does **not** read
   `experiment.refln` reflection metadata, which is calculator-specific
   and may be absent or cleared. The data-only path — no calculation yet
   (`intensity_calc` all zero), or `use_model=False` — passes
   `y = intensity_meas` instead; both paths estimate an absolute
   background and clip heights to the original measured intensities
   (§2).

**Every call overwrites and re-fixes.** `auto_estimate()` always clears
the collection and rebuilds it — there is no append mode — and the
rebuilt points are **fixed** (`free=False`) regardless of whether the
previous points had been freed during refinement. A second call is
therefore a fresh fixed seed, not a merge: calling it again overwrites
the points and re-fixes them even if they were free. This keeps the loop
predictable (each pass starts from a clean, fixed background) and
idempotent (same inputs → same points). Clearing everything — including
any hand-added points — is the deliberate "overwrite" contract;
preserving manual points is deferred. When the collection is non-empty,
the call logs a one-line notice that it is replacing the existing
points, so a user who hand-tuned a background is not surprised; the
first call, with nothing to replace, is silent.

**Always fixed; no `free` argument.** Generated points are always
created fixed (`intensity.free = False`) — there is no caller-selectable
free option, so the "always re-fixes" contract above holds without
exception. The user reviews the points and flips individual ones — or
all — to refinable (`point.y.free = True`) afterward. This matches
fixed-point background practice and the stated review-then-refine
workflow.

**Mechanics.** Points get sequential string ids (`'1', '2', …`)
consistent with the existing `LineSegment.id` descriptor and its CIF
tag. Excluded regions are honoured for free, since `data.*` iterate
active points only.

### 6. Where the code lives

A backend-agnostic estimator helper —
`estimate_background_curve(x, y, *, beam_mode, peaks=None, width=None, ...) -> (curve, anchors)`
— lives in a new small module in the background package (e.g.
`datablocks/experiment/categories/background/estimate.py`). It is pure
array-in/array-out (the optional `peaks` argument carries model peak
positions detected from the peak-only model array per §5 — not
reflection metadata), holds no model state, wraps `pybaselines` for
Stage 1, and keeps the §3 parameterization and Stage-2 thinning in-house
— so it stays unit-testable in isolation and pulls no domain logic into
`core/`. `LineSegmentBackground.auto_estimate()` is a thin adapter: read
the pattern (and model, if present), call the helper, clip, and
`create()` the points. Helpers are extracted as needed to stay under the
lint complexity thresholds
([`lint-complexity-thresholds.md`](../accepted/lint-complexity-thresholds.md))
rather than raising them.

The same helper can later serve `ChebyshevPolynomialBackground` (fit its
coefficients to `B(x)`), but that is **not** built now — see _Deferred
Work_ — to avoid an abstraction before its second concrete use.

## Open Questions

The four design questions raised in review are resolved: noise-relative
Stage-2 thinning (§3), always-overwrite with a replace notice (§5), a
single Stage-1 method for now (§3), and a void method that logs a
one-line summary (§1). What remains is empirical calibration, done
against the tutorial corpus during implementation:

- The exact Stage-2 tolerance multiplier (`c · σ`, proposed `c ≈ 2`) and
  the width percentile (proposed ~75th) need tuning against real
  datasets.
- Whether the single Stage-1 method holds across the whole corpus
  (CWL/TOF, neutron/X-ray) or a `beam_mode`/`radiation_probe` policy is
  eventually needed (see §Deferred Work).

## Consequences

### Positive

- One call, no arguments, gives scientists a sensible, reviewable
  starting background — including in overlap regions, where heights come
  from the de-peaked curve.
- Robust across datasets _and_ experiment types because the length scale
  is measured from the data per call (§3) rather than hardcoded — and
  reliable at the first modelling step, when the resolution model is
  not.
- Supports the natural estimate → refine → re-estimate loop (§5): a
  later pass uses the fitted model to improve anchor placement, and
  re-running is safe, idempotent, and re-fixes the points.
- Output is ordinary line-segment points: editable, individually
  fixable/refinable, and already CIF-persisted — **no new CIF tags or
  serialization work**.
- Reuses the same backend (`pybaselines`) the GSAS-II fixed-point
  background relies on.

### Trade-offs

- Adds one dependency, `pybaselines` (approved; BSD-3,
  NumPy/SciPy-only).
- Not infallible with literally zero input: amorphous/diffuse humps and
  pathological overlap can still bias the first (data-only) pass. The
  honest contract is "a good starting estimate you then refine,"
  surfaced by a warning when the estimate is unreliable — not a
  guarantee of correctness.
- Adds an estimator module and a new public method to maintain.

### Compatibility Outcomes

- Purely additive: the manual `create()` workflow, existing projects,
  and the default background type are all unchanged. Nothing auto-runs.
- A project saved after `auto_estimate()` is an ordinary line-segment
  background; it reloads with no new fields.

## Alternatives Considered

- **Call `pybaselines` with its library defaults.** Rejected: its
  generic defaults (a one-size `lam`, an untuned SNIP window) are wrong
  per-dataset, so the §3 auto-parameterization layer is needed
  regardless. `pybaselines` supplies the curve; the diffraction-aware
  parameters come from us.
- **Derive the peak width from the resolution model (`U/V/W`).**
  Rejected as the default: the model is unrefined at the typical
  first-use moment and would give a badly wrong width — the user's own
  observation. The measured pattern carries the true widths and is
  model-independent.
- **Ship a built-in estimator and make `pybaselines` optional.**
  Rejected now that the dependency is approved: a single hard backend
  removes import-availability branching and two divergent code paths,
  and gives the better algorithms (`arpls`, `fabc`, the classification
  mask) unconditionally.
- **Naive valley / local-minima picking on the raw data.** Rejected: it
  inflates the background in overlapped regions — the exact problem in
  §Context.
- **Run estimation automatically at calculation time** (fill if empty).
  Rejected: hides a modelling choice, fights hand-tuned points, and
  re-validates generated output at runtime — all against project
  principles.
- **Merge or append, rather than overwrite, on re-run** (keep
  freed/refined points; an earlier draft exposed a `replace=False`
  append mode). Rejected: it makes the loop unpredictable and lets a
  stale point survive a better estimate, and no real use case justified
  the second mode. Every call overwrites and re-fixes — one predictable
  behaviour.
- **Generalise `auto_estimate()` onto `BackgroundBase` now** so
  Chebyshev shares it. Deferred: the shared _estimator helper_ (§6)
  already captures the reusable core; a base-level method awaits the
  second implementation.

## Testing

Per [`test-strategy.md`](../accepted/test-strategy.md), unit-level tests
(no calculation engine, no network, no sleeping) on the pure estimator
helper:

- **Synthetic patterns with a known analytic background** (flat, linear
  slope, smooth curve, TOF-like decay) plus planted Gaussian peaks,
  including a deliberately overlapped multiplet. Assert the recovered
  points reproduce the true background within tolerance, that **no
  anchor lands on a planted peak**, and that none exceeds the local
  data.
- **CWL angular broadening**: peaks whose FWHM grows with x. Assert the
  upper-percentile width keeps the background from being pulled up under
  the broad high-angle peaks.
- **Model-guided re-run**: with a supplied peak-only model over an
  overlapped cluster, assert better anchor placement (in true gaps) than
  the data-only pass on the same pattern, **and** that the emitted
  control-point heights are absolute background values matching the
  synthetic pattern's known background — not residual corrections around
  the input background.
- **Re-estimation lifecycle**: a second `auto_estimate()` clears prior
  points and produces **fixed** points even when the previous ones were
  freed; ids stay sequential.
- **Determinism**: identical inputs → identical points.
- **Graceful degradation**: a peakless or near-empty pattern triggers
  the single fallback warning rather than an exception or a garbage
  background.

**Tutorial corpus as real-world reference.** The ~25 tutorial scripts in
`docs/docs/tutorials/*.py` already build real experiments with
well-defined backgrounds across both beam modes and both probes — CWL
(e.g. the sloping background in
[`ed-17.py`](../../../../docs/docs/tutorials/ed-17.py) and
[`ed-2.py`](../../../../docs/docs/tutorials/ed-2.py)) and TOF (e.g.
[`ed-13.py`](../../../../docs/docs/tutorials/ed-13.py),
[`ed-16.py`](../../../../docs/docs/tutorials/ed-16.py)). Their
hand-placed line-segment points are ground truth: stripping them and
re-running `auto_estimate()` should reproduce a comparable background
curve within tolerance. This gives broad, real coverage across space
groups, beam modes, and probes at almost no authoring cost, and is the
reference set used to calibrate the default constants and confirm the
single Stage-1 method. These corpus checks run at the functional /
script level where the tutorial experiments are already loaded, not at
unit level.

The estimator module mirrors into
`tests/unit/easydiffraction/datablocks/experiment/categories/background/`
per the test-structure mirror rule.

## Deferred Work

- A spatially-varying / per-region Stage-1 window that follows the CWL
  angular broadening exactly (the upper-percentile single window is the
  adequate first cut).
- Beam-mode- and radiation-probe-specific Stage-1 method/parameter
  defaults, if benchmarking the single default against the tutorial
  corpus (CWL/TOF, neutron/X-ray) shows one method is not enough.
- `ChebyshevPolynomialBackground.auto_estimate()` fitting coefficients
  to the same `B(x)`, promoting the method to `BackgroundBase` once a
  second implementation exists.
- An opt-in path that consults the peak/resolution model for the width
  _once it is refined_, as a cross-check on the data-derived width.
- Using `experiment.refln` calculated reflection positions (when a
  calculator provides them) as an alternative or cross-check to the peak
  positions detected from the peak-only model array — deferred to keep
  the model-guided path backend-independent.
- A plot/diagnostic preview of the chosen curve and points via the
  display layer ([`display-ux.md`](../accepted/display-ux.md)).
- Tagging auto-generated points so a re-run can preserve hand-added
  ones.
- Total-scattering backgrounds (`pdffit2`) are out of scope — the
  line-segment model does not apply there.

## Related ADRs

- [`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — `background` is a Family-A switchable category; `auto_estimate()` is
  a type-specific method on `LineSegmentBackground`, not part of the
  selector surface.
- [`free-flag-cif-encoding.md`](../accepted/free-flag-cif-encoding.md) —
  generated points carry a fixed/fittable `free` flag persisted through
  CIF uncertainty syntax; no new tags.
- [`guarded-public-properties.md`](../accepted/guarded-public-properties.md)
  — each point's `intensity` is an editable `Parameter`.
- [`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md)
  — the `method` argument is an enum-backed closed value set.
- [`help-discoverability.md`](../accepted/help-discoverability.md) —
  `auto_estimate()` is surfaced in the category's `help()`.
- [`lint-complexity-thresholds.md`](../accepted/lint-complexity-thresholds.md)
  — the estimator stays within complexity guardrails via extracted
  helpers.
- [`test-strategy.md`](../accepted/test-strategy.md) — layered tests,
  mirror rule, no engines at unit level.
