# 179. Investigate a Better Automatic `cutoff_fwhm` Detection Mechanism

**Priority:** `[priority] medium`

## Problem

The automatic peak-range cutoff (`cutoff_fwhm = 0`, the default) picks the
window from a single heuristic: keep the profile down to a fixed fraction
`WDT_AUTO_FLOOR` (1e-6) of the peak height, with the Lorentzian reach
`0.5*sqrt(eta / WDT_AUTO_FLOOR)` FWHMs and a Gaussian floor
(`WDT_AUTO_GAUSS`). This depends only on the pseudo-Voigt mixing `eta`,
not on the actual data. A sweep across the Bragg-leastsq tutorials shows
this does **not** work equally well for all examples: the window is
far larger than needed for most patterns yet barely adequate for the most
demanding ones, and tuning a single global floor cannot satisfy both.

The current workaround is manual: a user re-runs a notebook at several
`cutoff_fwhm` (or `cutoff_fwhm_auto_floor`) values to find the smallest
window that does not move the refined parameters. That is exactly what an
"automatic" mode should remove.

## Evidence

Each tutorial was run with the AUTO window and with literal cutoffs down
to where a **physical** refined parameter first shifted by 1σ (background
`intensity`/`coef` points excluded as degenerate). Profiles affected:
TOF Jorgensen/JvD and CWL pseudo-Voigt(+berar). Cutoff-inert: single
crystal, PDF (pdffit2), and the TOF non-convoluted pseudo-Voigt (Npr=7).

| Example | beam / profile | AUTO ratio (1e-6) | empirical safe (≤1σ) |
| --- | --- | --- | --- |
| Si SEPD | TOF JvD (η≈0.22) | 10 → 234 | ~20 |
| LBCO HRPT | CWL pV (η 0.2–1) | 224 → 500 | ~10 |
| hs HRPT | CWL pV+berar | 6 → 500 | ~10 |
| CoSiO D20 | CWL pV+berar | 6 → 500 | ~3–5 |
| PbSO4 x-ray | x-ray CWL pV | 152 → 441 | ~50 |
| PbSO4 joint | joint x-ray+n | 209 → 433 | ~70–100 |
| TOF Gaussian (NCAF, mcstas) | TOF Jorgensen (η=0) | 10 (floor) | ~2–5 |

Key observations:

1. **The safe cutoff is governed by data S/N, not `eta` alone.** High-S/N
   x-ray (PbSO4) genuinely needs ~50–100 FWHMs because its Lorentzian
   tail stays above the noise far out; typical neutron powder (LBCO,
   CoSiO) needs only ~5–20 because the tail is buried in noise. `eta` only
   weakly orders these, so the η-only formula compresses a real 20×
   spread in need into a <2× spread in the chosen window.
2. **No single global floor works.** A floor that puts Si in its ~20–50
   target under-truncates PbSO4 (~100 need); a floor safe for PbSO4
   over-serves the neutron sets by 4×–100×.
3. **Tighter is not uniformly faster.** Per-fit-section timing showed that
   a tighter window can make the minimiser take *more* iterations
   (truncation roughens the χ² surface): LBCO §1 237→381 iterations
   (1e-6→1e-5), PbSO4-xray 181 s→257 s — yet Si JvD went 228→138
   iterations and 598 s→122 s. So a good mechanism must weigh per-iteration
   window cost against convergence robustness, not just window size.

The default floor is therefore kept conservative at 1e-6 (safe, robust,
max accuracy), with a per-experiment escape hatch (`cutoff_fwhm_auto_floor`,
and the literal `cutoff_fwhm`) for the rare slow case — but that still
requires the user to know which case they have.

## Candidate mechanisms to investigate

- **Noise-aware floor.** Truncate where the profile falls below a multiple
  of the local data esd / peak height, instead of a fixed fraction of the
  peak. Self-adapts to S/N: PbSO4 keeps its wide window, CoSiO shrinks.
  Needs the per-point esd at cutoff-evaluation time inside cryspy.
- **One-shot pre-fit calibration.** Before the first fit, evaluate the
  pattern once at a generous window, measure where each peak's modelled
  contribution drops below the data noise, and set the per-experiment
  window from that — no re-running the whole refinement.
- **Adaptive during fit.** Start generous and tighten once converged, or
  monitor whether shrinking the window changes the residual above noise.
- **Cap + floor combination.** Cap the η-derived ratio (e.g. at ~100–150)
  so broad-Lorentzian large patterns stay tractable while keeping the
  smooth-surface benefit of a not-too-tight window.

## Acceptance criteria

- A mechanism that, with no user input, selects a per-experiment window
  within ~1σ of the untruncated fit on every tutorial in the table above
  **and** is no slower than the current 1e-6 default on the fast cases.
- No reliance on re-running the notebook at multiple settings.
- Keep `cutoff_fwhm` (literal) and `cutoff_fwhm_auto_floor` as manual
  overrides.

## Related

- Auto/literal WDT cutoff and `cutoff_fwhm_auto_floor` live in the cryspy
  profile functions and are exposed on the TOF/CWL peak categories.
- Issue 167 (Add CrysFML `WDT` Parameter to Peak Shapes) — the crysfml
  backend has no cutoff yet; any cross-backend AUTO mechanism should
  consider both.
- Issue 130 (cryspy diverges on TOF JvD Lorentzian) — the robustness
  guard that motivated the conservative AUTO default.
