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
([`upstream-capability-request-evidence.md`](upstream-capability-request-evidence.md)):
the literal cutoff was proposed upstream and released in cryspy 0.12.0,
so EasyDiffraction drives it through the released `profile_cutoff_fwhm`
key without requiring a cryspy CIF-schema change.

## Decision

Expose a per-experiment peak-profile range cutoff and feed it to cryspy,
using cryspy's released **literal** cutoff (cryspy ≥ 0.12.0).

1. **Public API.** Add `experiment.peak.cutoff_fwhm` to the TOF and CWL
   peak categories as a non-refinable `NumericDescriptor` (a calculation
   control, not a fittable quantity). The value is the cutoff measured
   in **FWHMs**, which is what the name states; it equals FullProf's
   `WDT`. The name `cutoff_fwhm` is preferred over `cutoff_lorentz` (the
   cutoff trims the whole pseudo-Voigt window, not only the Lorentzian
   part) and over `cutoff_wdt` (cryptic outside FullProf).

2. **Literal window (matches FullProf `WDT` and cryspy ≥ 0.12.0).**
   `cutoff_fwhm` is a single literal half-width in FWHMs applied around
   each peak centre. cryspy keeps only the points within

   ```
   |Δ| ≤ cutoff_fwhm · (FWHM + 1/α + 1/β)   (TOF)
   |z| ≤ cutoff_fwhm                         (CWL, z in FWHM units)
   ```

   For TOF the back-to-back exponential e-folding tails (`1/α`, `1/β`)
   are added to the window so the asymmetric tails are retained. This is
   exactly FullProf's `WDT` semantics, so setting `cutoff_fwhm` to a
   `.pcr` `WDT` value gives an apples-to-apples comparison. A per-point
   η-adaptive window is **not** part of this decision — see Deferred
   Work.

3. **Backend hand-off (no cryspy CIF-schema change).** The cryspy
   profile functions take a cutoff argument that defaults to a module
   constant; the cryspy `rhochi` drivers read it from the experiment
   dictionary key `profile_cutoff_fwhm`, falling back to the constant
   when absent. The EasyDiffraction cryspy calculator injects
   `cryspy_dict[<expt>]["profile_cutoff_fwhm"] = peak.cutoff_fwhm.value`
   in the peak-update step, which runs on **both** the object-recreate
   path and the minimizer fast-dict path, so the value reaches every
   calculation without serialising a new CIF item.

4. **Default `cutoff_fwhm = 0` = no cutoff.** The default is `0` for
   both TOF and CWL, which cryspy treats as "no cutoff" (the full range
   is computed — slower but maximally accurate). A positive value is an
   opt-in literal cutoff that trades accuracy for speed. There is no
   safe auto-tuned default value to choose, because the right cutoff is
   data-dependent (see Context); the verification suite sets each page's
   `cutoff_fwhm` explicitly to that case's FullProf `.pcr` `WDT`.

## Consequences

- With a positive `cutoff_fwhm` the peak-profile function is markedly
  cheaper (TOF Jorgensen-Von Dreele ≈ 10× and CWL pseudo-Voigt ≈ 4–7×
  faster at the verification `WDT` values, with the FullProf area ratio
  and Rwp unchanged). The default `0` keeps the full profile, so the
  speed-up is opt-in per experiment.
- The speed-up is realised on profile-re-evaluating refinement
  iterations and on single `calculate()` calls. It is **not** the
  current minimization bottleneck: profiling shows refinement time is
  dominated by EasyDiffraction's per-iteration Wyckoff symmetry-
  constraint solve, not by cryspy (see Deferred Work).
- `cutoff_fwhm` persists in the experiment CIF
  (`_easydiffraction_peak.cutoff_fwhm`) like other peak settings; it is
  never refined.
- Correct results require a cryspy that honours `profile_cutoff_fwhm`
  (released in cryspy 0.12.0). An older cryspy ignores the key and
  computes the full profile (slower but identical numerically), so the
  parameter degrades safely.
- The accuracy contract is stated in area-ratio terms (the verification
  suite requires the integrated peak-area ratio to stay within
  `0.99–1.01`), giving a clear rule for choosing or validating any
  `cutoff_fwhm` value.

## Alternatives Considered

- **Fixed module constant, no user control.** Simplest, but cannot be
  both safe and fast across data with different Lorentzian content;
  gives users no lever. Rejected.
- **Auto-tuned positive default.** Choosing a single non-zero default
  (e.g. `10` TOF / `80` CWL) was prototyped but rejected: the safe value
  is data-dependent, so any constant is either too slow (sized for the
  worst case) or unsafe (truncates strong-Lorentzian tails). Defaulting
  to `0` (no cutoff) is always correct; users opt in to the speed-up.
- **Per-point η-adaptive window**
  (`half_width = max(4·FWHM, cutoff_fwhm·η)`). Faster than a uniform
  literal window on mixed-η patterns at equal accuracy, but it must run
  **inside** the cryspy profile kernels (per-point η is not available to
  the EasyDiffraction calculator, which can only inject one scalar) and
  released cryspy exposes only the literal cutoff. Deferred to upstream
  cryspy work; see Deferred Work.
- **Names `cutoff_lorentz` / `cutoff_wdt`.** Rejected: the first
  mis-implies a Lorentzian-only effect, the second is opaque.
- **Serialise `WDT` as a new cryspy CIF item.** Avoided; dict injection
  needs no upstream schema change and works on both calculation paths.

## Deferred Work

- **Automatic cutoff selection** (issue 179): compute a safe per-
  experiment literal `cutoff_fwhm` in EasyDiffraction from the peak
  parameters, so `0` could mean "auto" instead of "no cutoff" without
  the user guessing a value. This stays a single injected scalar and
  needs no cryspy change, but is a per-experiment (worst-case-η) bound,
  not a per-point optimum.
- **Per-point η-adaptive window upstream:** a future cryspy PR could add
  the η-adaptive window inside the profile kernels (where per-point η is
  known) for the extra speed-up on mixed-η patterns.
- The dominant **minimization** cost is EasyDiffraction-side, not the
  profile: `crystallography._orbit_template_residual` re-solves
  `numpy.linalg.lstsq` over 27 lattice shifts per orbit template per
  atom site on every iteration (~45 % of a fit iteration in profiling),
  even though the Wyckoff orbit assignment is fixed for the duration of
  a fit. Caching the per-site orbit template at fit setup is the larger
  refinement-speed win and is out of scope for this ADR.
