---
title: Verification
icon: material/check-decagram
---

# :material-check-decagram: Verification

Every page recreates the **same** diffraction pattern in EasyDiffraction
and compares it against a reference calculated by external software
(FullProf) on identical input parameters. Each supported engine —
`cryspy` and `crysfml` — is overlaid on the FullProf reference in turn,
with a residual panel and closeness metrics, and the page ends with a
single agreement table.

The structure is defined in code, with every experimental parameter
taken verbatim from the frozen FullProf `.pcr` files. Each engine first
calculates with those parameters **without fitting**; where a difference
remains, a short refinement frees only the disputed parameters to show
it comes from how an experiment parameter is defined between the codes,
not from a disagreement about the structure.

Single-crystal pages compare the calculated F² of each reflection on a
y=x scatter instead of a profile overlay, and use `cryspy` only — the
sole engine with single-crystal Bragg support.

Most pages also run as a fast regression check (`pixi run script-tests`
and `pixi run notebook-tests`), so agreement is monitored over time.
Where an engine cannot yet reproduce a modelled effect, the page marks
the difference **in the notebook itself** with `known_discrepancy=True`
and a short reason: it still renders in the docs and is verified to
**stay** discrepant — failing CI if it unexpectedly starts agreeing, so
the mark must then be removed — while the fast regression run skips it.
Such pages are flagged **Known discrepancy** below.

Pages are grouped by **experiment type** (sample form, radiation probe,
and beam mode). Coverage grows to span every supported combination —
`pd-neut-cwl`, `pd-neut-tof`, `pd-xray`, `sc-neut-cwl`, `sc-neut-tof`,
and so on. The list below notes only what is specific to each page.

## Powder, neutron, constant wavelength

- [LBCO `pd-neut-cwl`](pd-neut-cwl_pv_lbco.ipynb) – Lanthanum barium
  cobaltate (La₀.₅Ba₀.₅CoO₃, _Pm-3m_); pseudo-Voigt, no asymmetry.
- [LBCO `pd-neut-cwl` (preferred orientation)](pd-neut-cwl_pv-march_lbco.ipynb)
  – Lanthanum barium cobaltate (La₀.₅Ba₀.₅CoO₃, _Pm-3m_); two-parameter
  March–Dollase preferred orientation (`march_r`, `march_random_fract`)
  along [0 0 1]. cryspy only; refines the scale to absorb cryspy's
  reciprocal, non-normalised texture convention.
- [PbSO₄ `pd-neut-cwl` (pseudo-Voigt)](pd-neut-cwl_pv_pbso4.ipynb) –
  Anglesite (PbSO₄, _Pnma_); pseudo-Voigt, no asymmetry.
- [PbSO₄ `pd-neut-cwl` from X-ray geometry](pd-neut-cwl_pv-xray-geometry_pbso4.ipynb)
  – Diagnostic neutron conversion of the X-ray single-wavelength PCR.
  Known discrepancy: changing only the FullProf radiation mode to
  neutron does not reproduce the expected Cryspy agreement.
- [PbSO₄ `pd-neut-cwl` (Bérar–Baldinozzi asymmetry)](pd-neut-cwl_pv-beba_pbso4.ipynb)
  – Anglesite (PbSO₄, _Pnma_); pseudo-Voigt with Bérar–Baldinozzi
  (FullProf-style) axial-divergence asymmetry (`asym_beba_*`). cryspy
  and FullProf implement this asymmetry with different conventions
  (issue 166), so the FullProf coefficients do not transfer one-to-one;
  freeing cryspy's own coefficients recovers the FullProf profile, so
  the page agrees. crysfml has no empirical-asymmetry model.
- [LaB₆ `pd-neut-cwl` (SyCos/SySin)](pd-neut-cwl_tch-fcj-noabs-nosldl_lab6.ipynb)
  – Lanthanum hexaboride (LaB₆, _Pm-3m_); pseudo-Voigt with SyCos/SySin
  sample-displacement and transparency corrections. Known discrepancy:
  pending the unreleased cryspy build (PR #46) that adds these
  corrections.
- [LaB₆ `pd-neut-cwl` (FCJ asymmetry)](pd-neut-cwl_tch-fcj-noabs_lab6.ipynb)
  – Lanthanum hexaboride (LaB₆, _Pm-3m_); Thompson–Cox–Hastings with
  Finger–Cox– Jephcoat axial-divergence asymmetry. Known discrepancy:
  FCJ asymmetry is not implemented in cryspy (crysfml-only).
- [LaB₆ `pd-neut-cwl` (absorption)](pd-neut-cwl_tch-fcj_lab6.ipynb) –
  Lanthanum hexaboride (LaB₆, _Pm-3m_); adds Debye–Scherrer sample
  absorption (μR = 0.7), now modelled by both engines, on top of FCJ
  asymmetry. Known discrepancy: FCJ asymmetry is not implemented in
  cryspy (crysfml-only).
- [LaB₆ `pd-neut-cwl` (absorption, no FCJ)](pd-neut-cwl_tch-fcj-nosldl_lab6.ipynb)
  – Lanthanum hexaboride (LaB₆, _Pm-3m_); Debye–Scherrer sample
  absorption (μR = 0.7) with FCJ asymmetry switched off, isolating the
  absorption correction. Enabling the correction removes a ≈ 2.9×
  intensity mismatch. Known discrepancy: a residual peak-position
  difference remains on the released cryspy (needs PR #46); it agrees on
  a develop cryspy build.
- [Y₂O₃ `pd-neut-cwl` (anisotropic β-tensor ADPs)](pd-neut-cwl_pv-beta_y2o3.ipynb)
  – Yttria (Y₂O₃, bixbyite, _Ia-3_); dimensionless β-tensor anisotropic
  ADPs (`adp_type='beta'`) on the three sites, with cylindrical
  Debye–Scherrer absorption (μR = 1.5) and the Thompson–Cox–Hastings
  profile. cryspy only. Refining every parameter recovers the FullProf
  values; the Bérar–Baldinozzi asymmetry (`asym_beba_*`) is implemented
  with different conventions in cryspy and FullProf (issue 166), so
  those coefficients do not transfer one-to-one, but all closeness
  metrics stay within tolerance.

## Powder, neutron, time-of-flight

- [Si `pd-neut-tof` (Jorgensen)](pd-neut-tof_j_si.ipynb) – Silicon (Si,
  _Fd-3m_); Jorgensen (back-to-back exponentials with a Gaussian). Known
  discrepancy: the ed-crysfml profile is ~8.5% off after fitting the
  scale; cryspy matches FullProf (issue 130).
- [Si `pd-neut-tof` (Jorgensen–Von Dreele)](pd-neut-tof_jvd_si.ipynb) –
  Silicon (Si, _Fd-3m_); Jorgensen–Von Dreele (back-to-back exponentials
  with a pseudo-Voigt). Known discrepancy: residual cryspy TOF
  Lorentzian discrepancy.
- [NaCaAlF `pd-neut-tof`](pd-neut-tof_jvd_ncaf.ipynb) – Sodium calcium
  aluminium fluoride (Na₂Ca₃Al₂F₁₄, _I2₁3_); Jorgensen–Von Dreele. Both
  engines agree with the FullProf reference within tolerance.

## Powder, X-ray, constant wavelength

- [PbSO₄ `pd-xray`](pd-xray-pbso4.ipynb) – Anglesite (PbSO₄, _Pnma_);
  laboratory Cu-source X-ray Rietveld Round Robin data; pseudo-Voigt.
  Known discrepancy: FullProf and Cryspy use different Cu Kα anomalous
  dispersion values, especially Pb f′, and FullProf truncates peak
  tails with Wdt.
- [PbSO₄ `pd-xray` single wavelength](pd-xray-pbso4-single.ipynb) –
  diagnostic single-wavelength FullProf reference for the same
  anglesite model. Known discrepancy: removing the Cu Kα₁/Kα₂ doublet
  leaves the anomalous-dispersion and Wdt tail-truncation mismatch.
- [PbSO₄ `pd-xray` single wavelength, Wdt 48, aligned f′](pd-xray-pbso4-single-unpolarized-wdt48-aligned.ipynb) –
  diagnostic single-wavelength FullProf reference with `Rpolarz = 0`,
  `Cthm = 0`, and `Wdt = 48`. Cryspy's Cu Kα anomalous-dispersion table
  and scale are locally aligned to FullProf, and the profile agrees
  within tolerance.

## Single crystal, neutron, constant wavelength

- [Pr₂NiO₄ `sc-neut-cwl` (no extinction)](sc-neut-cwl_pr2nio4.ipynb) –
  Strontium-doped praseodymium nickelate (Pr₂NiO₄:Sr, K₂NiF₄-type,
  _Fmmm_); per-reflection F² against FullProf reference with anisotropic
  ADPs.
- [Tb₂Ti₂O₇ `sc-neut-cwl` (no extinction)](sc-neut-cwl_noext_tbti.ipynb)
  – Terbium titanate (Tb₂Ti₂O₇, _F d -3 m_); per-reflection F² against a
  FullProf-no-extinction reference with anisotropic ADPs. Scale is
  initialized from the FullProf and refined.
- [Tb₂Ti₂O₇ `sc-neut-cwl` (isotropic extinction)](sc-neut-cwl_ext-iso_tbti.ipynb)
  – Terbium titanate (Tb₂Ti₂O₇, _F d -3 m_); per-reflection F² against
  FullProf reference with anisotropic ADPs and empirical extinction.
  Cryspy extinction (`becker-coppens`, `gauss`) uses two parameters,
  `radius` and `mosaicity`. Only `scale` and `radius` are refined
  against FullProf. Known discrepancy: cryspy and FullProf use different
  asymmetry conventions.
