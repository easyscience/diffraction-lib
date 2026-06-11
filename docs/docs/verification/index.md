---
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
and `pixi run notebook-tests`), so agreement is monitored over time. A
few are excluded from CI where an engine cannot yet reproduce a modelled
effect; each such page states the reason below.

Pages are grouped by **experiment type** (sample form, radiation probe,
and beam mode). Coverage grows to span every supported combination —
`pd-neut-cwl`, `pd-neut-tof`, `pd-xray`, `sg-neut-cwl`, `sg-neut-tof`,
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
- [PbSO₄ `pd-neut-cwl` (empirical asymmetry)](pd-neut-cwl_pv-asym_empir_pbso4.ipynb)
  – Anglesite (PbSO₄, _Pnma_); pseudo-Voigt with empirical
  (FullProf-style) axial-divergence asymmetry. Skipped in CI: cryspy and
  FullProf parameterise the empirical asymmetry differently, and crysfml
  has no empirical-asymmetry model.
- [LaB₆ `pd-neut-cwl` (SyCos/SySin)](pd-neut-cwl_tch-fcj-noabs-nosldl_lab6.ipynb)
  – Lanthanum hexaboride (LaB₆, _Pm-3m_); pseudo-Voigt with SyCos/SySin
  sample-displacement and transparency corrections. Skipped in CI:
  pending the unreleased cryspy build that adds these corrections.
- [LaB₆ `pd-neut-cwl` (FCJ asymmetry)](pd-neut-cwl_tch-fcj-noabs_lab6.ipynb)
  – Lanthanum hexaboride (LaB₆, _Pm-3m_); Thompson–Cox–Hastings with
  Finger–Cox– Jephcoat axial-divergence asymmetry. Skipped in CI: FCJ
  asymmetry is crysfml-only.
- [LaB₆ `pd-neut-cwl` (absorption)](pd-neut-cwl_tch-fcj_lab6.ipynb) –
  Lanthanum hexaboride (LaB₆, _Pm-3m_); adds Debye–Scherrer sample
  absorption (μR) on top of FCJ asymmetry. Skipped in CI: sample
  absorption is modelled by neither engine.

## Powder, neutron, time-of-flight

- [Si `pd-neut-tof` (Jorgensen)](pd-neut-tof_j_si.ipynb) – Silicon (Si,
  _Fd-3m_); Jorgensen (back-to-back exponentials with a Gaussian).
- [Si `pd-neut-tof` (Jorgensen–Von Dreele)](pd-neut-tof_jvd_si.ipynb) –
  Silicon (Si, _Fd-3m_); Jorgensen–Von Dreele (back-to-back exponentials
  with a pseudo-Voigt). Skipped in CI: residual cryspy TOF Lorentzian
  discrepancy.
- [NaCaAlF `pd-neut-tof`](pd-neut-tof_jvd_ncaf.ipynb) – Sodium calcium
  aluminium fluoride (Na₂Ca₃Al₂F₁₄, _I2₁3_); Jorgensen–Von Dreele.
  Skipped in CI: the FullProf reference uses a tabulated
  instrument-resolution file that the polynomial profile cannot
  reproduce.

## Single crystal, neutron, constant wavelength

- [Pr₂NiO₄ `sg-neut-cwl` (no extinction)](sg-neut-cwl_pr2nio4.ipynb) –
  Strontium-doped praseodymium nickelate (Pr₂NiO₄:Sr, K₂NiF₄-type,
  _Fmmm_); per-reflection F² against FullProf reference with anisotropic
  ADPs.
- [Tb₂Ti₂O₇ `sg-neut-cwl` (no extinction)](sg-neut-cwl_noext_tbti.ipynb)
  – Terbium titanate (Tb₂Ti₂O₇, _F d -3 m_); per-reflection F² against a
  FullProf-no-extinction reference with anisotropic ADPs. Scale is
  initialized from the FullProf and refined.
- [Tb₂Ti₂O₇ `sg-neut-cwl` (isotropic extinction)](sg-neut-cwl_ext-iso_tbti.ipynb)
  – Terbium titanate (Tb₂Ti₂O₇, _F d -3 m_); per-reflection F² against
  FullProf reference with anisotropic ADPs and empirical extinction.
  Cryspy extinction (`becker-coppens`, `gauss`) uses two parameters,
  `radius` and `mosaicity`. Only `scale` and `radius` are refined
  against FullProf.
