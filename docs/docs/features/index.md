---
title: Features
icon: material/clipboard-check-outline
---

# :material-clipboard-check-outline: Features

This page is the single source of truth for what EasyDiffraction can do
today and what is planned. Each capability is tracked across the three
ways you can use EasyDiffraction:

- **LIB** – Python library API
- **CLI** – command-line interface (text-based input and output)
- **APP** – graphical application

Implementation status:

- :white_check_mark: Done
- :ballot_box_with_check: Partially done
- :construction: Work in progress
- :date: Planned
  - :date: 5/5 – `highest` Urgent. Needs attention ASAP
  - :date: 4/5 – `high` Should be prioritized soon
  - :date: 3/5 – `medium` Normal/default priority
  - :date: 2/5 – `low` Low importance
  - :date: 1/5 – `lowest` Very low urgency
- — Not applicable

Each implemented capability lists the calculation engine(s) that provide
it (`cryspy`, `crysfml`, `pdffit2`), or `easydiffraction` where
EasyDiffraction performs it directly rather than through a calculation
engine. Structure-model inputs are shared
and consumed by every active engine. Where the backend uses a specific
profile keyword it is shown in quotes (e.g. `cryspy` "Gauss"). We also 
include `FullProf` cross-references to the equivalent `.pcr` entry where
applicable, to help users familiar with `FullProf` understand how their existing knowledge and workflows map to EasyDiffraction.

In the CLI column, :ballot_box_with_check: marks a capability that is
supported but set up by editing the project's text files (`.edi`/CIF)
in a separate editor — the command-line interface runs refinements
(`fit`, `display`, `undo`) but has no command to edit models,
parameters, or constraints directly.

---

# 1. Structure Model

## 1.1 Crystal Structure

### Space Group

| Feature<img width=450/>                                                | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Hermann-Mauguin space-group symbol<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Space group IT number                                                  | :date:             | :date:             | :date:             |
| IT coordinate system code<br/>- `cryspy` | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Cell

| Feature<img width=450/>                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Lengths _a, b, c_<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Angles _α, β, γ_<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Atom Sites

| Feature<img width=450/>                                                    | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| X-ray scattering factors (tabulated)<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Neutron scattering lengths (tabulated, natural element)<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Isotope-specific neutron scattering length<br/>_(e.g. ¹¹B, ²H — beyond the natural element)_<br/>- `cryspy` | :white_check_mark: | :white_check_mark: | :date:             |
| Custom neutron scattering length<br/>- `FullProf` (cross-ref) "Nsc (user-defined scattering)"                                           | :date:             | :date:             | :date:             |
| Fractional coordinates _x, y, z_<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2`  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Occupancy<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Symmetry _wyckoff_letter_<br/>- `easydiffraction` | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Atomic Displacement (ADP)

| Feature<img width=450/>                                                                | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Isotropic _Biso_<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2`                              | :white_check_mark: | :white_check_mark: | :date:             |
| Isotropic _Uiso_<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2`                              | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Anisotropic _Bani_ (_B11, B22, B33, B12, B13, B23_)<br/>- `cryspy`<br/>- `pdffit2`         | :white_check_mark: | :white_check_mark: | :date:             |
| Anisotropic _Uani_ (_U11, U22, U33, U12, U13, U23_)<br/>- `cryspy`<br/>- `pdffit2`         | :white_check_mark: | :white_check_mark: | :date:             |
| Anisotropic _β_ (_β11, β22, β33, β12, β13, β23_)<br/>- `cryspy`            | :white_check_mark: | :white_check_mark: | :date:             |

---

## 1.2 Magnetic Structure - EPIC

| Feature<img width=450/>                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Irreducible representations                           | :date:             | :date:             | :date:             |
| Magnetic Space Groups                                 | :date:             | :date:             | :date:             |
| Symmetry-adapted modes                                | :date:             | :date:             | :date:             |
| Magnetic propagation vector (_kx, ky, kz_)<br/>- `FullProf` (cross-ref) "Nvk (propagation vectors)"            | :date:             | :date:             | :date:             |
| Magnetic moments (_mx, my, mz_)<br/>- `FullProf` (cross-ref) "Rx, Ry, Rz"                       | :date:             | :date:             | :date:             |
| Local Susceptibility (_𝜒11, 𝜒22, 𝜒33, 𝜒12, 𝜒13, 𝜒23_) | :date:             | :date:             | :date:             |

---

# 2. Experiment Model

| Feature<img width=450/>                              | LIB<img width=40/>      | CLI<img width=39/>      | APP<img width=33/>      |
| ---------------------------------------------------- | ----------------------- | ----------------------- | ----------------------- |
| 2.1. Powder Diffraction                              | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.1.1. Common features                               | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.1.2. Standard Bragg diffraction (CWL)              | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.1.2. Standard Bragg diffraction (TOF)              | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.1.3. Total Scattering (Pair Distribution Function) | :ballot_box_with_check: | :ballot_box_with_check: | :date:                  |
| 2.2. Single-Crystal Diffraction                      | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.2.1. Single-Crystal Diffraction (CWL)              | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.2.2. Single-Crystal Diffraction (TOF)              | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.3. Polarized Powder Diffraction                    | :date:                  | :date:                  | :date:                  |
| 2.3.1. Flipping-ratio method (TOF)                   | :date:                  | :date:                  | :date:                  |
| 2.3.2. Flipping-ratio method (CWL)                   | :date:                  | :date:                  | :date:                  |
| 2.4. Polarized Single-Crystal Diffraction            | :date:                  | :date:                  | :date:                  |
| 2.4.1. Flipping-ratio method (CWL)                   | :date:                  | :date:                  | :date:                  |
| 2.4.2. Flipping-ratio method (TOF)                   | :date:                  | :date:                  | :date:                  |
| 2.4.3. XYZ Polarisation                              | :date:                  | :date:                  | :date:                  |
| 2.4.4. Spherical neutron polarimetry                 | :date:                  | :date:                  | :date:                  |

---

## 2.1. Powder Diffraction

## 2.1.1. Common features

### Linked Phases

| Feature<img width=450/>                                    | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Scale factor<br/>- `easydiffraction` | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Excluded Regions

| Feature<img width=450/>                    | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Multiple regions<br/>_start/end positions_<br/>- `easydiffraction` | :white_check_mark: | :white_check_mark: | :date:             |

## 2.1.2. Standard Bragg diffraction

### Fitting Methods

| Feature<img width=450/>                                            | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Rietveld refinement (full pattern)<br/>- `cryspy`<br/>- `crysfml`      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Le Bail refinement (profile matching)<br/>- `FullProf` (cross-ref) "Jbt=2 (profile matching)"                              | :date:             | :date:             | :date:             |

### Background

| Feature<img width=450/>                                                                          | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Line segments type _x, y_<br/>- `easydiffraction`<br/>- `FullProf` (cross-ref) "Nba" (linear interpolation points)           | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Chebyshev polynomial type _order, coefficient_<br/>- `easydiffraction`<br/>- `FullProf` (cross-ref) "Nba=0 (polynomial background)"                                                   | :white_check_mark: | :white_check_mark: | :date:             |
| Automatic background estimation<br/>_auto, arPLS, FABC, SNIP_<br/>- `easydiffraction`                | :white_check_mark: | :white_check_mark: | :date:             |

### Preferred Orientation

| Feature<img width=450/>                                                                                      | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| March–Dollase<br/> _march_r, random fraction, hkl axis_<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "Nor=1", "Pref1/2, Pr1/2/3" | :white_check_mark: | :white_check_mark: | :date:             |

### Instrument — Constant Wavelength

| Feature<img width=450/>                                                                          | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Wavelength<br/>- `cryspy`<br/>- `crysfml`<br/>- `FullProf` (cross-ref) "Lambda1"                                                            | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Second wavelength _λ₂, I₂/I₁ ratio_<br/>- `easydiffraction`<br/>- `FullProf` (cross-ref) "Lambda2, Ratio" | :white_check_mark: | :white_check_mark: | :date:             |
| 2θ offset<br/>- `cryspy`<br/>- `crysfml`<br/>- `FullProf` (cross-ref) "Zero"                             | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sample displacement correction<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "SyCos, SySin" | :white_check_mark: | :white_check_mark: | :date:             |
| Sample transparency correction<br/>- `cryspy` | :white_check_mark: | :white_check_mark: | :date:             |
| Absorption correction (cylinder, Hewat)<br/>- `easydiffraction`<br/>- `FullProf` (cross-ref) "muR" | :white_check_mark: | :white_check_mark: | :date:             |
| X-ray Lorentz-polarization correction<br/>_polarization coefficient, monochromator 2θ_<br/>- `cryspy`<br/>- `easydiffraction` (for `crysfml`)<br/>- `FullProf` (cross-ref) "Cthm, Rpolarz" | :white_check_mark: | :white_check_mark: | :date:             |

### Instrument — Time-of-Flight

| Feature<img width=450/>                                                                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| 2θ bank<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "2-theta bank"                               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| d → TOF conversion<br/>_offset, linear, quadratic_<br/>_(reciprocal defined but not yet wired)_<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "Dtt1, Dtt2, Zero;<br/>reciprocal = Dtt2t (Npr=10)" | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Peak Profile — Constant Wavelength

| Feature<img width=450/>                                                                                                                                                                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Thompson-Cox-Hastings pseudo-Voigt<br/>_Gaussian broadening U, V, W._<br/>_Lorentzian broadening X, Y_<br/>- `cryspy`<br/>- `crysfml`<br/>- `FullProf` (cross-ref) "Npr=7"                                          | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Thompson-Cox-Hastings pseudo-Voigt<br/>+ Bérar-Baldinozzi asymmetry<br/>_Gaussian broadening U, V, W._<br/>_Lorentzian broadening X, Y_<br/>_Bérar-Baldinozzi empirical asymmetry a₀, b₀, a₁, b₁_<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "Npr=7" + "Asy1-4" | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Thompson-Cox-Hastings pseudo-Voigt<br/>+ Finger-Cox-Jephcoat asymmetry<br/>_Gaussian broadening U, V, W._<br/>_Lorentzian broadening X, Y_<br/>_Finger-Cox-Jephcoat asymmetry 1, 2_<br/>- `crysfml`<br/>- `FullProf` (cross-ref) "Npr=7" + "S_L/D_L" | :white_check_mark: | :white_check_mark: | :date:             |

### Peak Profile — Time-of-Flight

| Feature<img width=450/>                                                                                                                                                                                                          | LIB<img width=40/>      | CLI<img width=39/>      | APP<img width=33/> |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| Pseudo-Voigt (non-convoluted)<br/>_Gaussian broadening σ₀, σ₁, σ₂._<br/>_Lorentzian broadening γ₀, γ₁, γ₂_<br/>- `cryspy` "non-conv-pseudo-Voigt"<br/>- `FullProf` (cross-ref) "Npr=7" (TOF)                                                | :white_check_mark:      | :white_check_mark:      | :date:             |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)<br/>_Gaussian broadening σ₀, σ₁, σ₂_<br/>_Back-to-back exponential rise α₀, α₁ and decay β₀, β₁_<br/>- `cryspy` "Gauss"<br/>- `FullProf` (cross-ref) "Npr=9" (Gaussian limit)           | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Jorgensen-Von Dreele<br/>(back-to-back exponentials ⊗ pseudo-Voigt)<br/>_Gaussian broadening σ₀, σ₁, σ₂._<br/>_Lorentzian broadening γ₀, γ₁, γ₂_<br/>_Back-to-back exponential rise α₀, α₁ and decay β₀, β₁_<br/>- `cryspy` "pseudo-Voigt"<br/>- `FullProf` (cross-ref) "Npr=9" | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Double back-to-back exponentials ⊗ pseudo-Voigt<br/>_Gaussian broadening σ₀, σ₁, σ₂._<br/>_Lorentzian broadening γ₀, γ₁, γ₂_<br/>_Rise α₁, α₂. Fast decay β₀₀, β₀₁._<br/>_Slow decay β₁₀. Switching r₀₁, r₀₂, r₀₃_<br/>- `cryspy` "type0m"<br/>- Z-Rietveld (cross-ref) "type0m"<br/>(no direct `FullProf` Npr; cf. Npr=10 two-component) | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Ikeda-Carpenter ⊗ pseudo-Voigt<br/>_Moderator pulse α₀, α₁, β₀, κ_<br/>_Gaussian broadening σ₀, σ₁, σ₂._<br/>_Lorentzian broadening γ₀, γ₁, γ₂_<br/>- `FullProf` (cross-ref) "Npr=13"                                                       | :date:                  | :date:                  | :date:             |
| Microstructural size/strain broadening<br/>_extends Jorgensen (Gaussian size_g, strain_g)_<br/>_and Jorgensen-Von Dreele (+ Lorentzian size_l, strain_l)_<br/>- available in `cryspy` backend;<br/>not yet exposed in `easydiffraction`<br/>- `FullProf` (cross-ref) "Iso-GSize, Iso-GStrain,<br/>Iso-LorSize, Iso-LorStrain"                                                          | :date:                  | :date:                  | :date:             |

TOF profiles by source type and relative performance:

| TOF profile                                                         | TOF source                                                        | Performance |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------- |
| Pseudo-Voigt (non-convoluted)                                       | Symmetric profile; simplest TOF case                              | Fastest     |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)                    | Simpler TOF profile, including reactor-source TOF implementations | Fast        |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)     | Spallation-source TOF                                             | Slower      |
| Double back-to-back exponentials ⊗ pseudo-Voigt (Z-Rietveld type0m) | Spallation-source TOF; more elaborate asymmetric profile          | Slowest     |
| Ikeda-Carpenter ⊗ pseudo-Voigt                                      | Spallation-source TOF; moderator pulse shape model                | Moderate    |

## 2.1.3. Total Scattering (Pair Distribution Function)

### Peak Profile

| Feature<img width=450/>                                                                                                                                                            | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Gaussian-damped sinc termination function<br/>_cutoff q (Qmax), broadening (Qbroad), sharpening δ₁, δ₂_<br/>_damping (Qdamp), particle diameter (spdiameter)_<br/>- `pdffit2`       | :white_check_mark: | :white_check_mark: | :date:             |

---

## 2.2. Single Crystal Diffraction

### Extinction

CrysPy's extinction is an analytical Becker-Coppens spherical model with
a Gaussian or Lorentzian mosaicity distribution.

| Feature<img width=450/>                                                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Isotropic Becker-Coppens, Gaussian model:<br/>_radius, mosaicity_<br/>- `cryspy`               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Isotropic Becker-Coppens, Lorentzian model:<br/>_radius, mosaicity_<br/>- `cryspy`             | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Anisotropic extinction correction<br/>- `FullProf` (cross-ref) "Ext (Line 29)"                                                        | :date:             | :date:             | :date:             |

### Twinning / domains

| Feature<img width=450/>                           | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Twinning / domains for single-crystal diffraction | :date:             | :date:             | :date:             |

### Instrument — Constant Wavelength

| Feature<img width=450/>                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------- | ------------------ | ------------------ | ------------------ |
| Wavelength<br/>- `cryspy`<br/>- `FullProf` (cross-ref) "Lambda1"                  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Half wavelength (λ/2)<br/>- `FullProf` (cross-ref) "x-Lambda/2"                    | :date:             | :date:             | :date:             |

### Instrument — Time-of-Flight

| Feature<img width=450/>                            | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Individual wavelength per reflection<br/>- `cryspy`  | :white_check_mark: | :white_check_mark: | :date:             |

---

## 2.3. Polarized Neutron Powder Diffraction - EPIC

| Feature<img width=450/>     | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------- | ------------------ | ------------------ | ------------------ |
| Flipping-ratio method (TOF) | :date:             | :date:             | :date:             |
| Flipping-ratio method (CWL) | :date:             | :date:             | :date:             |

## 2.4. Polarized Neutron Single-Crystal Diffraction - EPIC

| Feature<img width=450/>       | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------- | ------------------ | ------------------ | ------------------ |
| Flipping-ratio method (TOF)   | :date:             | :date:             | :date:             |
| Flipping-ratio method (CWL)   | :date:             | :date:             | :date:             |
| XYZ Polarisation              | :date:             | :date:             | :date:             |
| Spherical neutron polarimetry | :date:             | :date:             | :date:             |

---

# 3. Multi-Dataset Support

| Feature<img width=450/>           | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------- | ------------------ | ------------------ | ------------------ |
| Multiple structural data blocks   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Multiple experimental data blocks | :white_check_mark: | :white_check_mark: | :date:             |

---

# 4. Analysis (Fitting)

### Calculation Modes

| Feature<img width=450/>                                                                                                                       | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Calculate diffraction pattern for fitting/comparison<br/>against simulated or measured data<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2`              | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Calculate diffraction pattern for simple view<br/>without fitting/comparison against<br/>simulated or measured data<br/>- `cryspy`<br/>- `crysfml`<br/>- `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Calculate structure factors<br/>- `cryspy`                                                                                                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Refinement Algorithms (numerical derivatives)

| Feature<img width=450/>                                     | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Levenberg–Marquardt<br/>LMFIT minimizer                     | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Levenberg–Marquardt<br/>LMFIT minimizer (scipy-based)       | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Levenberg–Marquardt<br/>BUMPS minimizer                     | :white_check_mark: | :white_check_mark: | :date:             |
| Derivative-free minimization<br/>DFO-LS minimizer           | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Nelder-Mead<br/>BUMPS Amoeba minimizer | :white_check_mark: | :white_check_mark: | :date:             |
| Differential evolution<br/>BUMPS DE minimizer | :white_check_mark: | :white_check_mark: | :date:             |

### Bayesian Analysis (sampling)

| Feature<img width=450/>                         | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------- | ------------------ | ------------------ | ------------------ |
| MCMC sampling<br/>BUMPS DREAM minimizer         | :white_check_mark: | :white_check_mark: | :date:             |
| Affine-invariant ensemble sampling<br/>emcee    | :white_check_mark: | :white_check_mark: | :date:             |
| Resume sampling<br/>BUMPS DREAM minimizer       | :white_check_mark: | :white_check_mark: | :date:             |
| Resume sampling<br/>emcee                       | :white_check_mark: | :white_check_mark: | :date:             |

### Fit Strategies

| Feature<img width=450/>                                                                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Single fit of one experimental data block<br/>to one or more structural data blocks                   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sequential fit of experimental data blocks                                                            | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit of experimental data blocks<br/>within the same calculation engine                          | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit of experimental data blocks using<br/>different calculation engines (e.g. CrysPy + Pdffit2) | :white_check_mark: | :white_check_mark: | :date:             |
| Custom weighting for joint fit: _weight per dataset_                                                  | :white_check_mark: | :white_check_mark: | :date:             |

### Live Fitting

| Feature<img width=450/>                        | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Live fitting during real-time data acquisition | :date:             | :date:             | :date:             |

---

# 5. Refinement Execution

| Feature<img width=450/>                       | LIB<img width=40/> | CLI<img width=39/>      | APP<img width=33/> |
| --------------------------------------------- | ------------------ | ----------------------- | ------------------ |
| GUI-driven refinement workflow                | —                  | —                       | :white_check_mark: |
| Command-line refinement execution             | —                  | :white_check_mark:      | —                  |
| Scripted refinement workflow                  | :white_check_mark: | —                       | —                  |
| Parameter modification                        | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Load individual structure or experiment files | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Project-based refinement                      | :white_check_mark: | :white_check_mark:      | :white_check_mark: |
| Sequential refinement                         | :white_check_mark: | :white_check_mark:      | :date:             |
| Save refinement results to project            | :white_check_mark: | :white_check_mark:      | :white_check_mark: |
| Undo last fit                                 | :white_check_mark: | :white_check_mark:      | :date:             |

---

# 6. Constraints

| Feature<img width=450/>                                                                            | LIB<img width=40/> | CLI<img width=39/>      | APP<img width=33/>      |
| -------------------------------------------------------------------------------------------------- | ------------------ | ----------------------- | ----------------------- |
| Automatic symmetry constraints                                                                     | :white_check_mark: | :white_check_mark:      | :ballot_box_with_check: |
| User-defined constraints<br/>Basic types, e.g.:<br/>"biso_Ba = biso_La"<br/>"occ_Ba = 1 - occ_La"  | :white_check_mark: | :ballot_box_with_check: | :date:                  |

---

# 7. Data Management

### Project Files

Project files are a way to save and load the full state of a refinement,
including the structure model, experimental data, fit settings, and
results.

| Feature<img width=450/>     | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------- | ------------------ | ------------------ | ------------------ |
| Load full project from disk | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Save full project to disk   | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Data Loading

| Feature<img width=450/>                     | LIB<img width=40/> | CLI<img width=39/>      | APP<img width=33/> |
| ------------------------------------------- | ------------------ | ----------------------- | ------------------ |
| Add structure (to project) from CIF         | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add structure (to project) from edi         | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add experiment data (to project) from CIF   | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add experiment data (to project) from edi   | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add experiment data (to project) from ASCII | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add experiment data (to project) from NeXus | :date:             | :date:                  | :date:             |

### SciCat Integration

| Feature<img width=450/>       | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------- | ------------------ | ------------------ | ------------------ |
| Load full project from SciCat | :date:             | :date:             | :date:             |
| Save full project to SciCat   | :date:             | :date:             | :date:             |

### External Resources

| Feature<img width=450/>           | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------- | ------------------ | ------------------ | ------------------ |
| List available tutorial notebooks | :white_check_mark: | :white_check_mark: | —                  |
| Download tutorial notebooks       | :white_check_mark: | :white_check_mark: | —                  |

---

# 8. Visualization

## 8.1. Structure

### Crystal Structure

| Feature<img width=450/>                   | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/>      |
| ----------------------------------------- | ------------------ | ------------------ | ----------------------- |
| Visualize unit cell                       | :white_check_mark: | :date:             | :ballot_box_with_check: |
| Visualize multiple unit cells             | :date:             | :date:             | :date:                  |
| Visualize atom sites as spheres           | :white_check_mark: | :date:             | :white_check_mark:      |
| Visualize atoms occupied same position    | :white_check_mark: | :date:             | :date:                  |
| Visualize bonds                           | :white_check_mark: | :date:             | :date:                  |
| Visualize polyhedra                       | :date:             | :date:             | :date:                  |
| Interactive mode<br/>3D rotation, zooming | :white_check_mark: | :date:             | :white_check_mark:      |

### Magnetic Structure

| Feature<img width=450/>           | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------- | ------------------ | ------------------ | ------------------ |
| Visualize magnetic moments        | :date:             | :date:             | :date:             |
| Visualize magnetization densities | :date:             | :date:             | :date:             |

---

## 8.2. Experiment

### Powder Diffraction

| Feature<img width=450/>               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------- | ------------------ | ------------------ | ------------------ |
| Plot experimental curve               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot calculated curve                 | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot residual curve                   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot Bragg peaks                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Interactive mode<br/>zooming, panning | :white_check_mark: | —                  | :white_check_mark: |

### Single Crystal Diffraction

| Feature<img width=450/>               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------- | ------------------ | ------------------ | ------------------ |
| Plot obs vs calc for reflections      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Interactive mode<br/>zooming, panning | :white_check_mark: | —                  | :white_check_mark: |

---

## 8.3. Analysis

| Feature<img width=450/>                               | LIB<img width=40/>      | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------- | ----------------------- | ------------------ | ------------------ |
| Live update of plots on parameter change with slider  | —                       | —                  | :white_check_mark: |
| Live update of plots during refinement                | —                       | —                  | :white_check_mark: |
| Live update of fit quality (change in χ²)<br/>_table_ | :white_check_mark:      | :white_check_mark: | —                  |
| Live update of fit quality (change in χ²)<br/>_chart_ | :date:                  | —                  | :date:             |
| Parameter evolution (sequential refinement)           | :white_check_mark:      | :white_check_mark: | :date:             |
| Correlation between parameters                        | :white_check_mark:      | :white_check_mark: | :date:             |

---

# 9. User documentation

| Feature<img width=450/>             | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/>      |
| ----------------------------------- | ------------------ | ------------------ | ----------------------- |
| New unified documentation structure | :white_check_mark: | :white_check_mark: | :date:                  |
| Introduction                        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Features                            | :white_check_mark: | :white_check_mark: | :date:                  |
| Installation and setup guide        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| User guide                          | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Tutorials                           | :white_check_mark: | :date:             | :date:                  |
| Verification                        | :white_check_mark: | :white_check_mark: | :date:                  |
| Command-line interface              | —                  | :white_check_mark: | —                       |
| Quick Reference                     | :white_check_mark: | :white_check_mark: | :date:                  |
| API reference                       | :white_check_mark: | —                  | —                       |

---

# 10. Unsorted features

| Feature<img width=450/>                                                   | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Set free parameters by category<br/>(e.g. all atomic positions, all ADPs)     | :date:             | :date:             | :date:             |
| Add category with fit quality metrics<br/>(e.g. chi2, R-factors)              | :date:             | :date:             | :date:             |
| Restraints (soft constraints, e.g. bond lengths, angles)                  | :date:             | :date:             | :date:             |
| Refinement using analytical derivatives                                   | :date:             | :date:             | :date:             |
| Global optimization algorithms (e.g. simulated annealing)                 | :date:             | :date:             | :date:             |
| Incommensurate structures                                                 | :date:             | :date:             | :date:             |
| 2D Rietveld refinement                                                     | :date:             | :date:             | :date:             |
| Built-in refinement strategies<br/>for common refinement workflows            | :date:             | :date:             | :date:             |
| Chatbot window for natural-language requests<br/>during the analysis process  | :date:             | —                  | —                  |
