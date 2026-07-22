---
title: Features — expanded catalog
icon: material/clipboard-text-multiple-outline
---

# :material-clipboard-text-multiple-outline: Features — expanded catalog

This page **extends the [Features](index.md) matrix** with the full set of
functionality ideas mined by the sibling **enhantica** projects — the
**crysta** C++ calculation/refinement engine and the **edi** product that
wraps it. crysta's team catalogued every diffraction feature found across
~20 reference libraries (CrysFML, cctbx, CrysPy, GSAS-II, MAUD, ObjCryst++,
pdffit2, Mantid, conograph, …) plus a stakeholder requirements brief (RWG);
this page folds that superset back into the EasyDiffraction feature layout so
the roadmap captures **everything we could build**, not only what is scoped
today.

The current [Features](index.md) page stays **authoritative for what
EasyDiffraction ships today**. Rows here that are already tracked there keep
their status; the value added on this page is the large set of **imported
ideas** — each carrying an :material-lightbulb-on-outline: **origin** tag that
points at where the capability is specified in the enhantica knowledge base,
so nothing has to be re-discovered later.

## Calculation engines

Same pluggable backends as the base page — `cryspy`, `crysfml`, `pdffit2`,
`easydiffraction` — plus, referenced here as the **idea source**, the enhantica
engine:

- **`crysta`** — an in-house C++ engine (thin nanobind/Qt bindings) that owns
  the whole forward model and convolution, with forward-mode automatic
  differentiation feeding an in-house Levenberg–Marquardt. It is **not an
  EasyDiffraction backend today**; it is cited as the place where much of the
  physics below is already specified, verified, or implemented.

## How to read this page

Each capability is tracked across the three ways to use EasyDiffraction, exactly
as on the base page:

- **LIB** — Python library · **CLI** — command-line interface · **APP** —
  graphical application

Status icons (unchanged from the base page):

- :white_check_mark: Done
- :ballot_box_with_check: Partially done — available with at least one
  engine/interface
- :construction: Work in progress
- :date: Planned (priority 5/5 `highest` … 1/5 `lowest`)
- :material-cancel: Not available / not applicable
- :material-help-circle: Unknown — support not yet confirmed

**New on this page:**

- :material-lightbulb-on-outline: **origin** — where the idea is specified in
  the enhantica knowledge base. `crysta §N` = engine book chapter, `crysta
  App.X` = engine appendix, `crysta ADR-00NN` = engine decision record, `edi
  E0N` / `edi ADR-000N` = product milestone / decision. A trailing marker gives
  the engine's own state: **impl ✅** (already built in crysta), **spec ✅**
  (equations written, not yet built), **fwd** (accepted forward-scope).
- :material-link-variant: cross-references the equivalent FullProf `.pcr` entry
  (carried over from the base page).
- :material-check-decagram: links to the [Verification](../verification/index.md)
  page where a calculation is cross-checked against an independent reference.

!!! note "Rows already on the base Features page"

    To keep this catalog readable, rows carried over from the base
    [Features](index.md) page are shown with their **status** and a short label;
    consult the base page for the full per-engine annotation. The imported rows
    — everything with an :material-lightbulb-on-outline: origin tag — are the
    substance of this page.

!!! note "Scope split — engine vs product"

    crysta is the **engine**; several ideas (coherent UI, side-by-side model
    views, facility data-system plumbing, the LLM chat assistant itself) are
    **product/front-end** concerns owned by **edi** and the EasyDiffraction app.
    Where the engine's only obligation is to *expose a hook*, that is noted.
    WASM / web-target ideas are intentionally **excluded** from this revision.

---

## 1. Structure Model

### 1.1. Crystal Structure

#### Space Group

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Hermann-Mauguin space-group symbol _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Space group IT number<br/>- :material-lightbulb-on-outline: crysta §1 (impl 🟡) | :date: | :date: | :date: |
| IT coordinate system / origin choice / setting _(base)_<br/>- :material-lightbulb-on-outline: crysta §1, ADR-0023 (consolidated symmetry DB) · :material-link-variant: `FullProf` ":1" | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |
| Consolidated in-tree symmetry database (nuclear + magnetic + superspace; 1651 Shubnikov groups vendored)<br/>- :material-lightbulb-on-outline: crysta ADR-0023 (impl 🟡) | :date: 3/5 | :date: 3/5 | :date: |
| Wyckoff positions, site multiplicity & symmetry constraints (auto-detect)<br/>- :material-lightbulb-on-outline: crysta §1 (impl 🟡) | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Systematic absences (centering + glide/screw), reflection generation & Friedel pairs _(engine internals; exposed for "list reflections")_<br/>- :material-lightbulb-on-outline: crysta §1 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Interplanar angle + Weiss zone law utilities<br/>- :material-lightbulb-on-outline: crysta §1.12 | :date: 1/5 | :date: 1/5 | :date: |

</div>

#### Cell

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Lengths _a, b, c_ and angles _α, β, γ_ _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Derived quantities — metric tensor _Gᵢⱼ_, volume, reciprocal cell & **B** (orthogonalization) matrix, _d_-spacing / _sinθ/λ_<br/>- :material-lightbulb-on-outline: crysta §1 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |
| U/UB orientation matrix + diffractometer geometry (Busing–Levy)<br/>- :material-lightbulb-on-outline: crysta §1.11 (single-crystal, C16) | :date: 2/5 | :date: 2/5 | :date: |

</div>

#### Atom Sites

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| X-ray form factors + neutron scattering lengths (natural + isotope) _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Fractional coordinates, occupancy, Wyckoff letter _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Custom / user-defined neutron scattering length _(base, planned)_<br/>- :material-link-variant: `FullProf` "Nsc" | :date: | :date: | :date: |
| Named, switchable scattering-source profiles (`crysta-default` / `fullprof-compat` / `cryspy-compat`) with field-level provenance<br/>- :material-lightbulb-on-outline: crysta ADR-0056 (impl 🟡) | :date: 3/5 | :date: 3/5 | :date: |
| Anomalous dispersion _f = f₀ + f′ + i f″_ (X-ray, energy-dependent)<br/>- :material-lightbulb-on-outline: crysta §2, C15 (spec ✅) · :material-link-variant: `FullProf` dispersion | :date: 3/5 | :date: 3/5 | :date: |
| Neutron cross-section chain — σ_c / σ_i / σ_a (1/v), SLD, penetration depth<br/>- :material-lightbulb-on-outline: crysta §2.7, C14 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Resonant energy-dependent b_c(λ) for rare earths<br/>- :material-lightbulb-on-outline: crysta §2.7 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Multipole (aspherical) atom density / charge-density form factor (Hansen–Coppens)<br/>- :material-lightbulb-on-outline: crysta ADR-0019, §13 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Uniform-sphere scatterer form factor (j₀)<br/>- :material-lightbulb-on-outline: crysta §2 | :date: 1/5 | :date: 1/5 | :date: |

</div>

#### Atomic Displacement (ADP)

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Isotropic _Biso / Uiso_ (with B/U/β conversion) _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Anisotropic _Bani / Uani / β_ (with B/U/β conversion) _(base)_ | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Type-neutral ADP storage + engine-side conversion (β = 2π² U a\*a\*)<br/>- :material-lightbulb-on-outline: crysta §2 (impl ✅) | :white_check_mark: | :white_check_mark: | :date: |

</div>

---

### 1.2. Magnetic Structure

The base page tracks this as a single **epic**; the enhantica engine has written
the physics for most of it (crysta §9–§11, ADR-0024), so the sub-rows below are
the concrete import.

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Magnetic propagation vector _k_ + moment components _m_<br/>- :material-lightbulb-on-outline: crysta §9, C18 (spec ✅) · :material-link-variant: `FullProf` "Nvk", "Rx,Ry,Rz" | :date: 3/5 | :date: 3/5 | :date: |
| Propagation-vector (_k_) **search from data** — grid scan + FOM / high-symmetry enumeration + lock-in<br/>- :material-lightbulb-on-outline: crysta §9.8, C31 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Shubnikov (magnetic) space groups — 1651, BNS/OG settings<br/>- :material-lightbulb-on-outline: crysta §10, ADR-0023 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Magnetic form factor ⟨j₀⟩+(2/g−1)⟨j₂⟩ + magnetic structure factor (complex 3-vector)<br/>- :material-lightbulb-on-outline: crysta §2, §9 (spec ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Magnetic interaction vector _M⊥_, satellite reflections _H = h ± k_, powder averaging<br/>- :material-lightbulb-on-outline: crysta §9 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Beyond-dipole magnetic ⟨j₄⟩ / ⟨j₆⟩<br/>- :material-lightbulb-on-outline: crysta §2.7 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Local susceptibility tensor _χ_<br/>- :material-lightbulb-on-outline: crysta §11, C19 (spec ✅) | :date: 1/5 | :date: 1/5 | :date: |
| Representation analysis (irreps) + symmetry-adapted modes (ISODISTORT/AMPLIMODES)<br/>- :material-lightbulb-on-outline: crysta §10 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Magnetic domains<br/>- :material-lightbulb-on-outline: crysta §9 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

### 1.3. Incommensurate / Superspace Structures — EPIC

New capability area imported from crysta's forward scope (not on the base page).

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| (3+d)D superspace modulation structure factor — modulation waves, t-averaged SF, Bessel/quadrature<br/>- :material-lightbulb-on-outline: crysta §2.8, ADR-0020 (spec ✅; tables to vendor) | :date: 1/5 | :date: 1/5 | :date: |
| Satellite reflection indexing (superspace)<br/>- :material-lightbulb-on-outline: crysta ADR-0020 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

### 1.4. Large-Cell / Macromolecular Path — EPIC

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| FFT-based structure factor for large cells + geometry restraints + sparse solve<br/>- :material-lightbulb-on-outline: crysta ADR-0021 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 2. Experiment Model

### 2.1. Powder Diffraction

#### Common — Linked Phases & Phase Analysis

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Scale factor + per-phase scale (multi-phase) _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Quantitative phase analysis — weight fractions (Hill–Howard)<br/>- :material-lightbulb-on-outline: crysta §5.1.1, C12 (spec ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Excluded regions — multiple start/end _(base)_ | :white_check_mark: | :white_check_mark: | :date: |

</div>

#### Fitting Methods

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Rietveld refinement (full pattern) _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Le Bail refinement (profile matching) _(base, planned)_<br/>- :material-lightbulb-on-outline: crysta §8.10, C31 (spec ✅) · :material-link-variant: `FullProf` "Jbt=2" | :date: 4/5 | :date: 4/5 | :date: |
| Pawley model-free intensity extraction<br/>- :material-lightbulb-on-outline: crysta §8.10, C31 (spec ✅) | :date: 3/5 | :date: 3/5 | :date: |

</div>

#### Background

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Line-segment (points) + Chebyshev polynomial _(base)_<br/>- :material-lightbulb-on-outline: crysta §6 (spec ✅) · :material-link-variant: `FullProf` "Nba" | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Automatic estimation — arPLS / FABC / SNIP _(base)_<br/>- :material-lightbulb-on-outline: crysta §6 | :white_check_mark: | :white_check_mark: | :date: |
| Extended bases — Legendre, cosine, Debye-diffuse, log-interpolation, Sonneveld–Visser<br/>- :material-lightbulb-on-outline: crysta §6 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Auto-bg anchor thinning (vertical RDP)<br/>- :material-lightbulb-on-outline: crysta §6 | :date: 1/5 | :date: 1/5 | :date: |

</div>

#### Preferred Orientation

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| March–Dollase _(base)_<br/>- :material-link-variant: `FullProf` "Nor=1" | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Spherical-harmonic preferred orientation / texture<br/>- :material-lightbulb-on-outline: crysta §12 (fwd) | :date: 2/5 | :date: 2/5 | :date: |

</div>

#### Instrument — Constant Wavelength

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Wavelength λ, second wavelength (Kα₁/Kα₂ doublet), 2θ offset _(base)_ | :white_check_mark: | :ballot_box_with_check: | :ballot_box_with_check: |
| Sample displacement / transparency / zero-shift _(base)_<br/>- :material-lightbulb-on-outline: crysta §5, C11 (spec ✅) · :material-link-variant: `FullProf` "SyCos, SySin, Zero" | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Absorption (cylinder, Hewat) + X-ray Lorentz-polarization _(base)_<br/>- :material-lightbulb-on-outline: crysta §5, C11/C15 (spec ✅) · :material-link-variant: `FullProf` "muR, Cthm, Rpolarz" | :white_check_mark: | :white_check_mark: | :date: |

</div>

!!! tip "Exact per-reflection corrections (crysta improvement idea)"

    crysta's central design win (vision doc §d) is applying absorption, LP,
    SyCos/SySin and preferred orientation **before convolution at exact
    integrated intensities**, instead of the point-wise approximations a
    correction layer bolted onto a black-box engine is forced into.

#### Instrument — Time-of-Flight

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| 2θ bank + d → TOF conversion (Zero, Dtt1, Dtt2, Dtt_1overd) _(base)_<br/>- :material-lightbulb-on-outline: crysta §4 (impl ✅) · :material-link-variant: `FullProf` TOF | :ballot_box_with_check: | :ballot_box_with_check: | :white_check_mark: |

</div>

#### Peak Profile — Common (CWL + TOF)

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Peak-range cutoff (speed vs accuracy, N·FWHM) _(base)_<br/>- :material-lightbulb-on-outline: crysta §3, ADR-0038 (impl ✅) · :material-link-variant: `FullProf` "WDT" | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Progressive auto-cutoff ramp (inexact→exact, amortised shrink-with-revalidation; e.s.d. from validated window)<br/>- :material-lightbulb-on-outline: crysta ADR-0038 (impl 🟡, `--auto-cutoff`) | :date: 2/5 | :date: 2/5 | :date: |

</div>

#### Peak Profile — Constant Wavelength

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Thompson-Cox-Hastings pseudo-Voigt (± Bérar–Baldinozzi / Finger–Cox–Jephcoat asymmetry) _(base)_<br/>- :material-lightbulb-on-outline: crysta §3, C11 (spec ✅) · :material-link-variant: `FullProf` "Npr=7" | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| True Voigt / Faddeeva `Re w(z)` (not pseudo-Voigt surrogate)<br/>- :material-lightbulb-on-outline: crysta §3, C11 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Pearson VII / IV, split-Lorentzian, EMG, skewed Gaussian/Voigt, Moffat<br/>- :material-lightbulb-on-outline: crysta §3.7 (spec ✅; Pearson VII classic lab-X-ray) | :date: 2/5 | :date: 2/5 | :date: |
| Fundamental-parameters (FPA) instrument convolutions<br/>- :material-lightbulb-on-outline: crysta §3.8 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Stacking faults — DIFFaX recursion (Treacy) + Warren analytical closed-form<br/>- :material-lightbulb-on-outline: crysta §3.9 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

#### Peak Profile — Time-of-Flight

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Pseudo-Voigt (non-convoluted), Jorgensen, Jorgensen–Von Dreele, double-b2b (type0m) _(base)_<br/>- :material-lightbulb-on-outline: crysta §4, ADR-0042 (impl ✅) · :material-link-variant: `FullProf` "Npr=9" | :ballot_box_with_check: | :ballot_box_with_check: | :ballot_box_with_check: |
| Ikeda–Carpenter ⊗ pseudo-Voigt (moderator pulse) _(base, planned)_<br/>- :material-lightbulb-on-outline: crysta §4, C14 (spec ✅) · :material-link-variant: `FullProf` "Npr=13" | :date: 3/5 | :date: 3/5 | :date: |
| Thermal ↔ epithermal TOF crossover (dual-pulse)<br/>- :material-lightbulb-on-outline: crysta §4.10 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| TOF Lorentz factor `L ∝ d⁴ sinθ_bank`<br/>- :material-lightbulb-on-outline: crysta §4/§5 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

#### Corrections (additional) — NEW subsection

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Microabsorption (Brindley/Vien)<br/>- :material-lightbulb-on-outline: crysta §5.1.2 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Surface roughness (Suortti, Pitschke–Hermann–Mattern)<br/>- :material-lightbulb-on-outline: crysta §5.9, C15 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Powder/TOF extinction — Sabine<br/>- :material-lightbulb-on-outline: crysta §5.10, C14 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Extended absorption geometries (flat plate / film / PSD) + beam footprint<br/>- :material-lightbulb-on-outline: crysta §5.11, C14 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Anisotropic hydrostatic-strain peak shift (Dᵢⱼ); exact `d′ = d·exp(ε)`<br/>- :material-lightbulb-on-outline: crysta §5.12/§12 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Thermal diffuse scattering (Warren)<br/>- :material-lightbulb-on-outline: crysta §5.13 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

#### Total Scattering (Pair Distribution Function)

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Gaussian-damped sinc termination (Qmax, Qbroad, δ₁, δ₂, Qdamp, spdiameter) _(base)_<br/>- :material-lightbulb-on-outline: crysta §7, C20 (spec ✅) | :white_check_mark: | :white_check_mark: | :date: |
| PDF definitions `G(r)`, `F(Q)`, `S(Q)` + real-space PDF from a structure (PDFfit)<br/>- :material-lightbulb-on-outline: crysta §7, C20 (spec ✅) | :white_check_mark: | :white_check_mark: | :date: |
| Debye scattering equation `Σ bᵢbⱼ sin(Qr)/(Qr)`<br/>- :material-lightbulb-on-outline: crysta §7 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Compton / inelasticity corrections (Klein–Nishina, Ruland)<br/>- :material-lightbulb-on-outline: crysta §7.7, C20 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Normalization — Faber–Ziman ⟨b⟩² vs Warren ⟨b²⟩; partial PDFs (per type-pair); Lorch window<br/>- :material-lightbulb-on-outline: crysta §7.6, C20 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

### 2.2. Single Crystal Diffraction

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Isotropic Becker–Coppens extinction (Gaussian / Lorentzian mosaicity) _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Anisotropic extinction correction _(base, planned)_<br/>- :material-lightbulb-on-outline: crysta §5, C16 · :material-link-variant: `FullProf` "Ext-Model=4" | :date: 2/5 | :date: 2/5 | :date: |
| Structural twinning + twin-fraction refinement (analytic gradient) _(base epic)_<br/>- :material-lightbulb-on-outline: crysta App.D, C16 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| ShelXL F_o² weighting scheme<br/>- :material-lightbulb-on-outline: crysta App.D, C16 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Merging statistics (Rmerge / Rmeas / Rpim / CC½ / CC\*)<br/>- :material-lightbulb-on-outline: crysta App.D, C27 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| French–Wilson (Bayesian F from I)<br/>- :material-lightbulb-on-outline: crysta App.D, C16 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Flack / absolute structure (Flack, Hooft, Student-t) + Patterson/anomalous maps<br/>- :material-lightbulb-on-outline: crysta App.D (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Twin/pathology intensity statistics (L-test, Britton, H-test), normalized E-values, Wilson scaling<br/>- :material-lightbulb-on-outline: crysta App.D (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Reported geometry with e.s.d.s (coord + cell covariance)<br/>- :material-lightbulb-on-outline: crysta App.D.11, C17 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Individual wavelength per reflection (TOF Laue) _(base)_ | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Single-crystal Laue white-beam geometry<br/>- :material-lightbulb-on-outline: crysta §12 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

### 2.3. / 2.4. Polarized Neutron Diffraction (Powder & Single-Crystal) — EPIC

Base page lists these as two epics; crysta §11 / ADR-0024 write the observable
model (the `polarisation` axis: UNP / FR / XYZ / SNP via a density-matrix core).

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Blume–Maleev cross-section + flipping ratio _R_<br/>- :material-lightbulb-on-outline: crysta §11, ADR-0024, C19 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Powder-averaged polarized cross-section + 2D geometry (Gukasov–Ressouche)<br/>- :material-lightbulb-on-outline: crysta §11.7, C19 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Spherical neutron polarimetry (CRYOPAD 3×3) + density-matrix polarization (Mag2Pol)<br/>- :material-lightbulb-on-outline: crysta §11, ADR-0024 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

### 2.5. Engineering Diffraction — Texture / Strain / Stress — EPIC (NEW)

New capability area imported from crysta ADR-0022 / §12 (forward scope, spec ✅
vs MAUD/GSAS-II).

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Harmonic (Bunge) texture ODF + WIMV / E-WIMV discrete ODF<br/>- :material-lightbulb-on-outline: crysta §12, ADR-0022 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Popa anisotropic size broadening + Popa/Stephens anisotropic strain (15-term)<br/>- :material-lightbulb-on-outline: crysta §12 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Warren–Averbach Fourier size/strain; size/strain distribution coefficients<br/>- :material-lightbulb-on-outline: crysta §12.6 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Triaxial sin²ψ residual stress + moment-pole / WSODF stress + elastic homogenization (Reuss/Voigt/Hill)<br/>- :material-lightbulb-on-outline: crysta §12, ADR-0022 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 3. Multi-Dataset Support

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Multiple structural + experimental data blocks _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| N-dimensional dataset & residual model (fit 1D/2D/3D data whole, not reduced to 1D)<br/>- :material-lightbulb-on-outline: crysta ADR-0017 (fwd) | :date: 2/5 | :date: 2/5 | :date: |
| Fitting-axis abstraction (2θ / TOF / d / Q; d-spacing-native)<br/>- :material-lightbulb-on-outline: crysta ADR-0018 (impl 🟡) | :date: 3/5 | :date: 3/5 | :date: |

</div>

---

## 4. Analysis (Fitting)

### 4.1. Calculation Modes

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Calculate diffraction pattern (for fitting/comparison, simple view, structure factors) _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Two-tier calculation split (per-reflection vs per-point) + event-clock lazy recompute<br/>- :material-lightbulb-on-outline: crysta ADR-0007/0009/0033 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

### 4.2. Refinement Algorithms

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| LMFIT (leastsq / least_squares), BUMPS (LM / AMOEBA / DE), DFO-LS minimizers _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| In-house Levenberg–Marquardt with **analytic (AD) Jacobians** (cost ∝ #free params) + λ strategy<br/>- :material-lightbulb-on-outline: crysta ADR-0004/0005, §8 (impl ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Geodesic-acceleration LM rung<br/>- :material-lightbulb-on-outline: crysta ADR-0005 (impl ✅, C22-T9) | :date: 1/5 | :date: 1/5 | :date: |
| Hybrid Jacobian — AD default, hand-analytic override per column<br/>- :material-lightbulb-on-outline: crysta ADR-0047 (proposed) | :date: 1/5 | :date: 1/5 | :date: |
| Sparse, scalable Jacobian + normal equations (10⁴–10⁶+ parameters)<br/>- :material-lightbulb-on-outline: crysta ADR-0016 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Refinement using analytical derivatives _(base backlog — spec'd here)_<br/>- :material-lightbulb-on-outline: crysta ADR-0004, App.B (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

### 4.3. Bayesian Analysis & Uncertainty

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| DREAM / EMCEE MCMC sampling + resume _(base)_ | :white_check_mark: | :white_check_mark: | :date: |
| Model selection — AIC / BIC, F-test, profile & 2-D confidence regions<br/>- :material-lightbulb-on-outline: crysta §8.13 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Covariance / uncertainties / correlations + R-factors & GoF (Rwp, Rexp, S, χ², R_B)<br/>- :material-lightbulb-on-outline: crysta §8 (impl ✅) | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |

</div>

### 4.4. Fit Strategies

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Single / sequential / joint / different-engine / custom-weighted fits _(base)_ | :white_check_mark: | :white_check_mark: | :date: |
| Joint multi-bank refinement (arrowhead residual, engine-side)<br/>- :material-lightbulb-on-outline: crysta ADR-0040 (impl ✅) · edi E02 | :ballot_box_with_check: | :ballot_box_with_check: | :date: |
| Autonomous / user-selectable fitting-strategy selection (simultaneous / staged / autonomous; data-driven pre-estimation + correlation-alternation)<br/>- :material-lightbulb-on-outline: crysta ADR-0013/0037 (proposed) | :date: 2/5 | :date: 2/5 | :date: |
| Sequential & parametric refinement (warm-started series; params as AD-differentiable functions of an external variable; whole-series joint fit; fault isolation + trajectory record)<br/>- :material-lightbulb-on-outline: crysta ADR-0053, C32 (proposed) | :date: 2/5 | :date: 2/5 | :date: |
| Evaluation-accuracy ramp (coarse → fine)<br/>- :material-lightbulb-on-outline: crysta ADR-0038 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |
| Built-in refinement strategies for common workflows + set free parameters by category (all positions, all ADPs)<br/>- :material-lightbulb-on-outline: crysta ADR-0037 · base backlog | :date: 2/5 | :date: 2/5 | :date: |

</div>

### 4.5. Live Fitting

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Live fitting during real-time data acquisition _(base)_ | :date: | :date: | :date: |
| Residual-only per-iteration stream (live fit plot) + progress + cancellation on every surface<br/>- :material-lightbulb-on-outline: edi E05-T4 · crysta C09 callbacks (engine hook) | :date: 3/5 | :date: 3/5 | :date: |

</div>

### 4.6. Global Optimization & Structure Solution — NEW

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Global optimization — simulated annealing / parallel tempering<br/>- :material-lightbulb-on-outline: crysta §8, C26 (spec ✅) · base backlog | :date: 2/5 | :date: 2/5 | :date: |
| Charge flipping (ab-initio phasing)<br/>- :material-lightbulb-on-outline: crysta §13 (spec ✅, Oszlányi–Sütő) | :date: 1/5 | :date: 1/5 | :date: |
| Powder auto-indexing — FOM (de Wolff M), Ito zone search, Selling/Delaunay reduction, error-stable Bravais, zero-shift<br/>- :material-lightbulb-on-outline: crysta App.C, C31 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Structure-solution global-search costs (anti-bump, BVS-restraint, molecular restraints, SA/PT schedules)<br/>- :material-lightbulb-on-outline: crysta App.D.10 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

### 4.7. Robust Objectives & Weighting — NEW

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Robust objectives — Cauchy / negentropy losses, Poisson deviance (low-count TOF)<br/>- :material-lightbulb-on-outline: crysta §8.13 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |
| Robust singular / non-negative LSQ (Pawley) + Cholesky / singular solve (mod-Cholesky, eigen-trunc)<br/>- :material-lightbulb-on-outline: crysta §8, C02/C26 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

## 5. Refinement Execution

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| GUI / CLI / scripted execution, parameter modification, project-based & sequential refinement, save results _(base)_ | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Undo last fit _(base)_ + full **undo/redo** via EditCommand transaction primitive (capture-at-setter, preflight replay, versioned JSON journal)<br/>- :material-lightbulb-on-outline: crysta ADR-0055 (impl ✅) · edi E06-T5 | :date: 3/5 | :date: 3/5 | :date: |
| Autonomous refinement control (health gating, rollback, release order)<br/>- :material-lightbulb-on-outline: crysta ADR-0013 (fwd) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 6. Constraints & Restraints

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Automatic symmetry constraints + user-defined equality constraints / ties _(base)_<br/>- :material-lightbulb-on-outline: crysta ADR-0039, §1 (impl ✅) | :white_check_mark: | :white_check_mark: | :ballot_box_with_check: |
| Restraints (soft — bond length / angle / planarity / chirality; rigid-bond, ADP-sim, RIGU)<br/>- :material-lightbulb-on-outline: crysta App.D.1, C17 (spec ✅) · base backlog | :date: 3/5 | :date: 3/5 | :date: |
| Rigid bodies / molecular constraints (Z-matrix)<br/>- :material-lightbulb-on-outline: crysta App.D.10 (fwd) | :date: 2/5 | :date: 2/5 | :date: |
| Geometry with e.s.d. calculator (AD Jacobian) + bond-valence sum QA (Brown–Altermatt)<br/>- :material-lightbulb-on-outline: crysta App.D.10/.11, C13 (spec ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

## 7. Data Management

### 7.1. Project Files

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Load / save full project from disk _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Directory-format `.edi` project + crysta-loader parity (edi writes → crysta reads, tested)<br/>- :material-lightbulb-on-outline: edi E02 / E02-T2 · crysta ADR-0040 (impl ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Declarative refinement config in the project — free set via CIF SU brackets (`10.25(5)` = free), excluded regions, cutoff<br/>- :material-lightbulb-on-outline: crysta ADR-0039 (impl ✅) · edi E02-T3 | :date: 3/5 | :date: 3/5 | :date: |
| Parameter addressing form (`model(id) _category.item(site)`)<br/>- :material-lightbulb-on-outline: edi E02-T2 · crysta ADR-0048 (dictionary) | :date: 2/5 | :date: 2/5 | :date: |

</div>

### 7.2. Reports

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Interactive HTML / LaTeX / PDF / CIF reports _(base)_ | :white_check_mark: | :white_check_mark: | :date: |
| Machine fit-report contract — one versioned `key=value` record shared by every surface (`schema=1`, `record=fit\|calc\|error`, indexed `bank.`/`iter.`/`param.` keys)<br/>- :material-lightbulb-on-outline: crysta ADR-0057 (impl 🟡) | :date: 3/5 | :date: 3/5 | :date: |
| `--format human / plain / json` structured CLI output<br/>- :material-lightbulb-on-outline: edi E03 · crysta C10 (CLI kit) | :material-cancel: | :date: 3/5 | :material-cancel: |

</div>

### 7.3. Data Loading

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Add structure / experiment from CIF / edi / ASCII _(base)_ | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| NeXus / HDF5 intake _(base, planned)_ — focused reader + field-by-field reduced-powder layout spec<br/>- :material-lightbulb-on-outline: crysta ADR-0054, C27 (spec ✅) | :date: 3/5 | :date: 3/5 | :date: |
| GSAS `.gss` + `.irf` / `.pcr` instrument-resolution intake<br/>- :material-lightbulb-on-outline: crysta ADR-0012, C27 · :material-link-variant: `FullProf` "Irf" · base backlog | :date: 2/5 | :date: 2/5 | :date: |
| Format zoo → normalize to `.edi` (ownership: edi/product)<br/>- :material-lightbulb-on-outline: edi E-post-v1 · crysta C27 | :date: 2/5 | :date: 2/5 | :date: |

</div>

### 7.4. SciCat Integration _(base — unchanged)_

Load / save full project from SciCat — :date: planned on all surfaces.

### 7.5. External Resources _(base — unchanged)_

List / download tutorial notebooks — :white_check_mark: LIB/CLI.

### 7.6. Provenance & Metadata — NEW

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Versioned `DatasetMetadata` schema + Mantid-`WorkspaceHistory`-style provenance record on the EditCommand journal<br/>- :material-lightbulb-on-outline: crysta ADR-0054 (proposed) | :date: 2/5 | :date: 2/5 | :date: |
| Facility data-system integration (ADARA / ONCat / IPTS) — **product/facility scope (edi)**; engine exposes the reader hook<br/>- :material-lightbulb-on-outline: crysta RWG §09 (⚪ front-end) · edi | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 8. Visualization

Base rows (structure unit cell / atoms / bonds / interactive 3D; powder &
single-crystal curves, Bragg peaks, interactive zoom/pan; analysis: live χ²,
parameter evolution, correlation & posterior plots) are **unchanged** — see the
[base page](index.md). Added below: density-map reconstruction, a forward-scope
output stage.

### 8.4. Density Reconstruction & Maps — NEW

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Fourier density synthesis `ρ(r) = (1/V) Σ F(H) e^{−2πi H·r}` + difference / residual maps (Fo−Fc, σ_A, Patterson)<br/>- :material-lightbulb-on-outline: crysta §13, ADR-0025, C25 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Map statistics + peak search; FFT kernel + grid sampling<br/>- :material-lightbulb-on-outline: crysta §13, C25 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Maximum Entropy Method (MEM) density<br/>- :material-lightbulb-on-outline: crysta §13, ADR-0025 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Spin / magnetization-density map<br/>- :material-lightbulb-on-outline: crysta §13 (fwd) | :date: 1/5 | :date: 1/5 | :date: |
| Visualize magnetic moments / magnetization densities _(base epic)_ | :date: | :date: | :date: |

</div>

---

## 9. User Documentation _(base — unchanged)_

The base page's documentation matrix is carried over as-is.

---

## 10. Validation & Diagnostics — NEW

Structured, collect-all validation the engine exposes for every surface to render
(never re-validate).

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Tiered validation (tier-1 syntax/structural · tier-2 dictionary-generated schema · tier-3 domain)<br/>- :material-lightbulb-on-outline: crysta ADR-0049 (impl ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Structured collect-all `Diagnostic{code, severity, path, message, source}` + append-only versioned catalogue; strict `load()` routes through non-throwing `validate() → [Diagnostic]`<br/>- :material-lightbulb-on-outline: crysta ADR-0049 (impl ✅) | :date: 3/5 | :date: 3/5 | :date: |
| Engine-hosted parameter dictionary (CIF-DDL data → generated tag/units table; `required`/`ge`/`le`/`enum` validators)<br/>- :material-lightbulb-on-outline: crysta ADR-0048 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |
| Logging facade + Warn+ ring buffer + opt-in crash dump (dependency-free, host-installed sink)<br/>- :material-lightbulb-on-outline: crysta ADR-0050 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

## 11. Architecture & Extensibility — NEW

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Extensibility & plugin architecture — one registry+factory per extension point (loader / correction / profile / SF / residual), compiled + dynamic tiers<br/>- :material-lightbulb-on-outline: crysta ADR-0051 (proposed) | :date: 2/5 | :date: 2/5 | :date: |
| Value-owned refinable `Parameter` (value, σ, bounds, free, units, tag) with explicit `for_each_parameter()` enumeration (no reflection)<br/>- :material-lightbulb-on-outline: crysta ADR-0003 (impl ✅) | :date: 2/5 | :date: 2/5 | :date: |
| One C++ core + thin nanobind (Python) / Qt (app) bindings — no duplicated domain logic<br/>- :material-lightbulb-on-outline: crysta ADR-0002 · edi ADR-0009 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |
| Composable correction stack + unified `ResidualProvider` seam (joint multi-technique)<br/>- :material-lightbulb-on-outline: crysta ADR-0008/0011 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |

</div>

---

## 12. Expert Guidance / LLM-Assist — NEW

The base backlog lists a "chatbot for natural-language requests." crysta scopes
the **engine hooks**; the assistant itself is a product concern.

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Chatbot for natural-language requests during analysis _(base backlog)_ | :date: | :material-cancel: | :material-cancel: |
| LLM-assist surface contract — declarative EDI + structured diagnostics + EditCommand + strategy-as-data + state snapshot + diagnostics→action table + what-if path<br/>- :material-lightbulb-on-outline: crysta ADR-0052 (proposed; engine hook) · edi | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 13. Platform, Packaging & Surfaces — NEW

Product-side delivery ideas from edi. _(Web/WASM target intentionally excluded
from this revision.)_

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| `pip install easydiffraction` → `import edi` (wheel with real C++ bindings)<br/>- :material-lightbulb-on-outline: edi E02 · ADR-0009 | :date: 3/5 | :material-cancel: | :material-cancel: |
| Product CLI as a thin C++ `main()` over the core (Python-free)<br/>- :material-lightbulb-on-outline: edi ADR-0007, E03 | :material-cancel: | :date: 2/5 | :material-cancel: |
| Desktop shell on a decoupled GUI base (pages · `ApplicationInfo` · Style tokens) + QtGraphs charting façade + light/dark theme<br/>- :material-lightbulb-on-outline: edi ADR-0005, E04 | :material-cancel: | :material-cancel: | :date: 2/5 |
| Installer (app + CLI component) + i18n (`qsTr` coverage)<br/>- :material-lightbulb-on-outline: edi E04-T5 · E04+ | :material-cancel: | :date: 1/5 | :date: 2/5 |
| Tag-driven versions (versioningit)<br/>- :material-lightbulb-on-outline: edi D10 (☑ shipped) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| Golden example projects (beta `Examples/`, NCAF first)<br/>- :material-lightbulb-on-outline: edi E05-T6 | :date: 3/5 | :date: 3/5 | :date: |

</div>

---

## 14. Performance & Scale — NEW

Engine-side scalability levers (crysta performance roadmap). _(GPU is
deliberately deferred; WASM/web excluded from this revision.)_

<div class="ed-matrix" markdown="1">

| Feature | LIB | CLI | APP |
| --- | --- | --- | --- |
| Parallel execution — CPU multithreading (OpenMP disjoint row-chunks; off-UI on desktop)<br/>- :material-lightbulb-on-outline: crysta ADR-0034 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |
| SIMD vectorization + structure-of-arrays (SoA) hot-kernel layout<br/>- :material-lightbulb-on-outline: crysta ADR-0035 (impl 🟡) | :date: 2/5 | :date: 2/5 | :date: |
| Sequential-batch (~1000 patterns) map/reduce driver; cloud / HPC batch entry<br/>- :material-lightbulb-on-outline: crysta ADR-0053, C32, RWG §10 (proposed) | :date: 2/5 | :date: 2/5 | :date: |
| GPU / accelerator backend — deferred, with explicit revisit criteria (SoA + template kernels keep it ready)<br/>- :material-lightbulb-on-outline: crysta ADR-0036 (proposed) | :date: 1/5 | :date: 1/5 | :date: |

</div>

---

## 15. Backlog (base — folded in above where a spec exists)

Items from the base backlog and their new home on this page:

| Base backlog item | Now specified as |
| --- | --- |
| Incommensurate structures — EPIC | [§1.3](#13-incommensurate-superspace-structures-epic) (crysta ADR-0020) |
| 2D Rietveld refinement — EPIC | [§3](#3-multi-dataset-support) N-D dataset (crysta ADR-0017) |
| Chatbot for natural-language requests | [§12](#12-expert-guidance-llm-assist-new) (crysta ADR-0052 hooks) |
| Refinement using analytical derivatives | [§4.2](#42-refinement-algorithms) (crysta ADR-0004, impl ✅) |
| Global optimization (simulated annealing) | [§4.6](#46-global-optimization-structure-solution-new) (crysta §8, C26) |
| Built-in refinement strategies for common workflows | [§4.4](#44-fit-strategies) (crysta ADR-0037) |
| Restraints (soft constraints — bond lengths, angles) | [§6](#6-constraints-restraints) (crysta App.D.1, C17) |
| Search & download structure from COD | product/loader concern (crysta ADR-0051 Loader point) |
| Read instrument resolution parameters from file (.irf) | [§7.3](#73-data-loading) (crysta ADR-0012) |
| Set free parameters by category | [§4.4](#44-fit-strategies) (crysta ADR-0048 dictionary groups) |

Still genuinely open (crysta's honest residual): throughput targets,
AD-sparsity-at-scale, anomalous-dispersion / representation-analysis /
superspace-table depth, model-selection & rigid-body primaries, the deferred GPU
path, and the out-of-engine measurement-loop frontier.

---

*Provenance: capabilities and their specification state are drawn from the
enhantica **crysta** engine knowledge base (`knowledge/book/features.md`,
`knowledge/book/adrs/`, `knowledge/requirements/rwg-*`) and the **edi** product
knowledge base (`knowledge/book/features.md`, `knowledge/book/adrs/`), 2026-07.
This page tracks **ideas and where they are specified**; the base
[Features](index.md) page remains authoritative for what EasyDiffraction ships.*
