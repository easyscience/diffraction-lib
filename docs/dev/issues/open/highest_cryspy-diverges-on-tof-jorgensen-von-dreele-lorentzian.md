# 130. cryspy Diverges on TOF Jorgensen–Von Dreele Lorentzian

**Priority:** `[priority] highest`

**Type:** Correctness

For time-of-flight powder data using the Jorgensen–Von Dreele peak
profile, the `cryspy` backend diverges from FullProf and `crysfml`
whenever the Lorentzian term (`broad_lorentz_gamma_*`) is non-zero. On
the Si Verification reference case the profile difference reaches ≈22%
with an integrated-intensity ratio ≈0.72–0.76, while `crysfml` matches
FullProf to <1%. When the Lorentzian term is zero (NaCaAlF) `cryspy`
agrees to <1%, which localises the problem to the cryspy translation of
the pseudo-Voigt (Gaussian ⊗ Lorentzian) mixing for TOF.

**Fix:** verify how `broad_lorentz_gamma_*` is passed to cryspy for the
`jorgensen-von-dreele` profile and reconcile the convention with
crysfml/FullProf.

**Visible on:** the Si TOF Verification page
(`pd-neut-tof_Si_jorgensen-von-dreele`), whose closeness table flags the
`cryspy` rows in red — reported via a `known_discrepancy=True` agreement
check, so CI fails once the page starts agreeing and must be re-gated
manually.

**Depends on:** nothing.

**Recommended-priority note:** cryspy TOF Jorgensen–Von Dreele
Lorentzian is ~22% off and has a CI-skipped verification page (paired
with #134). **Tier 1 (do first).**
