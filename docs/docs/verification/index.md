---
icon: material/check-decagram
---

# :material-check-decagram: Verification

This section compares EasyDiffraction's calculation engines against each
other and against external software (FullProf) on the **same** input
parameters, **without any fitting** — just calculated diffraction
patterns and clear closeness metrics. Each page defines the structure in
code, calculates the pattern with every supported engine, and overlays
each result on the reference with a residual panel and a closeness
table.

Each page also runs as a fast regression check (`pixi run script-tests`
and `pixi run notebook-tests`), so cross-engine agreement is monitored
over time. Coverage grows to span every supported experiment and
instrument combination.

The verification pages are organized into the following categories:

## Cross-engine

- [LBCO `pd-neut-cwl`](lbco-bragg-cwl.ipynb) – Compares the `cryspy` and
  `crysfml` engines on the La0.5Ba0.5CoO3 structure (HRPT, PSI). No
  external reference; the two engines are checked against each other.

## FullProf, constant wavelength

- [PbSO4 `pd-neut-cwl`](pbso4-bragg-cwl.ipynb) – Both engines compared
  against a FullProf reference for PbSO4 constant-wavelength neutron
  powder diffraction.
- [Al2O3 `pd-neut-cwl`](al2o3-bragg-cwl.ipynb) – Both engines compared
  against a FullProf reference for corundum (α-Al2O3).

## FullProf, time-of-flight

- [Al2O3 `pd-neut-tof`](al2o3-bragg-tof.ipynb) – Time-of-flight
  comparison for corundum using the Jorgensen–Von Dreele profile.
- [Si `pd-neut-tof`](si-bragg-tof.ipynb) – Time-of-flight comparison for
  silicon.
- [NaCaAlF `pd-neut-tof`](ncaf-bragg-tof.ipynb) – Time-of-flight
  comparison for Na2Ca3Al2F14.
