# EasyDiffraction Architecture

**Version:** 1.0  
**Date:** 2026-03-24  
**Status:** Living document — updated as the project evolves

---

## 1. Overview

EasyDiffraction is a Python library for crystallographic diffraction analysis
(Rietveld refinement, pair-distribution-function fitting, etc.). It models the
domain using **CIF-inspired abstractions** — datablocks, categories, and
parameters — while providing a high-level, user-friendly API through a single
`Project` façade.

### 1.1 Supported Experiment Dimensions

Every experiment is fully described by four orthogonal axes:

| Axis             | Options                             | Enum                  |
| ---------------- | ----------------------------------- | --------------------- |
| Sample form      | powder, single crystal              | `SampleFormEnum`      |
| Scattering type  | Bragg, total (PDF)                  | `ScatteringTypeEnum`  |
| Beam mode        | constant wavelength, time-of-flight | `BeamModeEnum`        |
| Radiation probe  | neutron, X-ray                      | `RadiationProbeEnum`  |

> **Planned extensions:** 1D / 2D data dimensionality, polarised / unpolarised
> neutron beam.

### 1.2 Calculation Engines

External libraries perform the heavy computation:

| Engine     | Scope                |
| ---------- | -------------------- |
| `cryspy`   | Bragg diffraction    |
| `crysfml`  | Bragg diffraction    |
| `pdffit2`  | Total scattering     |

---

## 2. Core Abstractions

All core types live in `core/` which contains **only** base classes and
utilities — no domain logic.

### 2.1 Object Hierarchy

```
GuardedBase                            # Controlled attribute access, parent linkage, identity
├── CategoryItem                       # Single CIF category row  (e.g. Cell, Peak, Instrument)
├── CollectionBase                     # Ordered name→item container
│   ├── CategoryCollection             # CIF loop  (e.g. AtomSites, Background, Data)
│   └── DatablockCollection            # Top-level container  (e.g. Structures, Experiments)
└── DatablockItem                      # CIF data block  (e.g. Structure, Experiment)
```

### 2.2 GuardedBase — Controlled Attribute Access

`GuardedBase` is the root ABC. It enforces that only **declared `@property`
attributes** are accessible publicly:

- **`__getattr__`** rejects any attribute not declared as a `@property` on the
  class hierarchy. Shows diagnostics with closest-match suggestions on typos.
- **`__setattr__`** distinguishes:
  - **Private** (`_`-prefixed) — always allowed, no diagnostics.
  - **Read-only public** (property without setter) — blocked with a clear
    error.
  - **Writable public** (property with setter) — goes through the property
    setter, which is where validation happens.
  - **Unknown** — blocked with diagnostics showing allowed writable attrs.
- **Parent linkage** — when a `GuardedBase` child is assigned to another, the
  child's `_parent` is set automatically, forming an implicit ownership tree.
- **Identity** — every instance gets an `_identity: Identity` object for
  lazy CIF-style name resolution (`datablock_entry_name`, `category_code`,
  `category_entry_name`) by walking the `_parent` chain.

**Key design rule:** if a parameter has a public setter, it is writable for the
user. If only a getter — it is read-only. If internal code needs to set it, a
private method (underscore prefix) is used.

### 2.3 CategoryItem and CategoryCollection

| Aspect          | `CategoryItem`                     | `CategoryCollection`                      |
| --------------- |------------------------------------|-------------------------------------------|
| CIF analogy     | Single category row                | Loop (table) of rows                      |
| Examples        | Cell, SpaceGroup, Instrument, Peak | AtomSites, Background, Data, LinkedPhases |
| Parameters      | All `GenericDescriptorBase` attrs  | Aggregated from all child items           |
| Serialisation   | `as_cif` / `from_cif`              | `as_cif` / `from_cif`                     |
| Update hook     | `_update(called_by_minimizer=)`    | `_update(called_by_minimizer=)`           |
| Update priority | `_update_priority` (default 10)    | `_update_priority` (default 10)           |
| Display         | `show()` — single row              | `show()` — table                          |
| Building items  | N/A                                | `add(item)`, `create(**kwargs)`           |

**Update priority:** lower values run first. This ensures correct execution
order within a datablock (e.g. background before data).

### 2.4 DatablockItem and DatablockCollection

| Aspect             | `DatablockItem`                             | `DatablockCollection`          |
|--------------------|---------------------------------------------|--------------------------------|
| CIF analogy        | A single `data_` block                      | Collection of data blocks      |
| Examples           | Structure, BraggPdExperiment                | Structures, Experiments        |
| Category discovery | Scans `vars(self)` for categories           | N/A                            |
| Update cascade     | `_update_categories()` — sorted by priority | N/A                            |
| Parameters         | Aggregated from all categories              | Aggregated from all datablocks |
| Fittable params    | N/A                                         | Non-constrained `Parameter`s   |
| Free params        | N/A                                         | Fittable + `free == True`      |
| Dirty flag         | `_need_categories_update`                   | N/A                            |

When any `Parameter.value` is set, it propagates `_need_categories_update =
True` up to the owning `DatablockItem`. Serialisation (`as_cif`) and plotting
trigger `_update_categories()` if the flag is set.

### 2.5 Variable System — Parameters and Descriptors

```
GuardedBase
└── GenericDescriptorBase               # name, value (validated via AttributeSpec), description
    ├── GenericStringDescriptor         # _value_type = DataTypes.STRING
    └── GenericNumericDescriptor        # _value_type = DataTypes.NUMERIC, + units
        └── GenericParameter            # + free, uncertainty, fit_min, fit_max, constrained, uid
```

CIF-bound concrete classes add a `CifHandler` for serialisation:

| Class              | Base                        | Use case                     |
| ------------------ | --------------------------- | ---------------------------- |
| `StringDescriptor` | `GenericStringDescriptor`   | Read-only or writable text   |
| `NumericDescriptor`| `GenericNumericDescriptor`  | Read-only or writable number |
| `Parameter`        | `GenericParameter`          | Fittable numeric value       |

**Initialisation rule:** all Parameters/Descriptors are initialised with their
default values from `value_spec` (an `AttributeSpec`) **without any
validation** — we trust internal definitions. Changes go through public
property setters, which run both type and value validation.

**Mixin safety:** Parameter/Descriptor classes must not have init arguments
so they can be used as mixins safely (e.g. `PdTofDataPointMixin`).

### 2.6 Validation

`AttributeSpec` bundles `default`, `data_type`, `validator`, `allow_none`.
Validators include:

| Validator             | Purpose                                  |
| --------------------- | ---------------------------------------- |
| `TypeValidator`       | Checks Python type against `DataTypes`   |
| `RangeValidator`      | `ge`, `le`, `gt`, `lt` bounds checking   |
| `MembershipValidator` | Value must be in an allowed set          |
| `RegexValidator`      | Value must match a pattern               |

---

## 3. Experiment System

### 3.1 Experiment Type

An experiment's type is defined by the four enum axes and is **immutable after
creation**. This avoids the complexity of transforming all internal state when
the experiment type changes. The type is stored in an `ExperimentType` category
with four `StringDescriptor`s validated by `MembershipValidator`s.

### 3.2 Experiment Hierarchy

```
DatablockItem
└── ExperimentBase                   # name, type: ExperimentType, as_cif
    ├── PdExperimentBase             # + linked_phases, excluded_regions, peak, data
    │   ├── BraggPdExperiment        # + instrument, background (both via factories)
    │   └── TotalPdExperiment        # + instrument, scale_factor
    └── ScExperimentBase             # + linked_crystal, extinction, instrument, data
        ├── CwlScExperiment
        └── TofScExperiment
```

Each concrete experiment class carries:
- `type_info: TypeInfo` — tag and description for factory lookup
- `compatibility: Compatibility` — which enum axis values it supports

### 3.3 Category Ownership

Every experiment owns its categories as private attributes with public
read-only or read-write properties:

```python
# Read-only — user cannot replace the object, only modify its contents
experiment.linked_phases          # CategoryCollection
experiment.excluded_regions       # CategoryCollection
experiment.instrument             # CategoryItem
experiment.peak                   # CategoryItem
experiment.data                   # CategoryCollection

# Type-switchable — recreates the underlying object
experiment.background_type = 'chebyshev'   # triggers BackgroundFactory.create(...)
experiment.peak_profile_type = 'thompson-cox-hastings'  # triggers PeakFactory.create(...)
```

**Type switching pattern:** `expt.background_type = 'chebyshev'` rather than
`expt.background.type = 'chebyshev'`. This keeps the API at the experiment
level and makes it clear that the entire category object is being replaced.

---

## 4. Structure System

### 4.1 Structure Hierarchy

```
DatablockItem
└── Structure                       # name, cell, space_group, atom_sites
```

A `Structure` contains three categories:
- `Cell` — unit cell parameters (`CategoryItem`)
- `SpaceGroup` — symmetry information (`CategoryItem`)
- `AtomSites` — atomic positions collection (`CategoryCollection`)

Symmetry constraints (cell metric, atomic coordinates, ADPs) are applied via
the `crystallography` module during `_update_categories()`.

---

## 5. Factory System

### 5.1 FactoryBase

All factories inherit from `FactoryBase`, which provides:

| Feature            | Method / Attribute           | Description                                       |
| ------------------ |------------------------------|---------------------------------------------------|
| Registration       | `@Factory.register`          | Class decorator, appends to `_registry`           |
| Supported map      | `_supported_map()`           | `{tag: class}` from all registered classes        |
| Creation           | `create(tag)`                | Instantiate by tag string                         |
| Default resolution | `default_tag(**conditions)`  | Largest-subset matching on `_default_rules`       |
| Context creation   | `create_default_for(**cond)` | Resolve tag → create                              |
| Filtered query     | `supported_for(**filters)`   | Filter by `Compatibility` and `CalculatorSupport` |
| Display            | `show_supported(**filters)`  | Pretty-print table of type + description          |
| Tag listing        | `supported_tags()`           | List of all registered tags                       |

Each `__init_subclass__` gives every factory its own independent `_registry`
and `_default_rules`.

### 5.2 Default Rules

`_default_rules` maps frozensets of `(axis_name, enum_value)` tuples to tag
strings (preferably enum values for type safety):

```python
class PeakFactory(FactoryBase):
    _default_rules = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): PeakProfileTypeEnum.PSEUDO_VOIGT,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC,
    }
```

Resolution uses **largest-subset matching**: the rule whose frozenset is the
biggest subset of the given conditions wins. `frozenset()` acts as a universal
fallback.

### 5.3 Metadata on Registered Classes

Every `@Factory.register`-ed class carries three frozen dataclass attributes:

```python
@PeakFactory.register
class CwlPseudoVoigt(PeakBase, CwlBroadeningMixin):
    type_info = TypeInfo(
        tag='pseudo-voigt',
        description='Pseudo-Voigt profile',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )
```

| Metadata             | Purpose                                                 |
| -------------------- |---------------------------------------------------------|
| `TypeInfo`           | Stable tag for lookup/serialisation + human description |
| `Compatibility`      | Which enum axis values this class works with            |
| `CalculatorSupport`  | Which calculation engines support this class            |

### 5.4 Registration Trigger

Concrete classes use `@Factory.register` decorators. To trigger registration,
each package's `__init__.py` must **explicitly import** every concrete class:

```python
# datablocks/experiment/categories/background/__init__.py
from .chebyshev import ChebyshevPolynomialBackground
from .line_segment import LineSegmentBackground
```

### 5.5 All Factories

| Factory               | Domain                | Tags resolve to                                          |
| --------------------- | --------------------- |----------------------------------------------------------|
| `ExperimentFactory`   | Experiment datablocks | `BraggPdExperiment`, `TotalPdExperiment`, …              |
| `BackgroundFactory`   | Background categories | `LineSegmentBackground`, `ChebyshevPolynomialBackground` |
| `PeakFactory`         | Peak profiles         | `CwlPseudoVoigt`, `TofPseudoVoigtIkedaCarpenter`, …      |
| `InstrumentFactory`   | Instruments           | `CwlPdInstrument`, `TofPdInstrument`, …                  |
| `DataFactory`         | Data collections      | `BraggPdData`, `BraggPdTofData`, …                       |
| `CalculatorFactory`   | Calculation engines   | `CryspyCalculator`, `PdfFitCalculator`, …                |
| `MinimizerFactory`    | Minimisers            | `LmfitMinimizer`, `DfolsMinimizer`, …                    |

---

## 6. Analysis

### 6.1 Calculator

The calculator performs the actual diffraction computation. It is currently
attached to the `Analysis` object (one per project). The `CalculatorFactory`
filters its registry by `engine_imported` (whether the third-party library is
available in the environment).

> **Design note:** for joint fitting of heterogeneous experiments (e.g.
> Bragg + PDF), the calculator should be attached per-experiment rather than
> globally. For sequential refinement of many datasets of the same type, a
> single shared calculator is sufficient. The current design uses a global
> calculator; per-experiment attachment is planned.

### 6.2 Minimiser

The minimiser drives the optimisation loop. `MinimizerFactory` creates
instances by tag (e.g. `'lmfit'`, `'lmfit (leastsq)'`, `'dfols'`).

### 6.3 Fitter

`Fitter` wraps a minimiser instance and orchestrates the fitting workflow:

1. Collect `free_parameters` from structures + experiments.
2. Record start values.
3. Build an objective function that calls the calculator.
4. Delegate to `minimizer.fit()`.
5. Sync results (values + uncertainties) back to parameters.

### 6.4 Analysis Object

`Analysis` is bound to a `Project` and provides the high-level API:

- Calculator selection: `current_calculator`, `show_supported_calculators()`
- Minimiser selection: `current_minimizer`, `show_available_minimizers()`
- Fit modes: `'single'` (per-experiment) or `'joint'` (simultaneous with
  weights)
- Parameter tables: `show_all_params()`, `show_fittable_params()`,
  `show_free_params()`, `how_to_access_parameters()`
- Fitting: `fit()`, `show_fit_results()`
- Aliases and constraints

---

## 7. Project — The Top-Level Façade

`Project` is the single entry point for the user:

```python
import easydiffraction as ed

project = ed.Project(name='my_project')
```

It owns and coordinates all components:

| Property               | Type                  | Description                              |
| ---------------------- | --------------------- | ---------------------------------------- |
| `project.info`         | `ProjectInfo`         | Metadata: name, title, description, path |
| `project.structures`   | `Structures`          | Collection of structure datablocks       |
| `project.experiments`  | `Experiments`         | Collection of experiment datablocks      |
| `project.analysis`     | `Analysis`            | Calculator, minimiser, fitting           |
| `project.summary`      | `Summary`             | Report generation                        |
| `project.plotter`      | `Plotter`             | Visualisation                            |

### 7.1 Data Flow

```
Parameter.value set
    → AttributeSpec validation (type + value)
    → _need_categories_update = True (on parent DatablockItem)

Plot / CIF export / fit objective evaluation
    → _update_categories()
        → categories sorted by _update_priority
        → each category._update()
            → background: interpolate/evaluate → write to data
            → calculator: compute pattern → write to data
    → _need_categories_update = False
```

### 7.2 Persistence

Projects are saved as a directory of CIF files:

```
project_dir/
├── project.cif          # ProjectInfo
├── analysis.cif         # Analysis settings
├── summary.cif          # Summary report
├── structures/
│   └── lbco.cif         # One file per structure
└── experiments/
    └── hrpt.cif         # One file per experiment
```

---

## 8. User-Facing API Patterns

All examples below are drawn from the actual tutorials (`tutorials/`).

### 8.1 Project Setup

```python
import easydiffraction as ed

project = ed.Project(name='lbco_hrpt')
project.info.title = 'La0.5Ba0.5CoO3 at HRPT@PSI'
project.save_as(dir_path='lbco_hrpt', temporary=True)
```

### 8.2 Define Structures

```python
# Create a structure datablock
project.structures.create(name='lbco')

# Set space group and unit cell
project.structures['lbco'].space_group.name_h_m = 'P m -3 m'
project.structures['lbco'].cell.length_a = 3.88

# Add atom sites
project.structures['lbco'].atom_sites.create(
    label='La', type_symbol='La',
    fract_x=0, fract_y=0, fract_z=0,
    wyckoff_letter='a', b_iso=0.5, occupancy=0.5,
)

# Show as CIF
project.structures['lbco'].show_as_cif()
```

### 8.3 Define Experiments

```python
# Download data and create experiment from a data file
data_path = ed.download_data(id=3, destination='data')
project.experiments.add_from_data_path(
    name='hrpt',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# Set instrument parameters
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6

# Browse and select peak profile type
project.experiments['hrpt'].show_supported_peak_profile_types()
project.experiments['hrpt'].peak_profile_type = 'pseudo-voigt'

# Set peak profile parameters
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1

# Browse and select background type
project.experiments['hrpt'].show_supported_background_types()
project.experiments['hrpt'].background_type = 'line-segment'

# Add background points
project.experiments['hrpt'].background.create(id='10', x=10, y=170)
project.experiments['hrpt'].background.create(id='50', x=50, y=170)

# Link structure to experiment
project.experiments['hrpt'].linked_phases.create(id='lbco', scale=10.0)
```

### 8.4 Analysis and Fitting

```python
# Select calculator and minimiser
project.analysis.show_supported_calculators()
project.analysis.current_calculator = 'cryspy'
project.analysis.current_minimizer = 'lmfit (leastsq)'

# Plot before fitting
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# Select free parameters
project.structures['lbco'].cell.length_a.free = True
project.experiments['hrpt'].linked_phases['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True

# Inspect free parameters
project.analysis.show_free_params()

# Fit and show results
project.analysis.fit()
project.analysis.show_fit_results()

# Plot after fitting
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# Save
project.save()
```

### 8.5 TOF Experiment (tutorial ed-7)

```python
expt = ed.ExperimentFactory.from_data_path(
    name='dream', data_path=data_path,
    beam_mode='time-of-flight',
)
expt.instrument.calib_d_to_tof_offset = -9.29
expt.instrument.calib_d_to_tof_linear = 7476.91
expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
expt.peak.broad_gauss_sigma_0 = 4.2
```

### 8.6 Total Scattering / PDF (tutorial ed-12)

```python
project.experiments.add_from_data_path(
    name='xray_pdf', data_path=data_path,
    sample_form='powder',
    scattering_type='total',
    radiation_probe='xray',
)
project.experiments['xray_pdf'].peak_profile_type = 'gaussian-damped-sinc'
project.analysis.current_calculator = 'pdffit'
```

---

## 9. Design Principles

### 9.1 Naming and CIF Conventions

- Follow CIF naming conventions where possible. Deviate for better API
  design when necessary, but keep the spirit of CIF names.
- Reuse the concept of datablocks and categories from CIF.
- `DatablockItem` = one CIF `data_` block, `DatablockCollection` = set of
  blocks.
- `CategoryItem` = one CIF category, `CategoryCollection` = CIF loop.

### 9.2 Immutability of Experiment Type

The experiment type (the four enum axes) can only be set at creation time.
It cannot be changed afterwards. This avoids the complexity of maintaining
different state transformations when switching between fundamentally different
experiment configurations.

### 9.3 Category Type Switching

In contrast to experiment type, categories that have multiple implementations
(peak profiles, backgrounds, instruments) can be switched at runtime by the
user. The API pattern uses a type property on the **experiment**, not on the
category itself:

```python
# ✅ Correct — type property on the experiment
expt.background_type = 'chebyshev'

# ❌ Not used — type property on the category
expt.background.type = 'chebyshev'
```

This makes it clear that the entire category object is being replaced and
simplifies maintenance.

### 9.4 Show/Display Pattern

All categories (both items and collections) provide a public `show()` method:
- `CategoryItem.show()` — displays as a single row.
- `CategoryCollection.show()` — displays as a table.

For factory-backed categories, experiments expose:
- `show_supported_<category>_types()` — table of available types for the
  current experiment configuration.
- `show_current_<category>_type()` — the currently selected type.

### 9.5 Discoverable Supported Options

The user can always discover what is supported for the current experiment:

```python
expt.show_supported_peak_profile_types()
expt.show_supported_background_types()
project.analysis.show_supported_calculators()
project.analysis.show_available_minimizers()
```

Available calculators are filtered by `engine_imported` (whether the library
is installed) and can further be filtered by the experiment's categories via
`CalculatorSupport` metadata.

### 9.6 Enum Values as Tags

Enum values (`str, Enum`) serve as the single source of truth for user-facing
tag strings. Class `type_info.tag` values must match the corresponding enum
values so that enums can be used directly in `_default_rules` and in
user-facing API calls.

---

## 10. Open Design Questions

### 10.1 Calculator Attachment

**Current:** calculator is global (one per `Analysis`/project).

**Problem:** joint fitting of heterogeneous experiments (e.g. Bragg + PDF)
requires different calculation engines per experiment — CrysPy for Bragg,
PDFfit for PDF — while the minimiser optimises a shared set of structural
parameters across both. The current global calculator cannot support this.

**Recommended solution — two-level attachment:**

1. **Per-experiment calculator.** Each experiment stores its own calculator
   reference (`expt._calculator`). When a calculator is not explicitly set, it
   is auto-resolved from the experiment's `ExperimentType` using
   `CalculatorFactory.create_default_for(scattering_type=..., ...)`.

2. **Collection-level default.** `Experiments` (the collection) holds an
   optional default calculator. When set, all experiments without an explicit
   override inherit it. This covers the sequential-refinement case (many
   same-type datasets, one shared calculator instance) without per-experiment
   overhead.

3. **Minimiser stays global.** The minimiser lives on `Analysis` and optimises
   shared structure parameters across all experiments, calling each
   experiment's calculator independently during objective evaluation.

**API sketch:**

```python
# Per-experiment (heterogeneous joint fit)
project.experiments['bragg'].calculator = 'cryspy'
project.experiments['pdf'].calculator = 'pdffit'
project.analysis.fit_mode = 'joint'
project.analysis.fit()

# Collection-level default (sequential refinement)
project.experiments.calculator = 'cryspy'   # all experiments use this
project.analysis.fit_mode = 'sequential'
project.analysis.fit()
```

**Benefits:**
- Joint fitting of Bragg + PDF becomes natural.
- Sequential refinement stays lightweight (one calculator instance shared).
- Backward-compatible: if no per-experiment calculator is set, the auto-
  resolved default mirrors today's behaviour.

### 10.2 Universal Factories for All Categories

**Current:** some categories (e.g. `Extinction`, `LinkedCrystal`) have only one
implementation and no factory.

**Recommendation: yes, add factories for all categories.**

The cost is minimal — a trivial factory with one registered class and a
`frozenset(): tag` universal fallback rule. The benefits are significant:

1. **Uniform pattern.** Contributors learn one pattern and apply it everywhere.
   No need to distinguish "factory-backed categories" from "plain categories".

2. **Future-proof.** Adding a second extinction model (e.g. Becker–Coppens vs
   Shelx-style) requires no structural changes — just register a new class and
   add a `_default_rules` entry.

3. **Self-describing metadata.** Every category gets `type_info`,
   `compatibility`, `calculator_support` for free. This feeds into
   `show_supported()`, documentation generation, and automatic calculator
   compatibility checks.

4. **Consistent user API.** All switchable categories follow the same
   `show_supported_*_types()` / `show_current_*_type()` / `*_type = '...'`
   pattern, even if there is currently only one option.

**Example for Extinction:**

```python
class ExtinctionFactory(FactoryBase):
    _default_rules = {
        frozenset(): 'shelx',   # universal fallback, single option today
    }

@ExtinctionFactory.register
class ShelxExtinction(CategoryItem):
    type_info = TypeInfo(tag='shelx', description='Shelx-style extinction correction')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
```

### 10.3 Future Enum Extensions

The four current axes will be extended with at least two more:

| New axis            | Options                | Enum (proposed)          |
| ------------------- | ---------------------- | ------------------------ |
| Data dimensionality | 1D, 2D                 | `DataDimensionalityEnum` |
| Beam polarisation   | unpolarised, polarised | `PolarisationEnum`       |

These should follow the same `str, Enum` pattern and integrate into:
- `Compatibility` — add corresponding `FrozenSet` fields.
- `_default_rules` — conditions can include the new axes.
- `ExperimentType` — add new `StringDescriptor`s with
  `MembershipValidator`s.

**Migration path:** existing `Compatibility` objects that don't specify the new
fields use `frozenset()` (empty = "any"), so all existing classes remain
compatible without changes. Only classes that are specific to a new axis need
to declare it.

### 10.4 Additional Improvements

#### 10.4.1 Category `_update` Contract

Currently `_update()` is an optional override with a no-op default. A clearer
contract would help contributors:

- **Active categories** (those that compute something, e.g. `Background`,
  `Data`) should have an explicit `_update()` implementation.
- **Passive categories** (those that only store parameters, e.g. `Cell`,
  `SpaceGroup`) keep the no-op default.

The distinction is already implicit in the code; making it explicit in
documentation and possibly via a naming convention (or a simple flag) would
reduce confusion for new contributors.

#### 10.4.2 Parameter Change Tracking Granularity

The current dirty-flag approach (`_need_categories_update` on `DatablockItem`)
triggers a full update of all categories when any parameter changes. This is
simple and correct.

If performance becomes a concern with many categories, a more granular
approach could track which specific categories are dirty. However, this adds
complexity and should only be implemented when profiling proves it is needed.

#### 10.4.3 CIF Round-Trip Completeness

Ensuring every parameter survives a `save()` → `load()` cycle is critical for
reproducibility. A systematic integration test that creates a project,
populates all categories, saves, reloads, and compares all parameter values
would strengthen confidence in the serialisation layer.


