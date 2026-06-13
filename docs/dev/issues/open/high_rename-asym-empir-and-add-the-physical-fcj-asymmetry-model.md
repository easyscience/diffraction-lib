# 133. Rename `asym_empir_*` and Add the Physical FCJ Asymmetry Model

**Priority:** `[priority] high`

**Type:** Experiment model / Peak profile / API naming

The four empirical peak-asymmetry parameters (`asym_empir_1`…`4`, the
`pd-neut-cwl_pv-asym_empir_pbso4` Verification page) are the
**Bérar–Baldinozzi** correction — FullProf's `P1`–`P4` — a
phenomenological sum of functions in `1/tan θ` and `1/tan 2θ`. It can
fit an asymmetric peak, but the parameters carry **no physical
meaning**, are strongly correlated, do **not** transfer between
datasets, and can misbehave (over-correction, unphysical profile
shapes).

The **Finger–Cox–Jephcoat (FCJ)** `S_L`/`D_L` model is physically based:
just **two** parameters tied to real instrument geometry (sample and
slit/detector heights over the goniometer radius), with the correct
built-in angular dependence — asymmetry that vanishes at `2θ = 90°` and
reverses past it. Fewer parameters, better-conditioned, and
instrument-meaningful.

**Two future considerations:**

1. **Rename** the empirical parameters so the name states what they are
   — e.g. `asym_berar_baldinozzi_1`…`4` (or a `berar_baldinozzi_p*`
   form) — rather than the generic `asym_empir_*`, which hides their
   origin and conflates "empirical asymmetry" with the specific
   Bérar–Baldinozzi formula.
2. **Add the FCJ model alongside** the empirical one (not as a
   replacement), as a switchable asymmetry choice, so users can pick the
   physically-based two-parameter model when the instrument geometry is
   known and fall back to the empirical correction otherwise.

**Relates to:** the asymmetry discrepancy tracked on the
`pd-neut-cwl_pv-asym_empir_pbso4` Verification page (currently in
`docs/docs/verification/ci_skip.txt`), and the TCH/FCJ work noted on the
`pd-neut-cwl_tch-fcj_lab6` page.

**Depends on:** calculator-backend support for the FCJ asymmetry
parameters (cryspy/crysfml) before the second item can be wired through.

**Recommended-priority note:** Physical FCJ asymmetry model plus renaming `asym_empir_*`; unblocks further CI-skipped asymmetry pages. **Tier 3 (user-visible roadmap feature).**
