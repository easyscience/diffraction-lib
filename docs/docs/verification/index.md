---
icon: material/check-decagram
---

# :material-check-decagram: Verification

Every page calculates the **same** diffraction pattern with each
supported EasyDiffraction engine — `cryspy` and `crysfml` — and compares
them against each other and, where a reference profile is available,
against external software (FullProf). All on identical input parameters
and **without any fitting**. Each page defines the structure in code,
overlays each engine on the reference with a residual panel and
closeness metrics, and ends with a single agreement table.

Single-crystal pages compare the calculated F² of each reflection on a
y=x scatter instead of a profile overlay, and use `cryspy` only — the
sole engine with single-crystal Bragg support.

Each page also runs as a fast regression check (`pixi run script-tests`
and `pixi run notebook-tests`), so agreement is monitored over time.

Pages are grouped by **experiment type** (sample form, radiation probe,
and beam mode). Coverage grows to span every supported combination —
`pd-neut-cwl`, `pd-neut-tof`, `pd-xray`, `sg-neut-cwl`, `sg-neut-tof`,
and so on. The list below notes only what is specific to each page.

## Powder, neutron, constant wavelength

- [LBCO `pd-neut-cwl`](pd-neut-cwl_pv_lbco.ipynb) – La0.5Ba0.5CoO3
  (cubic perovskite); pseudo-Voigt, no asymmetry.
- [PbSO4 `pd-neut-cwl`](pd-neut-cwl_pv_pbso4.ipynb) – Anglesite;
  pseudo-Voigt, no asymmetry.
- [PbSO4 `pd-neut-cwl`](pd-neut-cwl_pv-asym_empir_pbso4.ipynb) –
  Anglesite; pseudo-Voigt with empirical (FullProf-style)
  axial-divergence asymmetry.
- [LaB6 `pd-neut-cwl`](pd-neut-cwl_tch-fcj_lab6.ipynb) – Lanthanum
  hexaboride; Thompson–Cox–Hastings with Finger–Cox–Jephcoat asymmetry
  plus SyCos/SySin peak-position corrections. Prepared skeleton, skipped
  — pending EasyDiffraction support for these features.

## Powder, neutron, time-of-flight

- [Si `pd-neut-tof`](pd-neut-tof_jvd_si.ipynb) – Silicon; Jorgensen–Von
  Dreele (pseudo-Voigt with back-to-back exponential asymmetry).
- [NaCaAlF `pd-neut-tof`](pd-neut-tof_jvd_ncaf.ipynb) – Na2Ca3Al2F14;
  Jorgensen–Von Dreele (pseudo-Voigt with back-to-back exponential
  asymmetry).

## Single crystal, neutron, constant wavelength

- [Pr2NiO4 `sg-neut-cwl`](sg-neut-cwl_pr2nio4.ipynb) – Pr2NiO4:Sr
  (K2NiF4-type, Fmmm); per-reflection F² against FullProf with
  anisotropic ADPs, partial occupancies, and a split interstitial
  oxygen. `cryspy` only; no peak profile (integrated intensities).
