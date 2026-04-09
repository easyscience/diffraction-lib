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

# 1. Sample Model

## 1.1 Crystal Structure Parameters

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
|------------------------------------------------| --- | --- |
| Neutron scattering lengths (tabulated, CrysPy) | ✅  | ✅  |
| X-ray scattering factors (tabulated, CrysPy)   | ✅  | ✅  |
| Custom neutron scattering length               | 🗓  | 🗓  |
| Fractional coordinates _x, y, z_               | ✅  | ✅  |
| Occupancy                                      | ✅  | ✅  |
| Symmetry _wyckoff_letter_                      | ✅  | ✅  |

### Atomic Displacement Parameters (ADP)

| Feature                                         | LIB         | APP |
| ----------------------------------------------- | ----------- | --- |
| Isotropic Biso                                  | ✅          | 🗓  |
| Isotropic Uiso                                  | 🗓          | ✅  |
| Anisotropic Bani _B11, B22, B33, B12, B13, B23_ | 🗓`highest` | 🗓  |
| Anisotropic Uani _U11, U22, U33, U12, U13, U23_ | 🗓          | 🗓  |

---

## 1.2 Magnetic Structure Parameters

| Feature                                                 | LIB | APP |
| ------------------------------------------------------- | --- | --- |
| EPIC (Magnetic space groups, unpolarized and polarized) | 🗓  | 🗓  |

---

# 2. Experiment Model

## 2.1 Powder Diffraction

### Fitting Methods

| Feature                               | LIB | APP |
| ------------------------------------- | --- | --- |
| Rietveld refinement (full pattern)    | ✅  | ✅  |
| Le Bail refinement (profile matching) | 🗓  | 🗓  |

### Linked Phases

| Feature      | LIB | APP |
| ------------ | --- | --- |
| Scale factor | ✅  | ✅  |

### Excluded Regions

| Feature                                   | LIB | APP |
| ----------------------------------------- | --- | --- |
| Multiple regions<br>_start/end positions_ | ✅  | 🗓  |

---

### Background

| Feature                                           | LIB | APP |
| ------------------------------------------------- | --- | --- |
| Line segments type<br>_x, y_                      | ✅  | ✅  |
| Chebyshev polynomial type<br>_order, coefficient_ | ✅  | 🗓  |

### Preferred Orientation

| Feature                                    | LIB      | APP |
| ------------------------------------------ | -------- | --- |
| Basic preferred orientation model (CrysPy) | 🗓`high` | 🗓  |

### Instrument — Constant Wavelength

| Feature                                       | LIB | APP |
| --------------------------------------------- | --- | --- |
| Wavelength                                    | ✅  | ✅  |
| Second wavelength                             | 🚧  | 🗓  |
| 2θ offset                                     | ✅  | ✅  |
| Sample displacement correction _SyCos, SySin_ | 🚧  | 🗓  |

### Instrument — Time-of-Flight

| Feature                                                       | LIB | APP |
| ------------------------------------------------------------- | --- | --- |
| 2θ bank                                                       | ✅  | ✅  |
| d → TOF conversion<br>_reciprocal, offset, linear, quadratic_ | ✅  | ✅  |

### Peak Profile — Constant Wavelength

CrysPy: Pseudo-Voigt from FullProf.
Empirical asymmetry, 4 params (p1, p2, p3, p4) from FullProf.

| Feature                                                                                                                                                                            | LIB  | APP |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------| --- |
| Pseudo-Voigt + Empirical asymmetry<br>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br>Empirical asymmetry p1, p2, p3, p4_<br>(CrysPy)                                  | ✅    | ✅  |
| Thompson-Cox-Hastings Pseudo-Voigt + Finger-Cox-Jephcoat asymmetry<br>_Gaussian broadening U, V, W. Lorentzian broadening X, Y<br>Finger-Cox-Jephcoat asymmetry 1, 2_<br>(CrysFML) | ✅/🗓 | 🗓  |

### Peak Profile — Time-of-Flight

CrysPy peak_shape options:
- "Gauss": Jorgensen (back-to-back exponentials ⊗ Gaussian)
- "pseudo-Voigt": Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)
- "type0m": Double back-to-back exponentials ⊗ pseudo-Voigt (Z-Rietveld type 0m)

| Feature                                                                                                                                                                                                                            | LIB | APP |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| - | -- |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)<br>_Gaussian broadening σ₀, σ₁, σ₂<br>Back-to-back exponential rise α₀, α₁. Back-to-back exponential decay β₀, β₁_<br>(CrysPy)                                                    | ✅ | ✅ |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)<br>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br>Back-to-back exponential rise α₀, α₁. Back-to-back exponential decay β₀, β₁_<br>(CrysPy)   | 🗓 | ✅ |
| Double back-to-back exponentials ⊗ pseudo-Voigt [Z-Rietveld type0m]<br>_Gaussian broadening σ₀, σ₁, σ₂. Lorentzian broadening γ₀, γ₁, γ₂<br>Rise α₁, α₂. Fast decay β₀₀, β₀₁. Slow decay β₁₀. Switching r₀₁, r₀₂, r₀₃_<br>(CrysPy) | 🗓 | 🗓  |

| TOF profile                                                          | TOF source                                                        | Performance |
| -------------------------------------------------------------------- |-------------------------------------------------------------------| ---------- |
| Jorgensen (back-to-back exponentials ⊗ Gaussian)                     | Simpler TOF profile, including reactor-source TOF implementations | Fast       |
| Jorgensen-Von Dreele (back-to-back exponentials ⊗ pseudo-Voigt)      | Spallation-source TOF                                             | Slower       |
| Double back-to-back exponentials ⊗ pseudo-Voigt (Z-Rietveld type0m)  | Spallation-source TOF; more elaborate asymmetric profile          | Slowest           |

---

## 2.1.2 Total Scattering (Pair Distribution Function)

### Peak Profile

| Feature                                                                                                | LIB | APP |
| ------------------------------------------------------------------------------------------------------ | --- | --- |
| GaussianDampedSinc type<br>_cutoff q. broadening q. sharpening δ₁, δ₂<br>damping q, particle diameter_ | ✅  | 🗓  |

---

## 2.2 Single Crystal Diffraction

### Extinction

CrysPy's extinction is NOT Shelx-style. It's an analytical Becker-Coppens spherical model with 
Gauss or Lorentz mosaicity distribution

| Feature                               | LIB | APP |
| ------------------------------------- | --- | --- |
| Gaussian model: _radius, mosaicity_   | ✅  | ✅  |
| Lorentzian model: _radius, mosaicity_ | ✅  | ✅  |

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

## 2.3. Polarized Neutron Diffraction

| Feature                                        | LIB | APP |
| ---------------------------------------------- | --- | --- |
| EPIC (powders and single crystals, FR and SNP) | 🗓  | 🗓  |

---

# 3. Multi-Dataset Support

| Feature                           | LIB | APP |
| --------------------------------- | --- | --- |
| Multiple structural data blocks   | ✅  | ✅  |
| Multiple experimental data blocks | ✅  | 🗓  |

---

# 4. Analysis (Fitting)

### Refinement Algorithms

| Feature                                                         | LIB | APP |
| --------------------------------------------------------------- | --- | --- |
| Levenberg–Marquardt (numerical derivatives)<br>LMFIT minimizer  | ✅  | ✅  |
| Levenberg–Marquardt (analytical derivatives)<br>LMFIT minimizer | 🗓  | 🗓  |
| Derivative-free minimization<br>DFO-LS minimizer                | ✅  | ✅  |
| Bayesian analysis<br>BUMPS minimizer                            | 🗓  | 🗓  |

### Fit Strategies

| Feature                                                                                              | LIB | APP |
| ---------------------------------------------------------------------------------------------------- | --- | --- |
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
| Load project from disk | 🚧  | ✅  | 🗓  |
| Save project to disk   | ✅  | ✅  | 🗓  |

### SciCat Integration

| Feature                  | LIB | APP | CLI |
| ------------------------ | --- | --- | --- |
| Load project from SciCat | 🗓  | 🗓  | —   |
| Save project to SciCat   | 🗓  | 🗓  | —   |

### External Resources

| Feature                           | LIB | APP | CLI |
| --------------------------------- | --- | --- | --- |
| List available tutorial notebooks | —   | —   | ✅  |
| Download tutorial notebooks       | —   | —   | ✅  |

---

# 8. Visualization

## 8.1. Sample Model

### Crystal Structure

| Feature                                  | LIB | APP |
| ---------------------------------------- | --- |-----|
| Visualize unit cell                      | 🗓  | ✅/🗓  |
| Visualize multiple unit cells            | 🗓  | 🗓  |
| Visualize atom sites as spheres          | 🗓  | ✅   |
| Visualize atoms occupied same position   | 🗓  | 🗓  |
| Interactive mode<br>3D rotation, zooming | 🗓  | ✅   |
| Orthogonal unit cell                     | 🗓  | ✅   |
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

| Feature                                              | LIB | APP | CLI |
| ---------------------------------------------------- |-----| --- | --- |
| Live update of plots on parameter change with slider | —   | ✅  | —   |
| Live update of plots during refinement               | —   | ✅  | —   |
| Parameter evolution (sequential refinement)          | ✅/🗓  | 🗓  | —   |

### Fitting

| Feature                                   | LIB | APP | CLI |
| ----------------------------------------- | --- | --- | --- |
| Live update of plots                      | —   | ✅  | —   |
| Live update of fit quality (change in χ²) | ✅  | ✅  | ✅  |
| Plot correlation between parameters       | ✅  | 🗓  | —   |

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

# 10. Future Topics

Here, we list features that are not sorted into the above categories, but are
still on our radar for future development.

- Restrains (soft constraints, e.g. bond lengths, angles)
- Global optimization algorithms (e.g. simulated annealing)
- Incommensurate structures
- 2D Rietveld refinement
