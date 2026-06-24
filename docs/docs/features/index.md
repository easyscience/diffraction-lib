---
title: Features
icon: material/clipboard-check-outline
---

# :material-clipboard-check-outline: Features

EasyDiffraction calculates diffraction patterns from a structural model
and instrument settings, and refines that model against measured data.
This page gives a complete overview of **what it can do today and what
is planned**, across powder and single-crystal diffraction, total
scattering (PDF), and the analysis tools around them.

## Calculation engines

Most of the physics is computed by a pluggable **calculation engine**.
Each engine is described on the
[Analysis](../user-guide/analysis-workflow/analysis.md) page.

- [`cryspy`](../user-guide/analysis-workflow/analysis.md#cryspy-calculator)
  — Bragg diffraction, Python library.
- [`crysfml`](../user-guide/analysis-workflow/analysis.md#crysfml-calculator)
  — Bragg diffraction, Fortran library with Python bindings.
- [`pdffit2`](../user-guide/analysis-workflow/analysis.md#pdffit2-calculator)
  — Total scattering (Pair Distribution Function), Python library.
- `easydiffraction` — extra corrections around the engine (e.g.
  background, scale).

## How to read this page

Each capability is tracked across the three ways to use EasyDiffraction:

- **LIB** — Python library
- **CLI** — command-line interface
- **APP** — graphical application

The status icons:

- :white_check_mark: Done
- :ballot_box_with_check: Partially done — available with at least one
  engine/interface
- :construction: Work in progress
- :date: Planned (no priority yet) · 5/5 `highest` · 4/5 `high` · 3/5
  `medium` · 2/5 `low` · 1/5 `lowest`
- :material-cancel: Not available / not applicable — the
  engine/interface does not provide this
- :material-help-circle: Unknown — support not yet confirmed for this
  engine/interface

??? note "How the columns are scored"

    The **LIB** column aggregates the per-engine lines in the Feature
    cell (the engines are the library backends): :white_check_mark: when
    every relevant engine is done (engines that do not apply are marked
    :material-cancel:), and :ballot_box_with_check: when at least one
    engine is done but others are in progress or planned. The **CLI**
    and **APP** columns show whether the feature is available in those
    two interfaces.

??? note "Using the command-line interface"

    The CLI runs the refinement workflow — `fit`, `display`, `undo`.
    Models, parameters, constraints, and report options are set by
    editing the project text files (`.edi`/CIF) in your own editor,
    rather than through dedicated CLI commands. A :white_check_mark: in
    the CLI column means the capability is reachable through this
    edit-then-run workflow.

??? note "Icons inside the Feature cell"

    Each line in the Feature cell carries its own icon:

    - The **engine** lines show per-engine status, e.g.
      :white_check_mark: `cryspy` (done) or :date: `crysfml` (planned).
      A backend keyword is shown in quotes (e.g. `cryspy` "Gauss").
    - :material-link-variant: cross-references the equivalent FullProf
      `.pcr` entry, to help users coming from FullProf.
    - :material-check-decagram: links to the
      [Verification](../verification/index.md) page where the
      calculation is cross-checked against an independent reference.

??? note "Epics shown as single rows"

    Large areas still on the roadmap — magnetic structures, polarized
    neutron diffraction, 2D Rietveld, incommensurate structures — are
    listed as one top-level row each. They are **epics** that will be
    broken into detailed rows once work starts. Already-implemented areas
    are shown in full detail.

---

## 1. Structure Model

### 1.1. Crystal Structure

#### Space Group

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                            | LIB                     | CLI                     | APP                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| Hermann-Mauguin space-group symbol<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`                                                         | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Space group IT number<br/>- :date: `easydiffraction`                                                                                                                                               | :date:                  | :date:                  | :date:             |
| IT coordinate system code<br/>- :white_check_mark: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :material-cancel: `pdffit2`<br/>- :material-link-variant: `FullProf` ":1" (origin choice) | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |

</div>

#### Cell

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                   | LIB                | CLI                | APP                |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Lengths _a, b, c_<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2` | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Angles _α, β, γ_<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`  | :white_check_mark: | :white_check_mark: | :white_check_mark: |

</div>

#### Atom Sites

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                             | LIB                     | CLI                     | APP                |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| X-ray scattering factors (tabulated)<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`                                                                                                        | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Neutron scattering lengths for natural elements (tabulated)<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`                                                                                 | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Isotope-specific neutron scattering length _(e.g. ¹¹B, ²H)_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_LaB6_11B.ipynb)<br/>- :material-help-circle: `crysfml`<br/>- :material-help-circle: `pdffit2` | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Custom neutron scattering length<br/>- :material-cancel: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :material-help-circle: `pdffit2`<br/>- :material-link-variant: `FullProf` "Nsc (user-defined scattering)"                            | :date:                  | :date:                  | :date:             |
| Fractional coordinates _x, y, z_<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`                                                                                                            | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Occupancy<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`                                                                                                                                   | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Symmetry _wyckoff_letter_<br/>- :white_check_mark: `easydiffraction`                                                                                                                                                                                | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |

</div>

#### Atomic Displacement (ADP)

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                                | LIB                     | CLI                     | APP                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| Isotropic _Biso_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_Y2O3_isotropic-adp.ipynb)<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`<br/>- :white_check_mark: `easydiffraction` (B/U/β conversion)               | :white_check_mark:      | :white_check_mark:      | :date:             |
| Isotropic _Uiso_<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2`<br/>- :white_check_mark: `easydiffraction` (B/U/β conversion)                                                                                                 | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Anisotropic _Bani_ (_B11…B23_)<br/>- :white_check_mark: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :white_check_mark: `pdffit2`<br/>- :white_check_mark: `easydiffraction` (B/U/β conversion)                                                                               | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Anisotropic _Uani_ (_U11…U23_)<br/>- :white_check_mark: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :white_check_mark: `pdffit2`<br/>- :white_check_mark: `easydiffraction` (B/U/β conversion)                                                                               | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Anisotropic _β_ (_β11…β23_)<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_Y2O3_beta-adp.ipynb)<br/>- :material-help-circle: `crysfml`<br/>- :material-help-circle: `pdffit2`<br/>- :white_check_mark: `easydiffraction` (B/U/β conversion) | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |

</div>

!!! note

    CrysFML refines only isotropic ADPs today; for anisotropic atoms it
    uses the isotropic-equivalent _B_, so true anisotropic refinement in
    `crysfml` is unconfirmed (:material-help-circle: on the anisotropic
    rows). EasyDiffraction stores ADPs type-neutrally and converts
    between _B_, _U_, and _β_ for each engine, so the `easydiffraction`
    line marks that conversion. `pdffit2` works in _U_; its _β_ support
    is likewise unconfirmed.

---

### 1.2. Magnetic Structure

Magnetic structure refinement is an **epic** (one row per area for now).

<div class="ed-matrix" markdown="1">

| Feature                                                                                                         | LIB    | CLI    | APP    |
| --------------------------------------------------------------------------------------------------------------- | ------ | ------ | ------ |
| Irreducible representations                                                                                     | :date: | :date: | :date: |
| Magnetic Space Groups                                                                                           | :date: | :date: | :date: |
| Symmetry-adapted modes                                                                                          | :date: | :date: | :date: |
| Magnetic propagation vector (_kx, ky, kz_)<br/>- :material-link-variant: `FullProf` "Nvk (propagation vectors)" | :date: | :date: | :date: |
| Magnetic moments (_mx, my, mz_)<br/>- :material-link-variant: `FullProf` "Rx, Ry, Rz"                           | :date: | :date: | :date: |
| Local Susceptibility (_𝜒11…𝜒23_)                                                                                | :date: | :date: | :date: |
| Magnetic domains                                                                                                | :date: | :date: | :date: |

</div>

---

## 2. Experiment Model

<div class="ed-matrix" markdown="1">

| Technique                                                         | LIB                     | CLI                     | APP                     |
| ----------------------------------------------------------------- | ----------------------- | ----------------------- | ----------------------- |
| [2.1. Powder Diffraction](#21-powder-diffraction)                 | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| [2.2. Single-Crystal Diffraction](#22-single-crystal-diffraction) | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| 2.3. Polarized Powder Diffraction — EPIC                          | :date:                  | :date:                  | :date:                  |
| 2.4. Polarized Single-Crystal Diffraction — EPIC                  | :date:                  | :date:                  | :date:                  |

</div>

---

### 2.1. Powder Diffraction

#### Common features

##### Linked Phases

<div class="ed-matrix" markdown="1">

| Feature                                                 | LIB                | CLI                | APP                |
| ------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Scale factor<br/>- :white_check_mark: `easydiffraction` | :white_check_mark: | :white_check_mark: | :white_check_mark: |

</div>

##### Excluded Regions

<div class="ed-matrix" markdown="1">

| Feature                                                                            | LIB                | CLI                | APP    |
| ---------------------------------------------------------------------------------- | ------------------ | ------------------ | ------ |
| Multiple regions: _start/end positions_<br/>- :white_check_mark: `easydiffraction` | :white_check_mark: | :white_check_mark: | :date: |

</div>

#### Standard Bragg diffraction

##### Fitting Methods

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                           | LIB                | CLI                | APP                |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Rietveld refinement (full pattern)<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`                                                                           | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Le Bail refinement (profile matching)<br/>- :material-cancel: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :material-link-variant: `FullProf` "Jbt=2 (profile matching)" | :date:             | :date:             | :date:             |

</div>

##### Background

Background curves are evaluated by EasyDiffraction and added to the
calculated pattern; the engine is not involved.

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                             | LIB                | CLI                | APP                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Line segments type: _position, intensity_<br/>- :white_check_mark: `easydiffraction`<br/>- :material-link-variant: `FullProf` "Nba" (linear interpolation points)   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Chebyshev polynomial type: _order, coefficient_<br/>- :white_check_mark: `easydiffraction`<br/>- :material-link-variant: `FullProf` "Nba=0 (polynomial background)" | :white_check_mark: | :white_check_mark: | :date:             |
| Automatic background estimation: _auto_ or _arPLS, FABC, SNIP_<br/>- :white_check_mark: `easydiffraction`                                                           | :white_check_mark: | :white_check_mark: | :date:             |

</div>

##### Preferred Orientation

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                             | LIB                     | CLI                     | APP    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------ |
| March–Dollase: _march_r, random fraction, hkl axis_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_LBCO_preferred-orientation.ipynb)<br/>- :construction: `crysfml`<br/>- :material-link-variant: `FullProf` "Nor=1", "Pref1/2, Pr1/2/3" | :ballot_box_with_check: | :ballot_box_with_check: | :date: |

</div>

##### Instrument — Constant Wavelength

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                                                                          | LIB                     | CLI                     | APP                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| Wavelength: _λ_<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :material-link-variant: `FullProf` "Lambda1"                                                                                                                                                                                          | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Second wavelength: _λ₂, I₂/I₁ ratio_<br/>- :white_check_mark: `easydiffraction` (Kα₁/Kα₂ doublet; engine run twice) [:material-check-decagram:](../verification/pd-xray-cwl_LiF_doublet.ipynb)<br/>- :material-cancel: `cryspy`<br/>- :construction: `crysfml`<br/>- :material-link-variant: `FullProf` "Lambda2, Ratio"         | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| 2θ offset<br/>- :white_check_mark: `easydiffraction`<br/>- :material-link-variant: `FullProf` "Zero"                                                                                                                                                                                                                             | :white_check_mark:      | :white_check_mark:      | :white_check_mark: |
| Sample displacement and transparency corrections<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_LaB6_sycos-sysin.ipynb)<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "SyCos, SySin"                                                                                | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Absorption correction (cylinder, Hewat)<br/>- :white_check_mark: `easydiffraction` [:material-check-decagram:](../verification/pd-neut-cwl_LaB6_absorption.ipynb)<br/>- :material-link-variant: `FullProf` "muR"                                                                                                                 | :white_check_mark:      | :white_check_mark:      | :date:             |
| X-ray Lorentz-polarization correction: _polarization coefficient, monochromator 2θ_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-xray-cwl_LiF_single_polarization.ipynb)<br/>- :white_check_mark: `easydiffraction` (for `crysfml`)<br/>- :material-link-variant: `FullProf` "Cthm, Rpolarz" | :white_check_mark:      | :white_check_mark:      | :date:             |

</div>

##### Instrument — Time-of-Flight

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                 | LIB                     | CLI                     | APP                |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| 2θ bank<br/>- :white_check_mark: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "2-theta bank"                                                                                                | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |
| d → TOF conversion: _offset, linear, quadratic (reciprocal defined but not yet wired)_<br/>- :white_check_mark: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Zero, Dtt1, Dtt2, Dtt_1overd" | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |

</div>

!!! note

    CrysFML's TOF branch is not yet functional (it parses TOF input but
    returns zero intensities), so TOF profiles and TOF instrument parameters
    are `cryspy`-only today; `crysfml` is marked :date:.

##### Peak Profile — Common (CWL + TOF)

Applies to every Bragg peak profile below, in both constant-wavelength
and time-of-flight modes.

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                             | LIB                     | CLI                     | APP    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------ |
| Peak-range cutoff (speed vs accuracy)<br/>_cutoff in FWHMs; 0 = full range_<br/>- :white_check_mark: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "WDT" | :ballot_box_with_check: | :ballot_box_with_check: | :date: |

</div>

##### Peak Profile — Constant Wavelength

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                                                                                                                                              | LIB                | CLI                | APP                |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Thompson-Cox-Hastings pseudo-Voigt<br/>_Gaussian broadening U, V, W<br/>Lorentzian broadening X, Y_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_LaB6_basic.ipynb)<br/>- :white_check_mark: `crysfml` [:material-check-decagram:](../verification/pd-xray-cwl_LiF_single.ipynb)<br/>- :material-link-variant: `FullProf` "Npr=7"                        | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Thompson-Cox-Hastings pseudo-Voigt + Bérar-Baldinozzi asymmetry<br/>_Gaussian broadening U, V, W<br/>Lorentzian broadening X, Y_<br/>_Bérar-Baldinozzi asymmetry a₀, b₀, a₁, b₁_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/pd-neut-cwl_PbSO4_beba-asymmetry.ipynb)<br/>- :material-cancel: `crysfml`<br/>- :material-link-variant: `FullProf` "Npr=7" + "Asy1-4" | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Thompson-Cox-Hastings pseudo-Voigt + Finger-Cox-Jephcoat asymmetry<br/>_Gaussian broadening U, V, W<br/>Lorentzian broadening X, Y_<br/>_Finger-Cox-Jephcoat asymmetry 1, 2_<br/>- :material-cancel: `cryspy`<br/>- :white_check_mark: `crysfml` [:material-check-decagram:](../verification/pd-neut-cwl_LaB6_fcj-asymmetry.ipynb)<br/>- :material-link-variant: `FullProf` "Npr=7" + "S_L/D_L"      | :white_check_mark: | :white_check_mark: | :date:             |

</div>

##### Peak Profile — Time-of-Flight

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | LIB                     | CLI                     | APP                |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ------------------ |
| Pseudo-Voigt (non-convoluted)<br/>_Gaussian σ₀, σ₁, σ₂, size_g, strain_g<br/>Lorentzian broadening γ₀, γ₁, γ₂, size_l, strain_l_<br/>- :white_check_mark: `cryspy` "non-conv-pseudo-Voigt" [:material-check-decagram:](../verification/pd-neut-tof_Fe_pseudo-voigt.ipynb)<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Npr=7" (TOF)                                                                                                                                                                                                                                             | :ballot_box_with_check: | :ballot_box_with_check: | :date:             |
| Jorgensen (back-to-back exp ⊗ Gaussian)<br/>_Gaussian broadening σ₀, σ₁, σ₂, size_g, strain_g<br/>Asymmetry rise α₀, α₁; decay β₀, β₁_<br/>- :white_check_mark: `cryspy` "Gauss" [:material-check-decagram:](../verification/pd-neut-tof_Si_jorgensen.ipynb)<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Npr=9" (Gaussian limit)                                                                                                                                                                                                                                               | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |
| Jorgensen-Von Dreele (back-to-back exp ⊗ pseudo-Voigt)<br/>_Gaussian broadening σ₀, σ₁, σ₂, size_g, strain_g<br/>Lorentzian broadening γ₀, γ₁, γ₂, size_l, strain_l<br/>Asymmetry rise α₀, α₁; decay β₀, β₁_<br/>- :white_check_mark: `cryspy` "pseudo-Voigt" [:material-check-decagram:](../verification/pd-neut-tof_Si_jorgensen-von-dreele.ipynb) (size/strain [:material-check-decagram:](../verification/pd-neut-tof_Si_jorgensen-von-dreele-size-strain.ipynb))<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Npr=9"; "Iso-GSize, Iso-GStrain, Iso-LorSize, Iso-LorStrain" | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |
| Double back-to-back exp ⊗ pseudo-Voigt<br/>_Gaussian broadening σ₀, σ₁, σ₂, size_g, strain_g<br/>Lorentzian broadening γ₀, γ₁, γ₂, size_l, strain_l<br/>Asymmetry rise α₁, α₂; fast decay β₀₀, β₀₁; slow decay β₁₀; switching r₀₁, r₀₂, r₀₃_<br/>- :white_check_mark: `cryspy` "type0m"<br/>- :material-link-variant: Z-Rietveld "type0m" (no direct `FullProf` Npr; cf. Npr=10)                                                                                                                                                                                                                    | :white_check_mark:      | :white_check_mark:      | :date:             |
| Ikeda-Carpenter ⊗ pseudo-Voigt<br/>_Gaussian broadening σ₀, σ₁, σ₂<br/>Lorentzian broadening γ₀, γ₁, γ₂<br/>Moderator pulse α₀, α₁, β₀, κ_<br/>- :date: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Npr=13"                                                                                                                                                                                                                                                                                                                                                           | :date:                  | :date:                  | :date:             |

</div>

#### Total Scattering (Pair Distribution Function)

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                                                                                                 | LIB                | CLI                | APP    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------ |
| Gaussian-damped sinc termination<br/>_cutoff Qmax, broadening Qbroad, sharpening δ₁, δ₂,<br/> damping Qdamp, particle diameter spdiameter_<br/>- :white_check_mark: `pdffit2` [:material-check-decagram:](../verification/total-neut-cwl_Ni_gaussian-damped-sinc.ipynb) | :white_check_mark: | :white_check_mark: | :date: |

</div>

---

### 2.2. Single Crystal Diffraction

#### Extinction

CrysPy's extinction is an analytical Becker-Coppens spherical model with
a Gaussian or Lorentzian mosaicity distribution.

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                      | LIB                | CLI                | APP                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Isotropic Becker-Coppens, Gaussian model: _radius, mosaicity_<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/sc-neut-cwl_Tb2Ti2O7_isotropic-extinction.ipynb) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Isotropic Becker-Coppens, Lorentzian model: _radius, mosaicity_<br/>- :white_check_mark: `cryspy`                                                                                            | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Anisotropic extinction correction<br/>- :material-cancel: `cryspy`<br/>- :material-help-circle: `crysfml`<br/>- :material-link-variant: `FullProf` "Ext-Model=4 (anisotropic)"               | :date:             | :date:             | :date:             |

</div>

#### Structural twinning

<div class="ed-matrix" markdown="1">

| Feature                                                                          | LIB    | CLI    | APP    |
| -------------------------------------------------------------------------------- | ------ | ------ | ------ |
| Structural twinning<br/>- :date: `cryspy`<br/>- :material-help-circle: `crysfml` | :date: | :date: | :date: |

</div>

#### Instrument — Constant Wavelength

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                  | LIB                     | CLI                     | APP                |
| ------------------------------------------------------------------------------------------------------------------------ | ----------------------- | ----------------------- | ------------------ |
| Wavelength<br/>- :white_check_mark: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "Lambda1"   | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |
| Half wavelength (λ/2)<br/>- :date: `cryspy`<br/>- :date: `crysfml`<br/>- :material-link-variant: `FullProf` "x-Lambda/2" | :date:                  | :date:                  | :date:             |

</div>

#### Instrument — Time-of-Flight

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                                                    | LIB                     | CLI                     | APP    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- | ----------------------- | ------ |
| Individual wavelength per reflection<br/>- :white_check_mark: `cryspy` [:material-check-decagram:](../verification/sc-neut-tof_taurine_basic.ipynb)<br/>- :material-help-circle: `crysfml` | :ballot_box_with_check: | :ballot_box_with_check: | :date: |

</div>

---

### 2.3. Polarized Powder Diffraction

Polarized-neutron powder diffraction is an epic. Planned: flipping-ratio
method.

---

### 2.4. Polarized Single-Crystal Diffraction

Polarized-neutron single-crystal diffraction is an epic. Planned:
flipping-ratio method, XYZ polarisation analysis, spherical neutron
polarimetry.

---

## 3. Multi-Dataset Support

<div class="ed-matrix" markdown="1">

| Feature                           | LIB                | CLI                | APP                |
| --------------------------------- | ------------------ | ------------------ | ------------------ |
| Multiple structural data blocks   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Multiple experimental data blocks | :white_check_mark: | :white_check_mark: | :date:             |

</div>

---

## 4. Analysis (Fitting)

### 4.1. Calculation Modes

<div class="ed-matrix" markdown="1">

| Feature                                                                                                                                                        | LIB                     | CLI                     | APP                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ----------------------- |
| Calculate diffraction pattern (for fitting/comparison)<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :white_check_mark: `pdffit2` | :white_check_mark:      | :white_check_mark:      | :white_check_mark:      |
| Calculate diffraction pattern (simple view, no data)<br/>- :white_check_mark: `cryspy`<br/>- :white_check_mark: `crysfml`<br/>- :date: `pdffit2`               | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| Calculate structure factors<br/>- :white_check_mark: `cryspy`<br/>- :date: `crysfml`                                                                           | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark:      |

</div>

### 4.2. Refinement Algorithms (numerical derivatives)

Minimizers are EasyDiffraction's optimizers and run with any engine.

<div class="ed-matrix" markdown="1">

| Feature                                                   | LIB                | CLI                | APP                |
| --------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Levenberg–Marquardt — LMFIT (leastsq) minimizer           | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Trust Region Reflective — LMFIT (least_squares) minimizer | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Levenberg–Marquardt — BUMPS (LM) minimizer                | :white_check_mark: | :white_check_mark: | :date:             |
| Nelder-Mead — BUMPS (AMOEBA) minimizer                    | :white_check_mark: | :white_check_mark: | :date:             |
| Differential evolution — BUMPS (DE) minimizer             | :white_check_mark: | :white_check_mark: | :date:             |
| Derivative-free minimization — DFO-LS minimizer           | :white_check_mark: | :white_check_mark: | :white_check_mark: |

</div>

### 4.3. Bayesian Analysis (Markov Chain Monte Carlo sampling)

<div class="ed-matrix" markdown="1">

| Feature                                                              | LIB                | CLI                | APP    |
| -------------------------------------------------------------------- | ------------------ | ------------------ | ------ |
| DiffeRential Evolution Adaptive Metropolis — BUMPS (DREAM) minimizer | :white_check_mark: | :white_check_mark: | :date: |
| Affine-invariant ensemble sampling — EMCEE minimizer                 | :white_check_mark: | :white_check_mark: | :date: |
| Resume sampling — BUMPS (DREAM) minimizer                            | :white_check_mark: | :white_check_mark: | :date: |
| Resume sampling — EMCEE minimizer                                    | :white_check_mark: | :white_check_mark: | :date: |

</div>

### 4.4. Fit Strategies

<div class="ed-matrix" markdown="1">

| Feature                                                   | LIB                | CLI                | APP                |
| --------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Single fit of one experiment to one or more structures    | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sequential fit of experimental data blocks                | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit within the same calculation engine              | :white_check_mark: | :white_check_mark: | :date:             |
| Joint fit using different engines (e.g. CrysPy + Pdffit2) | :white_check_mark: | :white_check_mark: | :date:             |
| Custom weighting for joint fit: _weight per dataset_      | :white_check_mark: | :white_check_mark: | :date:             |

</div>

### 4.5. Live Fitting

<div class="ed-matrix" markdown="1">

| Feature                                        | LIB    | CLI    | APP    |
| ---------------------------------------------- | ------ | ------ | ------ |
| Live fitting during real-time data acquisition | :date: | :date: | :date: |

</div>

---

## 5. Refinement Execution

<div class="ed-matrix" markdown="1">

| Feature                                       | LIB                | CLI                | APP                |
| --------------------------------------------- | ------------------ | ------------------ | ------------------ |
| GUI-driven refinement workflow                | :material-cancel:  | :material-cancel:  | :white_check_mark: |
| Command-line refinement execution             | :material-cancel:  | :white_check_mark: | :material-cancel:  |
| Scripted refinement workflow                  | :white_check_mark: | :material-cancel:  | :material-cancel:  |
| Parameter modification                        | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Load individual structure or experiment files | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Project-based refinement                      | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Sequential refinement                         | :white_check_mark: | :white_check_mark: | :date:             |
| Save refinement results to project            | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Undo last fit                                 | :white_check_mark: | :white_check_mark: | :date:             |

</div>

---

## 6. Constraints

<div class="ed-matrix" markdown="1">

| Feature                                                                      | LIB                | CLI                | APP                     |
| ---------------------------------------------------------------------------- | ------------------ | ------------------ | ----------------------- |
| Automatic symmetry constraints                                               | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| User-defined constraints<br/>e.g. "biso_Ba = biso_La", "occ_Ba = 1 - occ_La" | :white_check_mark: | :white_check_mark: | :date:                  |

</div>

---

## 7. Data Management

### 7.1. Project Files

<div class="ed-matrix" markdown="1">

| Feature                     | LIB                | CLI                | APP                |
| --------------------------- | ------------------ | ------------------ | ------------------ |
| Load full project from disk | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Save full project to disk   | :white_check_mark: | :white_check_mark: | :white_check_mark: |

</div>

### 7.2. Reports

<div class="ed-matrix" markdown="1">

| Feature                                                                            | LIB                | CLI                | APP    |
| ---------------------------------------------------------------------------------- | ------------------ | ------------------ | ------ |
| Interactive HTML report (Plotly fit plots, Three.js 3D structures; offline option) | :white_check_mark: | :white_check_mark: | :date: |
| LaTeX (TeX) report                                                                 | :white_check_mark: | :white_check_mark: | :date: |
| PDF report (compiled from the TeX bundle; requires a LaTeX engine)                 | :white_check_mark: | :white_check_mark: | :date: |
| CIF report (IUCr-style)                                                            | :white_check_mark: | :white_check_mark: | :date: |

</div>

### 7.3. Data Loading

<div class="ed-matrix" markdown="1">

| Feature                                     | LIB                | CLI                | APP                |
| ------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Add structure (to project) from CIF         | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Add structure (to project) from edi         | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Add experiment data (to project) from CIF   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Add experiment data (to project) from edi   | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Add experiment data (to project) from ASCII | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Add experiment data (to project) from NeXus | :date:             | :date:             | :date:             |

</div>

### 7.4. SciCat Integration

<div class="ed-matrix" markdown="1">

| Feature                       | LIB    | CLI    | APP    |
| ----------------------------- | ------ | ------ | ------ |
| Load full project from SciCat | :date: | :date: | :date: |
| Save full project to SciCat   | :date: | :date: | :date: |

</div>

### 7.5. External Resources

<div class="ed-matrix" markdown="1">

| Feature                                   | LIB                | CLI                | APP               |
| ----------------------------------------- | ------------------ | ------------------ | ----------------- |
| List available tutorial Jupyter notebooks | :white_check_mark: | :white_check_mark: | :material-cancel: |
| Download tutorial Jupyter notebooks       | :white_check_mark: | :white_check_mark: | :material-cancel: |

</div>

---

## 8. Visualization

### 8.1. Structure

#### Crystal Structure

<div class="ed-matrix" markdown="1">

| Feature                                  | LIB                | CLI    | APP                     |
| ---------------------------------------- | ------------------ | ------ | ----------------------- |
| Visualize unit cell                      | :white_check_mark: | :date: | :ballot_box_with_check: |
| Visualize multiple unit cells            | :date:             | :date: | :date:                  |
| Visualize atom sites as spheres          | :white_check_mark: | :date: | :white_check_mark:      |
| Visualize atoms occupied same position   | :white_check_mark: | :date: | :date:                  |
| Visualize bonds                          | :white_check_mark: | :date: | :date:                  |
| Visualize polyhedra                      | :date:             | :date: | :date:                  |
| Interactive mode: _3D rotation, zooming_ | :white_check_mark: | :date: | :white_check_mark:      |

</div>

#### Magnetic Structure

<div class="ed-matrix" markdown="1">

| Feature                           | LIB    | CLI    | APP    |
| --------------------------------- | ------ | ------ | ------ |
| Visualize magnetic moments        | :date: | :date: | :date: |
| Visualize magnetization densities | :date: | :date: | :date: |

</div>

### 8.2. Experiment

#### Powder Diffraction

<div class="ed-matrix" markdown="1">

| Feature                              | LIB                | CLI                | APP                |
| ------------------------------------ | ------------------ | ------------------ | ------------------ |
| Plot experimental curve              | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot calculated curve                | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot residual curve                  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Plot Bragg peaks                     | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Interactive mode: _zooming, panning_ | :white_check_mark: | :material-cancel:  | :white_check_mark: |

</div>

#### Single Crystal Diffraction

<div class="ed-matrix" markdown="1">

| Feature                              | LIB                | CLI                | APP                |
| ------------------------------------ | ------------------ | ------------------ | ------------------ |
| Plot obs vs calc for reflections     | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Interactive mode: _zooming, panning_ | :white_check_mark: | :material-cancel:  | :white_check_mark: |

</div>

### 8.3. Analysis

<div class="ed-matrix" markdown="1">

| Feature                                                         | LIB                | CLI                | APP                |
| --------------------------------------------------------------- | ------------------ | ------------------ | ------------------ |
| Live update of plots on parameter change with slider            | :material-cancel:  | :material-cancel:  | :white_check_mark: |
| Live update of plots during refinement                          | :material-cancel:  | :material-cancel:  | :white_check_mark: |
| Live update of fit quality (change in χ²) — _table_/_statusbar_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Live update of fit quality (change in χ²) — _chart_             | :date:             | :material-cancel:  | :date:             |
| Parameter evolution (sequential refinement)                     | :white_check_mark: | :white_check_mark: | :date:             |
| Correlation between parameters                                  | :white_check_mark: | :white_check_mark: | :date:             |
| Posterior pair (corner) plot                                    | :white_check_mark: | :white_check_mark: | :date:             |
| Posterior marginal distributions                                | :white_check_mark: | :white_check_mark: | :date:             |
| Posterior predictive bands                                      | :white_check_mark: | :white_check_mark: | :date:             |

</div>

---

## 9. User documentation

<div class="ed-matrix" markdown="1">

| Feature                             | LIB                | CLI                | APP                     |
| ----------------------------------- | ------------------ | ------------------ | ----------------------- |
| New unified documentation structure | :white_check_mark: | :white_check_mark: | :date:                  |
| Introduction                        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Features                            | :white_check_mark: | :white_check_mark: | :date:                  |
| Installation and setup guide        | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| User guide                          | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Tutorials                           | :white_check_mark: | :date:             | :date:                  |
| Verification                        | :white_check_mark: | :white_check_mark: | :date:                  |
| Command-line interface              | :material-cancel:  | :white_check_mark: | :material-cancel:       |
| Quick Reference                     | :white_check_mark: | :white_check_mark: | :date:                  |
| API reference                       | :white_check_mark: | :material-cancel:  | :material-cancel:       |

</div>

---

## 10. Backlog

Items not yet scheduled or detailed. Several are **epics** (large areas
that will be split into detailed rows once work begins).

<div class="ed-matrix" markdown="1">

| Feature                                                                                                               | LIB    | CLI               | APP               |
| --------------------------------------------------------------------------------------------------------------------- | ------ | ----------------- | ----------------- |
| Incommensurate structures — EPIC                                                                                      | :date: | :date:            | :date:            |
| 2D Rietveld refinement — EPIC                                                                                         | :date: | :date:            | :date:            |
| Chatbot for natural-language requests during analysis                                                                 | :date: | :material-cancel: | :material-cancel: |
| Refinement using analytical derivatives                                                                               | :date: | :date:            | :date:            |
| Global optimization algorithms (e.g. simulated annealing)                                                             | :date: | :date:            | :date:            |
| Built-in refinement strategies for common workflows                                                                   | :date: | :date:            | :date:            |
| Restraints (soft constraints, e.g. bond lengths, angles)                                                              | :date: | :date:            | :date:            |
| Search and download structure from Crystallography Open Database (COD)                                                | :date: | :material-cancel: | :date:            |
| Read instrument resolution parameters from file<br/>- :material-link-variant: `FullProf` "Irf" (.irf resolution file) | :date: | :date:            | :date:            |
| Set free parameters by category (e.g. all atomic positions, all ADPs)                                                 | :date: | :date:            | :date:            |

</div>
