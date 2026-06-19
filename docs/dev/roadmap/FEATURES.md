User interface components:

- LIB – Python library API
- CLI – Command-line interface (with text-based input and output)
- APP – Graphical application

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

---

# 1. Structure Model

## 1.1 Crystal Structure

### Space Group

| Feature<img width=450/>            | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------- | ------------------ | ------------------ | ------------------ |
| Hermann-Mauguin space-group symbol | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Space group IT number              | :date:             | :date:             | :date:             |
| IT coordinate system code          | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Cell

| Feature<img width=450/> | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------- | ------------------ | ------------------ | ------------------ |
| Lengths _a, b, c_       | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Angles _α, β, γ_        | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Atom Sites

| Feature<img width=450/>                        | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------- | ------------------ | ------------------ | ------------------ |
| X-ray scattering factors (tabulated, CrysPy)   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Neutron scattering lengths (tabulated, CrysPy) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Custom neutron scattering length               | :date:             | :date:             | :date:             |
| Fractional coordinates _x, y, z_               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Occupancy                                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Symmetry _wyckoff_letter_                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Atomic Displacement (ADP)

| Feature<img width=450/>                             | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Isotropic _Biso_                                    | :white_check_mark: | :white_check_mark: | :date:             |
| Isotropic _Uiso_                                    | :construction:     | :construction:     | :white_check_mark: |
| Anisotropic _Bani_ (_B11, B22, B33, B12, B13, B23_) | :construction:     | :construction:     | :date:             |
| Anisotropic _Uani_ (_U11, U22, U33, U12, U13, U23_) | :construction:     | :construction:     | :date:             |

---

## 1.2 Magnetic Structure - EPIC

| Feature<img width=450/>                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Irreducible representations                           | :date:             | :date:             | :date:             |
| Magnetic Space Groups                                 | :date:             | :date:             | :date:             |
| Symmetry-adapted modes                                | :date:             | :date:             | :date:             |
| Magnetic propagation vector (_kx, ky, kz_)            | :date:             | :date:             | :date:             |
| Magnetic moments (_mx, my, mz_)                       | :date:             | :date:             | :date:             |
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
| 2.4.3. XYZ Polarisation                 | :date:                  | :date:                  | :date:                  |
| 2.4.4. Spherical neutron polarimetry                 | :date:                  | :date:                  | :date:                  |

---

## 2.1. Powder Diffraction

## 2.1.1. Common features

### Linked Phases

| Feature<img width=450/> | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------- | ------------------ | ------------------ | ------------------ |
| Scale factor            | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Excluded Regions

| Feature<img width=450/>                    | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Multiple regions<br/>_start/end positions_ | :white_check_mark: | :white_check_mark: | :date:             |

## 2.1.2. Standard Bragg diffraction

### Fitting Methods

| Feature<img width=450/>               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------- | ------------------ | ------------------ | ------------------ |
| Rietveld refinement (full pattern)    | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Le Bail refinement (profile matching) | :date:             | :date:             | :date:             |

### Background

| Feature<img width=450/>                        | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ---------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Chebyshev polynomial type _order, coefficient_ | :white_check_mark: | :white_check_mark: | :date:             |
| Line segments type _x, y_                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Line segments type _x, y_ (auto-detection)     | :date:             | :date:             | :date:             |

### Preferred Orientation

| Feature<img width=450/>                             | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Exponential function (FullProf "Nor=0": _G1, G2_) | :date:         | :date:         | :date:             |
| Modified March's function (FullProf "Nor=1": _G1, G2_, CrysPy) | :date: 4/5         | :date: 4/5         | :date:             |

### Instrument — Constant Wavelength

| Feature<img width=450/>                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Wavelength                                               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Second wavelength                                        | :date:             | :date:             | :date:             |
| 2θ offset                                                | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sample displacement correction (FullProf: _SyCos, SySin_) | :date:             | :date:             | :date:             |

### Instrument — Time-of-Flight

| Feature<img width=450/>                                        | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| -------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| 2θ bank                                                        | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| d → TOF conversion<br/>_reciprocal, offset, linear, quadratic_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Peak Profile — Constant Wavelength

| Feature<img width=450/>                                                                                                                                                                           | LIB<img width=40/>      | CLI<img width=39/>      | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| pseudo-Voigt + Bérar-Baldinozzi empirical asymmetry<br/>_Broadening U, V, W. Mixing X, eta0<br/>(FullProf "Npr=5", "UVWX, Shape1") <br/>Bérar-Baldinozzi empirical asymmetry_<br/>(FullProf "Asy1-4")                                              |  :date:    |  :date:   | :date: |
| Thompson-Cox-Hastings pseudo-Voigt + Bérar-Baldinozzi empirical asymmetry<br/>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br/>(FullProf "Npr 7", CrysPy)<br/>Bérar-Baldinozzi empirical asymmetry_<br/>(FullProf "Asy1-4", CrysPy)                                              | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Thompson-Cox-Hastings pseudo-Voigt + Finger-Cox-Jephcoat asymmetry<br/>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br/>(FullProf "Npr 7")<br/>Finger-Cox-Jephcoat asymmetry_<br/>(FullProf "S_L/D_L") | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |

### Peak Profile — Time-of-Flight

| Feature<img width=450/>                                                                                                                                                                                                                         | LIB<img width=40/>      | CLI<img width=39/>      | APP<img width=33/> |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| pseudo-Voigt<br/>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂_<br/>(FullProf "Npr 7", CrysPy "non-conv-pseudo-Voigt")                                                                                                   | :date:                  | :date:                  | :date:             |
| Ikeda-Carpenter ⊗ pseudo-Voigt<br/>_Moderator pulse α₀, α₁, β₀, κ<br/>Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂_<br/>(FullProf "Npr 13")                                                                                                   | :date:                  | :date:                  | :date:             |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)<br/>_Gaussian broadening σ₀, σ₁, σ₂<br/>Back-to-back exponential rise α₀, α₁ and decay β₀, β₁_<br/>(CrysPy "Gauss")                                                                            | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)<br/>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br/>Back-to-back exponential rise α₀, α₁ and decay β₀, β₁_<br/>(CrysPy "pseudo-Voigt")                    | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Double back-to-back exponentials ⊗ pseudo-Voigt<br/>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br/>Rise α₁, α₂. Fast decay β₀₀, β₀₁. Slow decay β₁₀. Switching r₀₁, r₀₂, r₀₃_<br/>(CrysPy "type0m", Z-Rietveld "type0m") | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |

## 2.1.3. Total Scattering (Pair Distribution Function)

### Peak Profile

| Feature<img width=450/>                                                                                                              | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Gaussian-damped sinc termination function<br/>_cutoff q. broadening q. sharpening δ₁, δ₂<br/>damping q, particle diameter_ (Pdffit2) | :white_check_mark: | :white_check_mark: | :date:             |

---

## 2.2. Single Crystal Diffraction

### Extinction

| Feature<img width=450/>                                                  | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------------------------------ | ------------------ | ------------------ | ------------------ |
| Isotropic Becker-Coppens, Gaussian model: _radius, mosaicity_ (CrysPy)   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Isotropic Becker-Coppens, Lorentzian model: _radius, mosaicity_ (CrysPy) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Anisotropic extinction correction                                        | :date:             | :date:             | :date:             |

### Twinning / domains

| Feature<img width=450/>                           | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Twinning / domains for single-crystal diffraction | :date:             | :date:             | :date:             |

### Instrument — Constant Wavelength

| Feature<img width=450/> | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------- | ------------------ | ------------------ | ------------------ |
| Wavelength              | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Half wavelength (λ/2)   | :date:             | :date:             | :date:             |

### Instrument — Time-of-Flight

| Feature<img width=450/>              | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ------------------------------------ | ------------------ | ------------------ | ------------------ |
| Individual wavelength per reflection | :white_check_mark: | :white_check_mark: | :date:             |

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
| XYZ Polarisation   | :date:             | :date:             | :date:             |
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

| Feature<img width=450/>                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Calculate diffraction pattern for fitting/comparison against simulated or measured data              | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Calculate diffraction pattern for simple view without fitting/comparison against simulated or measured data             | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Calculate structure factors              | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Refinement Algorithms (numerical derivatives)

| Feature<img width=450/>                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Levenberg–Marquardt<br/>LMFIT minimizer               | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Levenberg–Marquardt<br/>LMFIT minimizer (scipy-based) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Levenberg–Marquardt<br/>BUMPS minimizer               | :construction:     | :construction:     | :date:             |
| Derivative-free minimization<br/>DFO-LS minimizer     | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Bayesian analysis<br/>BUMPS minimizer                 | :date:             | :date:             | :date:             |

### Fit Strategies

| Feature<img width=450/>                                                                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Single fit of one experimental data block to one or more structural<br/>data blocks                   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sequential fit of experimental data blocks                                                            | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit of experimental data blocks within the same calculation<br/>engine                          | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit of experimental data blocks using different calculation<br/>engines (e.g. CrysPy + Pdffit2) | :white_check_mark: | :white_check_mark: | :date:             |
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
| Sequential refinement                         | :white_check_mark: | :date:                  | :date:             |
| Save refinement results to project            | :white_check_mark: | :white_check_mark:      | :white_check_mark: |

---

# 6. Constraints

| Feature<img width=450/>                                                                           | LIB<img width=40/> | CLI<img width=39/>      | APP<img width=33/>      |
| ------------------------------------------------------------------------------------------------- | ------------------ | ----------------------- | ----------------------- |
| Automatic symmetry constraints                                                                    | :white_check_mark: | :white_check_mark:      | :ballot_box_with_check: |
| User-defined constraints<br/>Basic types, e.g.:<br/>"biso_Ba = biso_La"<br/>"occ_Ba = 1 - occ_La" | :white_check_mark: | :ballot_box_with_check: | :date:                  |

---

# 7. Data Management

### Project Files

Project files are a way to save and load the full state of a refinement, including the structure model, experimental data, fit settings, and results.

| Feature<img width=450/> | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| ----------------------- | ------------------ | ------------------ | ------------------ |
| Load full project from disk  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Save full project to disk    | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### Data Loading

| Feature<img width=450/>                     | LIB<img width=40/> | CLI<img width=39/>      | APP<img width=33/> |
| ------------------------------------------- | ------------------ | ----------------------- | ------------------ |
| Add structure (to project) from CIF         | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
| Add experiment data (to project) from CIF   | :white_check_mark: | :ballot_box_with_check: | :white_check_mark: |
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
| Visualize unit cell                       | :date:             | :date:             | :ballot_box_with_check: |
| Visualize multiple unit cells             | :date:             | :date:             | :date:                  |
| Visualize atom sites as spheres           | :date:             | :date:             | :white_check_mark:      |
| Visualize atoms occupied same position    | :date:             | :date:             | :date:                  |
| Visualize bonds                           | :date:             | :date:             | :date:                  |
| Visualize polyhedra                       | :date:             | :date:             | :date:                  |
| Interactive mode<br/>3D rotation, zooming | :date:             | :date:             | :white_check_mark:      |

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
| Plot Bragg peaks                      | :date: 5/5         | —                  | :white_check_mark: |
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
| Parameter evolution (sequential refinement)           | :ballot_box_with_check: | —                  | :date:             |
| Correlation between parameters                        | :white_check_mark:      | :white_check_mark: | :date:             |

---

# 9. User documentation

| Feature<img width=450/>             | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/>      |
| ----------------------------------- | ------------------ | ------------------ | ----------------------- |
| New unified documentation structure | :white_check_mark: | :white_check_mark: | :date:                  |
| Introduction                        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Installation and setup guide        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| User guide                          | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Tutorials                           | :white_check_mark: | :date:             | :date:                  |
| API reference                       | :white_check_mark: | —                  | —                       |

---

# 10. Unsorted features

| Feature<img width=450/>                                               | LIB<img width=40/> | CLI<img width=39/> | APP<img width=33/> |
| --------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Set free parameters by category (e.g. all atomic positions, all ADPs) |                    |                    |                    |
| Add category with fit quality metrics (e.g. chi2, R-factors)          |                    |                    |                    |
| Restraints (soft constraints, e.g. bond lengths, angles)              |                    |                    |                    |
| Refinement using analytical derivatives                               |                    |                    |                    |
| Global optimization algorithms (e.g. simulated annealing)             |                    |                    |                    |
| Incommensurate structures                                             |                    |                    |                    |
| 2D Rietveld refinement                                                |                    |                    |                    |
| Built-in refinement strategies for common refinement workflows                                               |                    |                    |                    |
| Chatbot window for natural-language requests during the analysis process                                             |                    | —                   |    —                |
