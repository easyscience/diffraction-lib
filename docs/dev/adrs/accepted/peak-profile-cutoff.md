# ADR: Peak-Profile Range Cutoff (`cutoff_fwhm`)

## Status

Accepted.

## Date

2026-06-20

## Group

Experiment model.

## Context

For powder data the cryspy backend evaluates each reflection's peak
profile at **every** point of the pattern. Concretely the TOF
back-to-back-exponential profile (`tof_Jorgensen`,
`tof_Jorgensen_VonDreele`) and the constant-wavelength pseudo-Voigt
(`calc_profile_pseudo_voight`) each build a dense `(n_points × n_hkl)`
matrix and run the transcendental kernels (`erfc`, `exp`, the complex
exponential integral `exp1`, Lorentzian and Finger-Cox-Jephcoat
asymmetry) over all of it — including the vast region far from each peak
where the contribution is numerically negligible. The cost grows with
`n_points × n_hkl`, which is large for wide constant-wavelength scans
with many reflections.

FullProf solves this with its `WDT` parameter: each peak is only
calculated within a window of a few FWHMs around its centre. cryspy has
no equivalent, so the wasted far-field evaluation is paid on every
profile computation, i.e. on the refinement iterations that re-evaluate
the profile (when broadening parameters `U/V/W/X/Y`, `σ/γ`, or the unit
cell are refined).

The right cutoff value is data-dependent: a sharp, Gaussian-dominated
peak needs only a few FWHMs, while the slow `1/Δ²` Lorentzian tail needs
a much wider window. The **binding accuracy metric is the integrated
peak-area ratio**, not Rwp: truncating the Lorentzian tail removes area
(absorbed by the scale factor, so Rwp barely moves) and the verification
suite requires the area ratio to stay within `0.99–1.01`. Empirically a
strong-Lorentzian case with preferred orientation (LBCO) needs a much
wider window than a weak-Lorentzian one (LaB6), so a single hard-coded
constant is either too slow (sized for the worst case everywhere) or
unsafe (too aggressive for some data). Users therefore need a per-
experiment knob, mirroring FullProf's `.pcr` `WDT`.

This relates to the upstream capability-request workflow
([`upstream-capability-request-evidence.md`](../suggestions/upstream-capability-request-evidence.md)):
the cutoff is implemented in cryspy via a local patch and proposed
upstream; EasyDiffraction must drive it without requiring a cryspy CIF-
schema change.

## Decision

Expose a per-experiment peak-profile range cutoff and feed it to cryspy.

1. **Public API.** Add `experiment.peak.cutoff_fwhm` to the TOF and CWL
   peak categories as a non-refinable `NumericDescriptor` (a calculation
   control, not a fittable quantity). The value is the cutoff measured
   in **FWHMs**, which is what the name states; it equals FullProf's
   `WDT`. The name `cutoff_fwhm` is preferred over `cutoff_lorentz` (the
   cutoff trims the whole pseudo-Voigt window, not only the Lorentzian
   part) and over `cutoff_wdt` (cryptic outside FullProf).

2. **η-adaptive window.** Per evaluated point the half-width is

   ```
   half_width = max(WDT_GAUSS_FLOOR · FWHM,  cutoff_fwhm · η)
   ```

   with `WDT_GAUSS_FLOOR = 4`. Thus `cutoff_fwhm` is the window for a
   _pure Lorentzian_ (η = 1); Gaussian-dominated points (η → 0) collapse
   to the ~4-FWHM floor. Scaling the window **linearly with η** keeps
   the absolute truncated tail-area bounded; a naive
   `floor + (cutoff_fwhm − floor)·η` interpolation under-windows the
   moderate-η peaks that dominate CWL and breaks the area-ratio
   invariant (verified against LBCO). For TOF the back-to-back
   exponential e-folding tails (`1/α`, `1/β`) are added inside the
   window so the asymmetric tails are retained.

3. **Backend hand-off (no cryspy CIF-schema change).** The cryspy
   profile functions take a `wdt` argument that defaults to a module
   constant; the cryspy `rhochi` drivers read it from the experiment
   dictionary key `profile_cutoff_fwhm`, falling back to the constant
   when absent. The EasyDiffraction cryspy calculator injects
   `cryspy_dict[<expt>]["profile_cutoff_fwhm"] = peak.cutoff_fwhm.value`
   in the peak-update step, which runs on **both** the object-recreate
   path and the minimizer fast-dict path, so the value reaches every
   calculation without serialising a new CIF item.

4. **Defaults.** `cutoff_fwhm = 10` (TOF), `cutoff_fwhm = 80` (CWL) —
   the smallest values that keep every FullProf verification's area
   ratio within `0.99–1.01`. CWL is binding via LBCO (passes at ≥ 64; 80
   gives margin). The large CWL default looks big but, because the
   window is η-adaptive, only pure-Lorentzian peaks pay it; low-η peaks
   use far tighter windows.

## Consequences

- The peak-profile function is markedly cheaper: TOF Jorgensen-Von
  Dreele ≈ 10× and CWL pseudo-Voigt ≈ 4–7× faster at the safe defaults,
  with the FullProf area ratio and Rwp unchanged. On a mixed-η CWL
  pattern the η-adaptive window is ≈ 1.6× faster than a uniform window
  at equal accuracy.
- The speed-up is realised on profile-re-evaluating refinement
  iterations and on single `calculate()` calls. It is **not** the
  current minimization bottleneck: profiling shows refinement time is
  dominated by EasyDiffraction's per-iteration Wyckoff symmetry-
  constraint solve, not by cryspy (see Deferred Work).
- `cutoff_fwhm` persists in the experiment CIF
  (`_easydiffraction_peak.cutoff_fwhm`) like other peak settings; it is
  never refined.
- Correct results require a cryspy build that honours
  `profile_cutoff_fwhm`. Until the upstream cryspy PR is released this
  is supplied by the local patch; a stock cryspy ignores the key and
  computes the full profile (slower but identical numerically), so the
  parameter degrades safely.
- The accuracy contract is stated in area-ratio terms, giving a clear
  rule for choosing or validating any future default.

## Alternatives Considered

- **Fixed module constant, no user control.** Simplest, but cannot be
  both safe and fast across data with different Lorentzian content;
  gives users no lever. Rejected.
- **Uniform (non-adaptive) window.** Safe but pays the worst-case
  Lorentzian width on every peak; ≈ 1.6× slower than η-adaptive on mixed
  patterns. Kept as the conceptual baseline, not the implementation.
- **`floor + (cutoff_fwhm − floor)·η` interpolation.** Intuitive but
  under-windows moderate-η peaks and fails LBCO's area ratio (measured).
  Rejected in favour of the `max(floor, cutoff_fwhm·η)` scaling.
- **Names `cutoff_lorentz` / `cutoff_wdt`.** Rejected: the first
  mis-implies a Lorentzian-only effect, the second is opaque.
- **Serialise `WDT` as a new cryspy CIF item.** Avoided; dict injection
  needs no upstream schema change and works on both calculation paths.

## Deferred Work

- The dominant **minimization** cost is EasyDiffraction-side, not the
  profile: `crystallography._orbit_template_residual` re-solves
  `numpy.linalg.lstsq` over 27 lattice shifts per orbit template per
  atom site on every iteration (~45 % of a fit iteration in profiling),
  even though the Wyckoff orbit assignment is fixed for the duration of
  a fit. Caching the per-site orbit template at fit setup is the larger
  refinement-speed win and is out of scope for this ADR.
- Upstream cryspy PR adding `profile_cutoff_fwhm` support (peak-range
  cutoff for the TOF and CWL profiles) so the local patch can be
  dropped.
