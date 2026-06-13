# EasyDiffraction Development Roadmap

LIB – Python library API  
APP – graphical application  
CLI – command-line interface

Legend:

- ✅ done
- 🚧 work in progress
- 🗓 planned
  - 🗓`highest` Urgent. Needs attention ASAP
  - 🗓`high` Should be prioritized soon
  - 🗓`medium` Normal/default priority
  - 🗓`low` Low importance
  - 🗓`lowest` Very low urgency
- — not applicable / not implemented

---

# 1. Structure Model

## 1.1 Crystal Structure

### Space Group

| Feature                            | LIB | APP |
| ---------------------------------- | --- | --- |
| Hermann-Mauguin space-group symbol | ✅  | ✅  |
| Space group IT number              | 🗓  | 🗓  |
| IT coordinate system code          | ✅  | ✅  |

### Cell

| Feature           | LIB | APP |
| ----------------- | --- | --- |
| Lengths _a, b, c_ | ✅  | ✅  |
| Angles _α, β, γ_  | ✅  | ✅  |

### Atom Sites

| Feature                                        | LIB | APP |
| ---------------------------------------------- | --- | --- |
| Neutron scattering lengths (tabulated, CrysPy) | ✅  | ✅  |
| X-ray scattering factors (tabulated, CrysPy)   | ✅  | ✅  |
| Custom neutron scattering length               | 🗓  | 🗓  |
| Fractional coordinates _x, y, z_               | ✅  | ✅  |
| Occupancy                                      | ✅  | ✅  |
| Symmetry _wyckoff_letter_                      | ✅  | ✅  |

### Atomic Displacement (ADP)

| Feature                                             | LIB | APP |
| --------------------------------------------------- | --- | --- |
| Isotropic _Biso_                                    | ✅  | 🗓  |
| Isotropic _Uiso_                                    | ✅  | ✅  |
| Anisotropic _Bani_ (_B11, B22, B33, B12, B13, B23_) | ✅  | 🗓  |
| Anisotropic _Uani_ (_U11, U22, U33, U12, U13, U23_) | ✅  | 🗓  |
| Anisotropic _β_ (_β11, β22, β33, β12, β13, β23_)    | ✅  | 🗓  |

---

## 1.2 Magnetic Structure - EPIC

| Feature                                               | LIB | APP |
| ----------------------------------------------------- | --- | --- |
| Magnetic Space Groups                                 | 🗓  | 🗓  |
| Irreducible representations                           | 🗓  | 🗓  |
| Magnetic propagation vector (_kx, ky, kz_)            | 🗓  | 🗓  |
| Magnetic moments (_mx, my, mz_)                       | 🗓  | 🗓  |
| Local Susceptibility (_𝜒11, 𝜒22, 𝜒33, 𝜒12, 𝜒13, 𝜒23_) | 🗓  | 🗓  |

---

# 2. Experiment Model

| Techniques                                           | LIB   | APP   |
| ---------------------------------------------------- | ----- | ----- |
| 2.1. Powder Diffraction                              | ✅/🗓 | ✅/🗓 |
| 2.1.1. Common features                               | ✅/🗓 | ✅/🗓 |
| 2.1.2. Standard Bragg diffraction (CWL)              | ✅/🗓 | ✅/🗓 |
| 2.1.2. Standard Bragg diffraction (TOF)              | ✅/🗓 | ✅/🗓 |
| 2.1.3. Total Scattering (Pair-Distribution Function) | ✅/🗓 | 🗓    |
| 2.2. Single-Crystal Diffraction (CWL)                | ✅/🗓 | ✅/🗓 |
| 2.2. Single-Crystal Diffraction (TOF)                | ✅/🗓 | ✅/🗓 |
| 2.3. Polarized Powder Diffraction                    | 🗓    | 🗓    |
| 2.3.1. Flipping-rathio method (TOF)                  | 🗓    | 🗓    |
| 2.3.1. Flipping-rathio method (CWL)                  | 🗓    | 🗓    |
| 2.4. Polarized Single-Crystal Diffraction            | 🗓    | 🗓    |
| 2.4.1. Flipping-rathio method (CWL)                  | 🗓    | 🗓    |
| 2.4.2. Flipping-rathio method (TOF)                  | 🗓    | 🗓    |
| 2.4.3. Spherical neutron polarimetry                 | 🗓    | 🗓    |

## 2.1. Powder Diffraction

## 2.1.1 Common features

### Linked Phases

| Feature      | LIB | APP |
| ------------ | --- | --- |
| Scale factor | ✅  | ✅  |

### Excluded Regions

| Feature                                   | LIB | APP |
| ----------------------------------------- | --- | --- |
| Multiple regions<br>_start/end positions_ | ✅  | 🗓  |

## 2.1.1 Standard Bragg diffraction

### Fitting Methods

| Feature                               | LIB | APP |
| ------------------------------------- | --- | --- |
| Rietveld refinement (full pattern)    | ✅  | ✅  |
| Le Bail refinement (profile matching) | 🗓  | 🗓  |

### Background

| Feature                                           | LIB | APP |
| ------------------------------------------------- | --- | --- |
| Line segments type<br>_x, y_                      | ✅  | ✅  |
| Chebyshev polynomial type<br>_order, coefficient_ | ✅  | 🗓  |
| Automatic background estimation<br>_one-call baseline (arpls/fabc), auto method_ | ✅ | 🗓 |

### Preferred Orientation

| Feature                                           | LIB | APP |
| ------------------------------------------------- | --- | --- |
| Basic preferred orientation model (March–Dollase) | ✅  | 🗓  |

### Instrument — Constant Wavelength

| Feature                                                  | LIB | APP |
| -------------------------------------------------------- | --- | --- |
| Wavelength                                               | ✅  | ✅  |
| Second wavelength                                        | 🗓  | 🗓  |
| 2θ offset                                                | ✅  | ✅  |
| Sample displacement correction (FullProf _SyCos, SySin_) | 🚧  | 🗓  |

### Instrument — Time-of-Flight

| Feature                                                       | LIB | APP |
| ------------------------------------------------------------- | --- | --- |
| 2θ bank                                                       | ✅  | ✅  |
| d → TOF conversion<br>_reciprocal, offset, linear, quadratic_ | ✅  | ✅  |

### Peak Profile — Constant Wavelength

| Feature                                                                                                                                                                            | LIB   | APP |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | --- |
| Pseudo-Voigt + Empirical asymmetry<br>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br>Empirical asymmetry p1, p2, p3, p4_<br>(CrysPy)                                  | ✅    | ✅  |
| Thompson-Cox-Hastings Pseudo-Voigt + Finger-Cox-Jephcoat asymmetry<br>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br>Finger-Cox-Jephcoat asymmetry 1, 2_<br>(CrysFML) | ✅/🗓 | 🗓  |

### Peak Profile — Time-of-Flight

| Feature                                                                                                                                                                                                                                         | LIB | APP |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | --- |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)<br>_Gaussian broadening σ₀, σ₁, σ₂<br>Back-to-back exponential rise α₀, α₁. Back-to-back exponential decay β₀, β₁_<br>(CrysPy "Gauss")                                                         | ✅  | ✅  |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)<br>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br>Back-to-back exponential rise α₀, α₁. Back-to-back exponential decay β₀, β₁_<br>(CrysPy "pseudo-Voigt") | ✅  | ✅  |
| Double back-to-back exponentials ⊗ pseudo-Voigt [Z-Rietveld type0m]<br>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br>Rise α₁, α₂. Fast decay β₀₀, β₀₁. Slow decay β₁₀. Switching r₀₁, r₀₂, r₀₃_<br>(CrysPy "type0m")     | ✅  | 🗓  |
| Ikeda-Carpenter ⊗ pseudo-Voigt<br>_Moderator pulse α₀, α₁, β₀, κ<br>Gaussian broadening σ². Lorentzian broadening γ_<br>(CrysFML)                                                                                                               | 🗓  | 🗓  |

| TOF profile                                                         | TOF source                                                        | Performance |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------- |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)                    | Simpler TOF profile, including reactor-source TOF implementations | Fast        |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)     | Spallation-source TOF                                             | Slower      |
| Double back-to-back exponentials ⊗ pseudo-Voigt (Z-Rietveld type0m) | Spallation-source TOF; more elaborate asymmetric profile          | Slowest     |
| Ikeda-Carpenter ⊗ pseudo-Voigt                                      | Spallation-source TOF; moderator pulse shape model                | Moderate    |

---

## 2.1.3 Total Scattering (Pair Distribution Function)

### Peak Profile

| Feature                                                                                                                  | LIB | APP |
| ------------------------------------------------------------------------------------------------------------------------ | --- | --- |
| Gaussian-damped sinc termination function<br>_cutoff q. broadening q. sharpening δ₁, δ₂<br>damping q, particle diameter_ | ✅  | 🗓  |

---

## 2.2 Single Crystal Diffraction

### Extinction

CrysPy's extinction is an analytical Becker-Coppens spherical model with
Gauss or Lorentz mosaicity distribution

| Feature                                               | LIB | APP |
| ----------------------------------------------------- | --- | --- |
| Becker-Coppens, Gaussian model: _radius, mosaicity_   | ✅  | ✅  |
| Becker-Coppens, Lorentzian model: _radius, mosaicity_ | ✅  | ✅  |
| Anisotropic extinction correction                     | 🗓  | 🗓  |

### Domains / Twinning

| Feature                                           | LIB | APP |
| ------------------------------------------------- | --- | --- |
| Twinning / domains for single-crystal diffraction | 🗓  | 🗓  |

### Instrument — Constant Wavelength

| Feature               | LIB | APP |
| --------------------- | --- | --- |
| Wavelength            | ✅  | ✅  |
| Half wavelength (λ/2) | 🗓  | 🗓  |

### Instrument — Time-of-Flight

| Feature                              | LIB | APP |
| ------------------------------------ | --- | --- |
| Individual wavelength per reflection | ✅  | 🗓  |

## 2.3. Polarized Neutron Powder Diffraction - EPIC

| Feature                      | LIB | APP |
| ---------------------------- | --- | --- |
| Flipping-rathio method (TOF) | 🗓  | 🗓  |
| Flipping-rathio method (CWL) | 🗓  | 🗓  |

## 2.3. Polarized Neutron Single Crystal Diffraction - EPIC

| Feature                       | LIB | APP |
| ----------------------------- | --- | --- |
| Flipping-rathio method (TOF)  | 🗓  | 🗓  |
| Flipping-rathio method (CWL)  | 🗓  | 🗓  |
| Spherical neutron polarimetry | 🗓  | 🗓  |

---

# 3. Multi-Dataset Support

| Feature                           | LIB | APP |
| --------------------------------- | --- | --- |
| Multiple structural data blocks   | ✅  | ✅  |
| Multiple experimental data blocks | ✅  | 🗓  |

---

# 4. Analysis (Fitting)

### Refinement Algorithms (numerical derivatives)

| Feature                                              | LIB | APP |
| ---------------------------------------------------- | --- | --- |
| Levenberg–Marquardt<br>LMFIT minimizer               | ✅  | ✅  |
| Levenberg–Marquardt<br>LMFIT minimizer (scipy-based) | ✅  | ✅  |
| Levenberg–Marquardt<br>BUMPS minimizer               | 🚧  | 🗓  |
| Derivative-free minimization<br>DFO-LS minimizer     | ✅  | ✅  |
| Bayesian analysis<br>BUMPS minimizer                 | 🗓  | 🗓  |

### Fit Strategies

| Feature                                                                                              | LIB | APP |
| ---------------------------------------------------------------------------------------------------- | --- | --- |
| Single fit of one experimental data block to one/multiple structural data block                      | ✅  | ✅  |
| Sequential fit of experimental data blocks                                                           | ✅  | 🗓  |
| Joint fit of experimental data blocks within the same calculation engine                             | ✅  | 🗓  |
| Joint fit of experimental data blocks using different calculation engines<br>(e.g. CrysPy + Pdffit2) | ✅  | 🗓  |
| Custom weighting for joint fit: _weight per dataset_                                                 | ✅  | 🗓  |

### Live Fitting

| Feature                                        | LIB | APP |
| ---------------------------------------------- | --- | --- |
| Live fitting during real-time data acquisition | 🗓  | 🗓  |

---

# 5. Refinement Execution

| Feature                                       | LIB | APP | CLI |
| --------------------------------------------- | --- | --- | --- |
| Scripted refinement workflow                  | ✅  | —   | —   |
| GUI-driven refinement workflow                | —   | ✅  | —   |
| Command-line refinement execution             | —   | —   | ✅  |
| Parameter modification                        | ✅  | ✅  | —   |
| Load individual structure or experiment files | ✅  | ✅  | —   |
| Project-based refinement                      | ✅  | ✅  | ✅  |
| Save refinement results to project            | ✅  | ✅  | ✅  |

---

# 6. Constraints

| Feature                        | LIB | APP   |
| ------------------------------ | --- | ----- |
| Automatic symmetry constraints | ✅  | ✅/🗓 |
| User-defined constraints       | ✅  | 🗓    |

---

# 7. Data Management

### Data Loading

| Feature                         | LIB | APP | CLI |
| ------------------------------- | --- | --- | --- |
| Load structure from CIF         | ✅  | ✅  | —   |
| Load experiment data from ASCII | ✅  | ✅  | —   |
| Load experiment data from CIF   | ✅  | ✅  | —   |

### Project Files

| Feature                | LIB | APP | CLI |
| ---------------------- | --- | --- | --- |
| Load project from disk | ✅  | ✅  | ✅  |
| Save project to disk   | ✅  | ✅  | ✅  |

### SciCat Integration

| Feature                  | LIB | APP | CLI |
| ------------------------ | --- | --- | --- |
| Load project from SciCat | 🗓  | 🗓  | —   |
| Save project to SciCat   | 🗓  | 🗓  | —   |

### External Resources

| Feature                           | LIB | APP | CLI |
| --------------------------------- | --- | --- | --- |
| List available tutorial notebooks | ✅  | —   | ✅  |
| Download tutorial notebooks       | ✅  | —   | ✅  |

---

# 8. Visualization

## 8.1. Sample Model

### Crystal Structure

| Feature                                  | LIB | APP |
| ---------------------------------------- | --- | --- |
| Visualize unit cell                      | 🗓  | ✅  |
| Visualize multiple unit cells            | 🗓  | 🗓  |
| Visualize atom sites as spheres          | 🗓  | ✅  |
| Visualize atoms occupied same position   | 🗓  | 🗓  |
| Visualize bonds                          | 🗓  | 🗓  |
| Visualize polyhedra                      | 🗓  | 🗓  |
| Interactive mode<br>3D rotation, zooming | 🗓  | ✅  |
| Orthogonal unit cell                     | 🗓  | ✅  |
| Non-orthogonal unit cell                 | 🗓  | 🗓  |

### Magnetic Structure

| Feature                              | LIB | APP |
| ------------------------------------ | --- | --- |
| Visualize magnetic moments as arrows | 🗓  | 🗓  |

## 8.2. Experiment

### Powder Diffraction

| Feature                              | LIB      | APP | CLI |
| ------------------------------------ | -------- | --- | --- |
| Plot experimental curve              | ✅       | ✅  | ✅  |
| Plot calculated curve                | ✅       | ✅  | ✅  |
| Plot residual curve                  | ✅       | ✅  | ✅  |
| Plot Bragg peaks                     | 🗓`high` | ✅  | —   |
| Interactive mode<br>zooming, panning | ✅       | ✅  | —   |

### Single Crystal Diffraction

| Feature                              | LIB | APP | CLI |
| ------------------------------------ | --- | --- | --- |
| Plot obs vs calc for reflections     | ✅  | ✅  | ✅  |
| Interactive mode<br>zooming, panning | ✅  | ✅  | —   |

## 8.3. Analysis

| Feature                                              | LIB   | APP | CLI |
| ---------------------------------------------------- | ----- | --- | --- |
| Live update of plots on parameter change with slider | —     | ✅  | —   |
| Live update of plots during refinement               | —     | ✅  | —   |
| Parameter evolution (sequential refinement)          | ✅/🗓 | 🗓  | —   |

### Fitting

| Feature                                   | LIB | APP | CLI |
| ----------------------------------------- | --- | --- | --- |
| Live update of plots                      | —   | ✅  | —   |
| Live update of fit quality (change in χ²) | ✅  | ✅  | ✅  |
| Plot correlation between parameters       | ✅  | 🗓  | ✅  |

---

# 9. User documentation

| Feature                             | LIB | APP   |
| ----------------------------------- | --- | ----- |
| New unified documentation structure | ✅  | 🗓    |
| Introduction                        | ✅  | ✅/🗓 |
| Installation and setup guide        | ✅  | ✅/🗓 |
| User guide                          | ✅  | ✅/🗓 |
| Tutorials                           | ✅  | 🗓    |
| API reference                       | ✅  | —     |

---

# 10. Unsorted features

- Restrains (soft constraints, e.g. bond lengths, angles)
- Refinement using analytical derivatives
- Global optimization algorithms (e.g. simulated annealing)
- Incommensurate structures
- 2D Rietveld refinement
