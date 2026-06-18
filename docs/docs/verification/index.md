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

- [LBCO basic pseudo-Voigt](pd-neut-cwl_lbco_basic.ipynb) – verifies a
  baseline pseudo-Voigt powder pattern.
- [LBCO preferred orientation](pd-neut-cwl_lbco_preferred-orientation.ipynb)
  – verifies the March-Dollase preferred-orientation correction.
- [PbSO₄ basic pseudo-Voigt](pd-neut-cwl_pbso4_basic.ipynb) – verifies a
  baseline pseudo-Voigt powder pattern.
- [PbSO₄ Bérar-Baldinozzi asymmetry](pd-neut-cwl_pbso4_beba-asymmetry.ipynb)
  – verifies the empirical asymmetry workflow.
- [LaB₆ SyCos/SySin shifts](pd-neut-cwl_lab6_sycos-sysin.ipynb) – verifies
  sample-displacement and transparency peak-position corrections.
- [LaB₆ FCJ asymmetry](pd-neut-cwl_lab6_fcj-asymmetry.ipynb) – verifies the
  Finger-Cox-Jephcoat axial-divergence asymmetry reference.
- [LaB₆ absorption](pd-neut-cwl_lab6_absorption.ipynb) – verifies
  Debye-Scherrer absorption with FCJ asymmetry disabled.
- [LaB₆ absorption + FCJ asymmetry](pd-neut-cwl_lab6_absorption_fcj-asymmetry.ipynb)
  – verifies the combined absorption and FCJ reference.
- [Y₂O₃ beta ADPs](pd-neut-cwl_y2o3_beta-adp.ipynb) – verifies
  beta-tensor anisotropic ADPs with other correction models disabled.

## Powder, Neutron, Time-Of-Flight

- [Si Jorgensen profile](pd-neut-tof_si_jorgensen.ipynb) – verifies the
  Jorgensen back-to-back exponential profile.
- [Si Jorgensen-Von Dreele profile](pd-neut-tof_si_jorgensen-von-dreele.ipynb)
  – verifies the Jorgensen-Von Dreele pseudo-Voigt profile.
- [Na₂Ca₃Al₂F₁₄ Jorgensen-Von Dreele profile](pd-neut-tof_ncaf_jorgensen-von-dreele.ipynb)
  – verifies the NCAF time-of-flight pseudo-Voigt profile.

## Powder, X-Ray, Constant Wavelength

- [LiF single wavelength](pd-xray-cwl_lif_single.ipynb) – verifies the
  baseline Cu Kα₁ pseudo-Voigt pattern.
- [LiF polarization](pd-xray-cwl_lif_single_polarization.ipynb) – verifies
  the X-ray polarization correction.
- [LiF absorption](pd-xray-cwl_lif_single_absorption.ipynb) – verifies
  Debye-Scherrer absorption.
- [LiF doublet](pd-xray-cwl_lif_doublet.ipynb) – verifies Cu Kα₁/Kα₂
  doublet handling.
- [PbSO₄ round robin](pd-xray-cwl_pbso4_round-robin.ipynb) – verifies the
  anglesite X-ray round-robin case with empirical asymmetry.

## Single Crystal, Neutron, Constant Wavelength

- [Pr₂NiO₄ basic](sc-neut-cwl_pr2nio4_basic.ipynb) – verifies calculated
  F² values with anisotropic ADPs.
- [Tb₂Ti₂O₇ basic](sc-neut-cwl_tbti_basic.ipynb) – verifies no-extinction
  calculated F² values with anisotropic ADPs.
- [Tb₂Ti₂O₇ isotropic extinction](sc-neut-cwl_tbti_isotropic-extinction.ipynb)
  – verifies the isotropic extinction model.
