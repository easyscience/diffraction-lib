---
title: Verification
icon: material/check-decagram
---

# :material-check-decagram: Verification

These pages compare EasyDiffraction calculations with reference
calculations. Bragg pages (powder/single-crystal) compare against
**FullProf**, an independent program. Pair-distribution-function pages
compare against a **direct `diffpy.pdffit2`** calculation — the same
library EasyDiffraction wraps, so those pages check wrapper fidelity
(correct parameter hand-off) rather than cross-validating the PDF
physics against an independent implementation. Each page focuses on one
experiment type or one additional model term, and feature names match
the [Features](../features/index.md) page. Some pages document a **known
difference** (EasyDiffraction does not yet match the reference for that
term); these are marked below and inside the notebook.

## Powder, Neutron, Constant Wavelength

### LaB6 structure

- [pd-neut-cwl LaB6 basic](pd-neut-cwl_LaB6_basic.ipynb) – baseline
  **Pseudo-Voigt** powder pattern (cryspy).
- [pd-neut-cwl LaB6 isotope](pd-neut-cwl_LaB6_11B.ipynb) –
  **isotope-specific neutron scattering length** (¹¹B).
- [pd-neut-cwl LaB6 sample displacement](pd-neut-cwl_LaB6_sycos-sysin.ipynb)
  – **sample displacement correction** (FullProf "SyCos, SySin"). _Known
  difference: cryspy's convention does not yet match FullProf._
- [pd-neut-cwl LaB6 FCJ asymmetry](pd-neut-cwl_LaB6_fcj-asymmetry.ipynb)
  – **Finger-Cox-Jephcoat asymmetry** (FullProf "Npr=7"). _Known
  difference: the cryspy CW profile has no FCJ term._
- [pd-neut-cwl LaB6 absorption](pd-neut-cwl_LaB6_absorption.ipynb) –
  **absorption correction (cylinder, Hewat)** (FullProf "muR").

### La0.5Ba0.5CoO3 structure

- [pd-neut-cwl LBCO basic](pd-neut-cwl_LBCO_basic.ipynb) – baseline
  **Pseudo-Voigt** powder pattern (cryspy).
- [pd-neut-cwl LBCO preferred orientation](pd-neut-cwl_LBCO_preferred-orientation.ipynb)
  – **March–Dollase preferred orientation** (FullProf "Nor=1").

### PbSO4 structure

- [pd-neut-cwl PbSO4 basic](pd-neut-cwl_PbSO4_basic.ipynb) – baseline
  **Pseudo-Voigt** powder pattern (cryspy).
- [pd-neut-cwl PbSO4 Bérar-Baldinozzi asymmetry](pd-neut-cwl_PbSO4_beba-asymmetry.ipynb)
  – **Pseudo-Voigt + Bérar-Baldinozzi asymmetry** (FullProf "Asy1-4").

### Y2O3 structure

- [pd-neut-cwl Y2O3 isotropic ADPs](pd-neut-cwl_Y2O3_isotropic-adp.ipynb)
  – baseline **isotropic ADPs** (Biso/Uiso).
- [pd-neut-cwl Y2O3 anisotropic β ADPs](pd-neut-cwl_Y2O3_beta-adp.ipynb)
  – **anisotropic β-tensor ADPs**.

## Powder, Neutron, Time-Of-Flight

### Fe structure

- [pd-neut-tof Fe Pseudo-Voigt](pd-neut-tof_Fe_pseudo-voigt.ipynb) –
  baseline **Pseudo-Voigt (non-convoluted)** TOF profile (FullProf
  "Npr=7" TOF).

### NCAF structure

- [pd-neut-tof NCAF Jorgensen-Von Dreele (Gaussian)](pd-neut-tof_NCAF_jorgensen-von-dreele.ipynb)
  – **Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)**
  profile with the Lorentzian terms (γ₀, γ₁, γ₂) forced to zero, i.e.
  the Gaussian case (FullProf "Npr=9").

### Si structure

- [pd-neut-tof Si Jorgensen](pd-neut-tof_Si_jorgensen.ipynb) –
  **Jorgensen (back-to-back exponentials ⊗ Gaussian)** profile (FullProf
  "Npr=9", Gaussian limit).
- [pd-neut-tof Si Jorgensen-Von Dreele](pd-neut-tof_Si_jorgensen-von-dreele.ipynb)
  – **Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)**
  profile with Lorentzian terms (FullProf "Npr=9"). _Known difference:
  cryspy TOF Lorentzian discrepancy._
- [pd-neut-tof Si Jorgensen-Von Dreele + size/strain](pd-neut-tof_Si_jorgensen-von-dreele-size-strain.ipynb)
  – **isotropic microstructural size/strain broadening** on the
  Jorgensen-Von Dreele profile (size*g/strain_g, size_l/strain_l).
  \_Known difference: requires the updated cryspy backend (TOF
  size/strain wiring + Jorgensen-Von Dreele fix, cryspy issue #49) and
  TOF scale.*

## Powder, X-Ray, Constant Wavelength

### LiF structure

- [pd-xray-cwl LiF single wavelength](pd-xray-cwl_LiF_single.ipynb) –
  baseline Cu Kα₁ **Pseudo-Voigt** pattern (cryspy and **crysfml**).
- [pd-xray-cwl LiF polarization](pd-xray-cwl_LiF_single_polarization.ipynb)
  – **X-ray Lorentz-polarization correction** (FullProf "Cthm,
  Rpolarz").
- [pd-xray-cwl LiF absorption](pd-xray-cwl_LiF_single_absorption.ipynb)
  – **absorption correction (cylinder, Hewat)** (FullProf "muR").
- [pd-xray-cwl LiF second wavelength](pd-xray-cwl_LiF_doublet.ipynb) –
  **second wavelength** (Cu Kα₁/Kα₂ doublet, FullProf "Lambda2, Ratio").
  The doublet is an EasyDiffraction-level implementation (the engine is
  run twice and summed by the intensity ratio).

### PbSO4 structure

- [pd-xray-cwl PbSO4 round robin](pd-xray-cwl_PbSO4_round-robin.ipynb) –
  anglesite X-ray round-robin case (**Pseudo-Voigt + Bérar-Baldinozzi
  asymmetry**).

## Single Crystal, Neutron, Constant Wavelength

### Pr2NiO4 structure

- [sc-neut-cwl Pr2NiO4 basic](sc-neut-cwl_Pr2NiO4_basic.ipynb) –
  calculated F² with **anisotropic β-tensor ADPs**.

### Tb2Ti2O7 structure

- [sc-neut-cwl Tb2Ti2O7 basic](sc-neut-cwl_Tb2Ti2O7_basic.ipynb) –
  baseline with **isotropic ADPs**.
- [sc-neut-cwl Tb2Ti2O7 isotropic extinction](sc-neut-cwl_Tb2Ti2O7_isotropic-extinction.ipynb)
  – **isotropic Becker-Coppens extinction** (Gaussian model). _Known
  difference: cryspy and FullProf use different extinction conventions._
- [sc-neut-cwl Tb2Ti2O7 anisotropic β ADPs](sc-neut-cwl_Tb2Ti2O7_anisotropic-adp.ipynb)
  – **anisotropic β-tensor ADPs**.

## Powder, Total Scattering (Pair Distribution Function)

### Ni structure

- [total-neut-cwl Ni Gaussian-damped sinc](total-neut-cwl_Ni_gaussian-damped-sinc.ipynb)
  – **Gaussian-damped sinc termination** PDF, neutron constant
  wavelength (pdffit2).

### Si structure

- [total-neut-tof Si Gaussian-damped sinc](total-neut-tof_Si_gaussian-damped-sinc.ipynb)
  – **Gaussian-damped sinc termination** PDF, neutron time-of-flight
  (pdffit2).

### NaCl structure

- [total-xray NaCl Gaussian-damped sinc](total-xray_NaCl_gaussian-damped-sinc.ipynb)
  – **Gaussian-damped sinc termination** PDF, X-ray (pdffit2).
