# 134. Investigate ed-crysfml TOF Jorgensen Profile Discrepancy

**Priority:** `[priority] highest`

**Type:** Correctness

For time-of-flight powder data using the plain Jorgensen profile
(back-to-back exponentials ⊗ Gaussian, no Lorentzian), the `crysfml`
backend diverges from FullProf and `cryspy` after the scale is fitted:
the profile is ≈8.5% off with an integrated-area ratio ≈1.09 (corr
≈0.997), while `cryspy` matches FullProf. This localises the problem to
the crysfml translation of the Jorgensen TOF profile, and is
complementary to the `cryspy` Jorgensen–Von Dreele Lorentzian divergence
tracked in issue 130.

**Visible on:** the Si TOF Jorgensen Verification page
(`pd-neut-tof_si_jorgensen`), currently marked with
`known_discrepancy=True`. Re-gate the page (or tighten its agreement
check) once the crysfml profile is reconciled.

**Depends on:** nothing.

**Recommended-priority note:** crysfml TOF Jorgensen is ~8.5% off and
has a known-discrepancy verification page (paired with #130). **Tier 1
(do first).**
