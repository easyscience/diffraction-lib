---
title: Verification
icon: material/check-decagram
---

# :material-check-decagram: Verification

These pages compare EasyDiffraction calculations with FullProf reference
calculations. Each page focuses on one experiment type or one additional
model term, and pages with known calculator differences mark that status
inside the notebook.

## Powder, Neutron, Constant Wavelength

### LBCO

- [pd-neut-cwl LBCO basic pseudo-Voigt](pd-neut-cwl_LBCO_basic.ipynb) –
  verifies a _baseline_ pseudo-Voigt powder pattern.
- [pd-neut-cwl LBCO preferred orientation](pd-neut-cwl_LBCO_preferred-orientation.ipynb)
  – verifies the **preferred-orientation** correction.

### PbSO4

- [pd-neut-cwl PbSO4 basic pseudo-Voigt](pd-neut-cwl_PbSO4_basic.ipynb)
  – verifies a _baseline_ pseudo-Voigt powder pattern.
- [pd-neut-cwl PbSO4 Berar-Baldinozzi asymmetry](pd-neut-cwl_PbSO4_beba-asymmetry.ipynb)
  – verifies the **empirical asymmetry** correction.

### LaB6

- [pd-neut-cwl LaB6 basic](pd-neut-cwl_LaB6_basic.ipynb) – verifies the
  _baseline_ LaB6 powder pattern.
- [pd-neut-cwl LaB6 11B isotope](pd-neut-cwl_LaB6_11B.ipynb) – verifies
  the **11B isotope** contribution.
- [pd-neut-cwl LaB6 SyCos/SySin shifts](pd-neut-cwl_LaB6_sycos-sysin.ipynb)
  – verifies the **SyCos/SySin** peak-position corrections.
- [pd-neut-cwl LaB6 FCJ asymmetry](pd-neut-cwl_LaB6_fcj-asymmetry.ipynb)
  – verifies the **Finger-Cox-Jephcoat asymmetry** correction.
- [pd-neut-cwl LaB6 absorption](pd-neut-cwl_LaB6_absorption.ipynb) –
  verifies **Debye-Scherrer absorption** correction.

### Y2O3

- [pd-neut-cwl Y2O3 isotropic ADPs](pd-neut-cwl_Y2O3_isotropic-adp.ipynb)
  – verifies the isotropic-ADP _baseline_.
- [pd-neut-cwl Y2O3 beta ADPs](pd-neut-cwl_Y2O3_beta-adp.ipynb) –
  verifies **beta-tensor anisotropic ADPs**...

## Powder, Neutron, Time-Of-Flight

- [pd-neut-tof Si Jorgensen profile](pd-neut-tof_Si_jorgensen.ipynb) –
  verifies the **Jorgensen back-to-back exponential** profile.
- [pd-neut-tof Si Jorgensen-Von Dreele profile](pd-neut-tof_Si_jorgensen-von-dreele.ipynb)
  – verifies the **Jorgensen-Von Dreele pseudo-Voigt** ... with
  Lorentzian terms.
- [pd-neut-tof NCAF Jorgensen-Von Dreele profile](pd-neut-tof_NCAF_jorgensen-von-dreele.ipynb)
  – verifies the **Jorgensen-Von Dreele pseudo-Voigt** ... without
  Lorentzian terms.

## Powder, X-Ray, Constant Wavelength

### LiF

- [pd-xray-cwl LiF single wavelength](pd-xray-cwl_LiF_single.ipynb) –
  verifies the _baseline_ Cu K-alpha1 pseudo-Voigt pattern.
- [pd-xray-cwl LiF polarization](pd-xray-cwl_LiF_single_polarization.ipynb)
  – verifies the **X-ray polarization** correction.
- [pd-xray-cwl LiF absorption](pd-xray-cwl_LiF_single_absorption.ipynb)
  – verifies **Debye-Scherrer absorption** correction.
- [pd-xray-cwl LiF doublet](pd-xray-cwl_LiF_doublet.ipynb) – verifies Cu
  **K-alpha1/K-alpha2 doublet** handling.

### PbSO4

- [pd-xray-cwl PbSO4 round robin](pd-xray-cwl_PbSO4_round-robin.ipynb) –
  verifies the anglesite X-ray round-robin case with empirical
  asymmetry.

## Powder, Total Scattering

### NaCl

- [pd-xray-cwl-total NaCl gaussian-damped sinc](pd-xray-cwl-total_NaCl_gaussian-damped-sinc.ipynb)
  – verifies the **X-ray PDF** calculations.

### Ni

- [pd-neut-cwl-total Ni gaussian-damped sinc](pd-neut-cwl-total_Ni_gaussian-damped-sinc.ipynb)
  – verifies the **neutron constant wavelength PDF** calculations.

### Si

- [pd-neut-tof-total Si gaussian-damped sinc](pd-neut-tof-total_Si_gaussian-damped-sinc.ipynb)
  – verifies the **neutron time-of-flight PDF** calculations.

## Single Crystal, Neutron, Constant Wavelength

### Pr2NiO4

- [sc-neut-cwl Pr2NiO4 basic](sc-neut-cwl_Pr2NiO4_basic.ipynb) –
  verifies calculated F2 values with anisotropic ADPs.

### Tb2Ti2O7

- [sc-neut-cwl Tb2Ti2O7 basic](sc-neut-cwl_Tb2Ti2O7_basic.ipynb) –
  verifies no-extinction calculated F2 values with anisotropic ADPs.
- [sc-neut-cwl Tb2Ti2O7 isotropic extinction](sc-neut-cwl_Tb2Ti2O7_isotropic-extinction.ipynb)
  – verifies the isotropic extinction model.
