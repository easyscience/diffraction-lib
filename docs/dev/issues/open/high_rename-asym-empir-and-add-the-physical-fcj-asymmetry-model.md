# 133. Rename `asym_empir_*` and Add the Physical FCJ Asymmetry Model

**Priority:** `[priority] high`

**Type:** Experiment model / Peak profile / API naming

**Status (partial):** Item 1 (the rename) is **done** — the parameters
are now `asym_beba_a0`, `asym_beba_b0`, `asym_beba_a1`, `asym_beba_b1`
(class `CwlPseudoVoigtBerarBaldinozziAsymmetry`, type string
`pseudo-voigt + berar-baldinozzi asymmetry`, page renamed to
`pd-neut-cwl_pbso4_beba-asymmetry`). This issue stays open for **item 2** (add
the physical FCJ model). The cryspy/FullProf implementation difference
is characterised in issue 166.

The four empirical peak-asymmetry parameters (`asym_beba_*`, formerly
`asym_empir_1`…`4`, on the `pd-neut-cwl_pbso4_beba-asymmetry` Verification
page) are the **Bérar–Baldinozzi** correction — FullProf's `P1`–`P4` — a
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

1. **Rename** the empirical parameters so the name states what they are.
   **Done:** renamed to `asym_beba_{a0,b0,a1,b1}` (the `beba` model tag
   mirrors `asym_fcj_*`; the `a0/b0/a1/b1` suffixes name the
   coefficients of the `Fa`/`Fb` × `1/tan θ`/`1/tan 2θ` basis),
   replacing the generic `asym_empir_*` that hid their Bérar–Baldinozzi
   origin.
2. **Add the FCJ model alongside** the empirical one (not as a
   replacement), as a switchable asymmetry choice, so users can pick the
   physically-based two-parameter model when the instrument geometry is
   known and fall back to the empirical correction otherwise.

**Relates to:** the asymmetry discrepancy tracked in issue 166 and on
the `pd-neut-cwl_pbso4_beba-asymmetry` Verification page (currently marked
`known_discrepancy=True`), and the TCH/FCJ work noted on the
`pd-neut-cwl_lab6_fcj-asymmetry` page.

**Depends on:** calculator-backend support for the FCJ asymmetry
parameters (cryspy/crysfml) before the second item can be wired through.

**Recommended-priority note:** Physical FCJ asymmetry model plus
renaming `asym_empir_*`; unblocks further CI-skipped asymmetry pages.
**Tier 3 (user-visible roadmap feature).**
