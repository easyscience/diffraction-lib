# 179. Investigate a Better Automatic `cutoff_fwhm` Detection Mechanism

**Priority:** `[priority] medium`

## Problem

There is currently **no** automatic peak-range cutoff. `cutoff_fwhm`
defaults to `0`, which cryspy (≥ 0.12.0) treats as "no cutoff" — the
full range is computed (maximally accurate, slowest). A positive
`cutoff_fwhm` is a literal window in FWHMs that mirrors FullProf's `WDT`
(see
[`peak-profile-cutoff.md`](../../adrs/accepted/peak-profile-cutoff.md)).
To get the speed-up a user must pick that value by hand.

The right value is data-dependent, so picking it by hand means
re-running a notebook at several `cutoff_fwhm` values to find the
smallest window that does not move the refined parameters. We want an
**automatic** mechanism that, with no user input, computes a safe
per-experiment literal `cutoff_fwhm` (a single injected scalar;
per-point adaptivity would need upstream cryspy support, see the ADR's
Deferred Work).

An earlier η-adaptive prototype (a window `max(4·FWHM, cutoff_fwhm·η)`
driven by a `WDT_AUTO_FLOOR` peak-height fraction) was measured but not
shipped: it keyed only on the pseudo-Voigt mixing `eta`, not on the
data, and a single global floor could not serve both the wide-tail and
buried-tail cases. Its measurements are kept below as the design target.

## Evidence

Each tutorial was run with the earlier η-adaptive prototype window and
with literal cutoffs down to where a **physical** refined parameter
first shifted by 1σ (background `intensity`/`coef` points excluded as
degenerate). Profiles affected: TOF Jorgensen/JvD and CWL
pseudo-Voigt(+berar). Cutoff-inert: single crystal, PDF (pdffit2), and
the TOF non-convoluted pseudo-Voigt (Npr=7).

| Example                     | beam / profile      | AUTO ratio (1e-6) | empirical safe (≤1σ) |
| --------------------------- | ------------------- | ----------------- | -------------------- |
| Si SEPD                     | TOF JvD (η≈0.22)    | 10 → 234          | ~20                  |
| LBCO HRPT                   | CWL pV (η 0.2–1)    | 224 → 500         | ~10                  |
| hs HRPT                     | CWL pV+berar        | 6 → 500           | ~10                  |
| CoSiO D20                   | CWL pV+berar        | 6 → 500           | ~3–5                 |
| PbSO4 x-ray                 | x-ray CWL pV        | 152 → 441         | ~50                  |
| PbSO4 joint                 | joint x-ray+n       | 209 → 433         | ~70–100              |
| TOF Gaussian (NCAF, mcstas) | TOF Jorgensen (η=0) | 10 (floor)        | ~2–5                 |

Key observations:

1. **The safe cutoff is governed by data S/N, not `eta` alone.**
   High-S/N x-ray (PbSO4) genuinely needs ~50–100 FWHMs because its
   Lorentzian tail stays above the noise far out; typical neutron powder
   (LBCO, CoSiO) needs only ~5–20 because the tail is buried in noise.
   `eta` only weakly orders these, so the η-only formula compresses a
   real 20× spread in need into a <2× spread in the chosen window.
2. **No single global floor works.** A floor that puts Si in its ~20–50
   target under-truncates PbSO4 (~100 need); a floor safe for PbSO4
   over-serves the neutron sets by 4×–100×.
3. **Tighter is not uniformly faster.** Per-fit-section timing showed
   that a tighter window can make the minimiser take _more_ iterations
   (truncation roughens the χ² surface): LBCO §1 237→381 iterations
   (1e-6→1e-5), PbSO4-xray 181 s→257 s — yet Si JvD went 228→138
   iterations and 598 s→122 s. So a good mechanism must weigh
   per-iteration window cost against convergence robustness, not just
   window size.

Today the user falls back to the literal `cutoff_fwhm` (default `0` = no
cutoff) and must know which case they have to choose a safe value.

## Candidate mechanisms to investigate

All EasyDiffraction-side options compute a single per-experiment scalar
that is injected as the literal `cutoff_fwhm`; per-point adaptivity is
out of reach without upstream cryspy support.

- **One-shot pre-fit calibration.** Before the first fit, evaluate the
  pattern once at a generous (or no) cutoff, measure where each peak's
  modelled contribution drops below the data noise, and set the
  per-experiment window from that — no re-running the whole refinement.
  This is the most promising in-project route.
- **Noise-aware floor.** Truncate where the profile falls below a
  multiple of the local data esd / peak height, instead of a fixed
  fraction of the peak. Self-adapts to S/N: PbSO4 keeps its wide window,
  CoSiO shrinks. Per-point would need the esd at cutoff-evaluation time
  inside cryspy; a per-experiment approximation can be derived in the
  pre-fit calibration above.
- **Adaptive during fit.** Start generous and tighten once converged, or
  monitor whether shrinking the window changes the residual above noise.
- **Cap + floor combination.** Cap the η-derived ratio (e.g. at
  ~100–150) so broad-Lorentzian large patterns stay tractable while
  keeping the smooth-surface benefit of a not-too-tight window.

## Acceptance criteria

- A mechanism that, with no user input, selects a per-experiment window
  within ~1σ of the untruncated (`cutoff_fwhm = 0`) fit on every
  tutorial in the table above **and** is no slower than that untruncated
  baseline on the fast cases.
- No reliance on re-running the notebook at multiple settings.
- Keep the literal `cutoff_fwhm` as the manual override.

## Recommendation

Start with **one-shot pre-fit calibration**: evaluate the pattern once at
no cutoff, then set a single per-experiment `cutoff_fwhm` from where each
peak's modelled contribution falls below the local data noise — keeping
the literal `cutoff_fwhm` as the manual override (satisfies the
acceptance criteria, no cryspy change). The per-point η-adaptive window
is the longer-term ideal but needs upstream cryspy support, since
per-point η is not visible to the EasyDiffraction calculator.

History: an automatic window did ship on the custom/hotfix cryspy
(`cutoff_fwhm` defaulted to a tail-aware window in commit `8996e5bd3`,
with a `cutoff_fwhm_auto_floor` knob in `5ba71617c`). It was removed in
`9a5660973` ("Use cryspy 0.12.0; … drop inert auto-floor param") when
adopting stock cryspy 0.12.0, which exposes only the single literal
scalar — so EasyDiffraction now passes the user's fixed value with no
automatic selection.

## Related

- The literal `WDT`/`cutoff_fwhm` cutoff lives in the cryspy profile
  functions (released in cryspy 0.12.0) and is exposed on the TOF/CWL
  peak categories; see
  [`peak-profile-cutoff.md`](../../adrs/accepted/peak-profile-cutoff.md)
  (Deferred Work covers this automatic mechanism and the upstream
  per-point η-adaptive window).
- Issue 167 (Add CrysFML `WDT` Parameter to Peak Shapes) — the crysfml
  backend has no cutoff yet; any cross-backend auto mechanism should
  consider both.
- Issue 130 (cryspy diverges on TOF JvD Lorentzian) — the robustness
  guard motivating a conservative window.
