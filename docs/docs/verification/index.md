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

Each page also runs as a fast regression check (`pixi run script-tests`
and `pixi run notebook-tests`), so agreement is monitored over time.

Pages are grouped by **experiment type** (sample form, radiation probe,
and beam mode). Coverage grows to span every supported combination —
`pd-neut-cwl`, `pd-neut-tof`, `pd-xray`, `sg-neut-cwl`, `sg-neut-tof`,
and so on. The list below notes only what is specific to each page.

## Powder, neutron, constant wavelength

- [LBCO `pd-neut-cwl`](lbco-bragg-cwl.ipynb) – La0.5Ba0.5CoO3 (HRPT,
  PSI); pseudo-Voigt, no asymmetry. No FullProf reference yet, so only
  the engines are compared.
- [PbSO4 `pd-neut-cwl`](pbso4-bragg-cwl.ipynb) – Anglesite;
  pseudo-Voigt, no asymmetry.
- [Al2O3 `pd-neut-cwl`](al2o3-bragg-cwl.ipynb) – Corundum (α-Al2O3);
  pseudo-Voigt, no asymmetry.
- [LaB6 `pd-neut-cwl`](lab6-bragg-cwl.ipynb) – Lanthanum hexaboride;
  Thompson–Cox–Hastings with Finger–Cox–Jephcoat asymmetry plus
  SyCos/SySin peak-position corrections. Prepared skeleton, skipped —
  pending EasyDiffraction support for these features.

## Powder, neutron, time-of-flight

- [Al2O3 `pd-neut-tof`](al2o3-bragg-tof.ipynb) – Corundum (α-Al2O3);
  Jorgensen–Von Dreele (pseudo-Voigt with back-to-back exponential
  asymmetry).
- [Si `pd-neut-tof`](si-bragg-tof.ipynb) – Silicon; Jorgensen–Von Dreele
  (pseudo-Voigt with back-to-back exponential asymmetry).
- [NaCaAlF `pd-neut-tof`](ncaf-bragg-tof.ipynb) – Na2Ca3Al2F14;
  Jorgensen–Von Dreele (pseudo-Voigt with back-to-back exponential
  asymmetry).
