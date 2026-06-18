# 119. Model Sample Absorption (Debye–Scherrer, μR)

**Priority:** `[priority] highest`

**Type:** Physics / Engine feature

The calculators (`cryspy`, `crysfml`) apply no sample-absorption
correction. For a cylindrical sample in Debye–Scherrer geometry this is
an angle-dependent intensity factor that boosts high-angle peaks. The
LaB₆ verification reference (`pd-neut-cwl_tch-fcj_lab6`) was refined in
FullProf with `μR = 0.7`; the unmodelled correction is the _entire_
intensity residual on the companion `pd-neut-cwl_tch-fcj_abs_lab6` page
(≈5% profile difference), while the `μR = 0` page passes to corr 0.9999.

**Correction (Hewat, Debye–Scherrer), validated to 4 decimals against
FullProf output:**

```
A(θ) = exp( -(1.7133 − 0.0368·sin²θ)·μR + (0.0927 + 0.375·sin²θ)·μR² )
```

A Lobanov–Alte-da-Veiga form covers `μR > 3`.

**Design:** captured in
[`adrs/accepted/model-sample-absorption.md`](../../adrs/accepted/model-sample-absorption.md)
— a switchable `experiment.absorption` category (mirroring `extinction`)
with a calculator-independent A(θ) envelope.

**What the backends actually provide (corrected):**

- `cryspy`: **no** absorption code at all (only Debye–Waller and sphere
  _extinction_); its CW intensity loop has no slot to multiply A(θ).
- `crysfml`: CrysFML08 implements `Lorentz_abs_CW` in Fortran, but the
  standalone absorption routine is **not** wrapped in `PythonAPI/`. The
  high-level CFL `patterns_simulation` path we call does not expose a
  model-level μR input through our binding, so it is **not** reachable
  through pycrysfml today without upstream changes.

**Implication:** neither backend can apply the correction internally
without changes we do not own. The chosen approach computes A(θ) in
EasyDiffraction and applies it as a pointwise envelope on the calculated
pattern, identically for both calculators (see the ADR).

**Note:** absorption is nearly degenerate with Biso + scale (its angle
term is linear in `sin²θ`, like the Debye–Waller), so refining Biso can
partly absorb it — but that biases Biso, so an explicit correction is
preferable. In FullProf `μR` is normally **fixed**, not refined.

**References:**

- A. W. Hewat, _Acta Cryst._ A35 (1979) 248 — cylindrical absorption.
- N. N. Lobanov & L. Alte da Veiga, 6th EPDIC, Abstract P12-16 (1998).
- CrysFML08:
  [`Src/CFML_Powder/Pow_Lorentz_Absorption.f90`](https://code.ill.fr/scientific-software/CrysFML2008/-/blob/master/Src/CFML_Powder/Pow_Lorentz_Absorption.f90),
  `Lorentz_abs_CW`.
- FullProf splits absorption into a refineable **magnitude** and a
  **type**: CW uses `μR` on the `.pcr` Lambda line (fixed there — no
  refinement codeword), with the cylindrical Hewat form implied; TOF
  uses `Iabscor` (`1` flat plate, `2` cylinder, `3` exponential
  `exp(−ABS·λᶜ)`). `Cthm`/`Rpolarz`/`2nd-muR` on the Lambda line are
  polarization and container terms, not the primary absorption knob.

**Depends on:** the switchable `experiment.absorption` category in the
ADR above (supersedes the earlier "add a `μR` instrument parameter"
sketch).

**Recommended-priority note:** Accounts for the entire intensity
residual on the LaB₆ verification page; well-specified (Hewat formula).
**Tier 1 (do first).**

**Architecture note (absorption correction).** Both backends return only
a finished, convolved profile to the EasyDiffraction layer
(`cryspy.calculate_pattern` → `signal_plus + signal_minus`;
`crysfml.calculate_pattern` → `np.asarray(y)`), and neither exposes a CW
absorption knob. So:

- An **in-project point-wise** `A(2θ)` correction is feasible now —
  multiply the summed structure profile by `A` in `bragg_pd.py` _before_
  adding the background (`_set_intensity_calc(calc + intensity_bkg)`),
  reusing the per-phase scale-factor precedent. Backend-agnostic, a
  small change plus a `μR` parameter (follows the
  `calib_sample_displacement` SyCos precedent).
- The **physically-exact per-reflection** `A(θ_hkl)`-before-convolution
  is **not** possible in our layer (both engines convolve internally);
  it requires owning the engine — the motivation of the
  in-house-calculation-engine ADR.
