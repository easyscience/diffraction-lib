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

```shell
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

```shell
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

```shell
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

```shell
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

```shell
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

All categories (both items and collections) provide a public `show()`
method:

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

---

## 11. Current and Potential Issues

This section catalogues concrete architectural issues observed in the current
codebase, organised by severity. Each entry explains the symptom, root cause,
and recommended fix.

### 11.1 Dirty-Flag Guard Is Disabled

**Where:** `core/datablock.py`, lines 49–51.

```python
# if not self._need_categories_update:
#    return
```

**Symptom:** every call to `_update_categories()` processes all categories
regardless of whether any parameter actually changed. The dirty flag
`_need_categories_update` is set by `GenericDescriptorBase.value.setter` and
reset at the end of `_update_categories()`, but nothing reads it.

**Impact:** during fitting, `_update_categories()` is called on every
objective-function evaluation. Without the guard, all categories (background,
instrument, data, etc.) are recomputed every time, even when only one
parameter changed.

**Recommended fix:** uncomment the guard. If specific categories must always
run (e.g. the calculator), they should opt out via a `_always_update` flag
rather than disabling the entire mechanism.

### 11.2 `Analysis` Is Not a `DatablockItem`

**Where:** `analysis/analysis.py`.

**Symptom:** `Analysis` owns categories (`Aliases`, `Constraints`,
`JointFitExperiments`) but does not extend `DatablockItem`. It has its own
ad-hoc `_update_categories()` that iterates over a hard-coded list:

```python
for category in [self.aliases, self.constraints]:
    if hasattr(category, '_update'):
        category._update(called_by_minimizer=called_by_minimizer)
```

**Impact:** Analysis categories do not participate in the standard
`DatablockItem.categories` discovery (which scans `vars(self)`), so they are
invisible to generic parameter enumeration, CIF serialisation, and display
methods.

**Recommended fix:** make `Analysis` extend `DatablockItem`, or extract an
`_update_categories()` protocol that `DatablockItem` and `Analysis` both
implement, so both use the same category-discovery and update-ordering logic.

### 11.3 `Analysis._calculator` Is a Class-Level Attribute

**Where:** `analysis/analysis.py`, line 49.

```python
class Analysis:
    _calculator = CalculatorFactory.create('cryspy')
```

**Symptom:** the calculator is instantiated once at **class definition time**
and shared across all `Analysis` instances.

**Impact:**

1. Import-time side effect: creating a `CryspyCalculator` object runs at
   module import, before the user has a chance to configure anything.
2. All projects share the same default calculator object until overridden. If
   one project mutates it before creating a second project, the second project
   sees the mutated state.
3. The class-level default is immediately overwritten in `__init__` (line 61:
   `self.calculator = Analysis._calculator`), making the sharing behaviour
   confusing rather than intentional.

**Recommended fix:** remove the class-level `_calculator`. Create the default
calculator in `__init__` so each project instance gets its own:

```python
def __init__(self, project) -> None:
    ...
    self.calculator = CalculatorFactory.create('cryspy')
    self._calculator_key = 'cryspy'
```

### 11.4 `ExperimentFactory._SUPPORTED` Duplicates the Registry

**Where:** `datablocks/experiment/item/factory.py`, lines 62–79.

**Symptom:** the hand-written `_SUPPORTED` nested dict maps
`(ScatteringType, SampleForm, BeamMode)` → class. The `_default_rules` dict
on the same class already provides the same mapping, and each registered class
carries `type_info` and `compatibility` metadata.

**Impact:** adding a new experiment type requires updating **three** places:
the class with its metadata, `_default_rules`, and `_SUPPORTED`. They can
fall out of sync silently.

**Recommended fix:** derive `_resolve_class` from `_default_rules` +
`_supported_map()`, or implement it as a `FactoryBase` method. Remove
`_SUPPORTED` entirely.

### 11.5 Symmetry Constraint Application Triggers Cascading Updates

**Where:** `datablocks/structure/item/base.py`, `_apply_cell_symmetry_constraints`.

**Symptom:** lines like `self.cell.length_a.value = dummy_cell['lattice_a']`
go through the public `value` setter, which:

1. Validates the value.
2. Sets `parent_datablock._need_categories_update = True`.

Each of the six cell parameters triggers this independently during a single
`_apply_symmetry_constraints` call. The same applies to atomic coordinate
constraints.

**Impact:** the dirty flag is set repeatedly during what is logically a single
batch operation. If the dirty-flag guard (11.1) were enabled, there would be
no correctness issue — but a bulk-assignment bypass (e.g. an internal
`_set_value_no_notify` method) would be cleaner and express intent.

**Recommended fix:** introduce a private method on `GenericDescriptorBase` that
sets the value without triggering the dirty flag, for use by internal batch
operations like symmetry constraints. Alternatively, suppress notification via a
context manager or flag on the owning datablock.

### 11.6 `CollectionBase._key_for` Mixes Two Identity Levels

**Where:** `core/collection.py`, line 77.

```python
def _key_for(self, item):
    return item._identity.category_entry_name or item._identity.datablock_entry_name
```

**Symptom:** the same collection class is used for both `CategoryCollection`
(items keyed by `category_entry_name`) and `DatablockCollection` (items keyed
by `datablock_entry_name`). The fallback chain conflates the two scopes.

**Impact:** if a `CategoryItem` lacks a `category_entry_name` but happens to
have a `datablock_entry_name` (inherited from its parent), it will be indexed
under the wrong key. This is fragile and relies on every `CategoryItem`
having a properly set `category_entry_name`.

**Recommended fix:** override `_key_for` in `CategoryCollection` and
`DatablockCollection` separately, each returning exactly the key it expects.

### 11.7 `CategoryCollection.create` Uses `**kwargs` with `setattr`

**Where:** `core/category.py`, lines 113–127.

```python
def create(self, **kwargs) -> None:
    child_obj = self._item_type()
    for attr, val in kwargs.items():
        setattr(child_obj, attr, val)
    self.add(child_obj)
```

**Symptom:** `create` accepts arbitrary keyword arguments and applies them
blindly via `setattr`. A typo in a keyword argument (e.g. `fract_xx=0.5`) is
silently caught by `GuardedBase.__setattr__` which logs a warning but does not
raise, so the value is quietly dropped.

**Impact:** the user sees no exception on typos; the item is created with
incorrect default values. This contradicts the project's "prefer explicit
keyword arguments" principle.

**Recommended fix:** concrete collection subclasses (e.g. `AtomSites`) should
override `create` with explicit parameters, so IDE autocomplete and typo
detection work. The base `create(**kwargs)` can remain as an internal
implementation detail.

### 11.8 `Project._update_categories` Has Ad-Hoc Orchestration

**Where:** `project/project.py`, lines 224–229.

```python
def _update_categories(self, expt_name) -> None:
    for structure in self.structures:
        structure._update_categories()
    self.analysis._update_categories()
    experiment = self.experiments[expt_name]
    experiment._update_categories()
```

**Symptom:** update orchestration is hard-coded in `Project`, with the update
order (structures → analysis → experiment) encoded implicitly. The
`_update_priority` system exists on categories but is not used across
datablocks.

**Impact:** if a new top-level component is added (e.g. a second analysis
object, or a pre-processing stage), the orchestration must be manually
updated. The `expt_name` parameter means only one experiment is updated per
call, which is inconsistent with the "fit all experiments" workflow in joint
mode.

**Recommended fix:** consider a project-level `_update_priority` on
datablocks/components, or at minimum document the required update order. For
joint fitting, all experiments should be updateable in a single call.

### 11.9 Single-Fit Mode Creates Dummy `Experiments` Wrapper

**Where:** `analysis/analysis.py`, lines 548–565.

```python
for expt_name in experiments.names:
    experiment = experiments[expt_name]
    dummy_experiments = Experiments()
    object.__setattr__(dummy_experiments, '_parent', self.project)
    dummy_experiments.add(experiment)
    self.fitter.fit(structures, dummy_experiments, analysis=self)
```

**Symptom:** to fit one experiment at a time, a throw-away `Experiments`
collection is created, the parent is manually forced via
`object.__setattr__`, and the single experiment is added. This bypasses the
normal parent-linkage mechanism.

**Impact:** the forced `_parent` assignment circumvents `GuardedBase` parent
tracking. If the `Experiments` collection does anything in `add()` that
depends on its parent (e.g. identity resolution), it will work here only by
coincidence. The pattern is fragile and hard to follow.

**Recommended fix:** make `Fitter.fit` accept a list of experiment objects (or
a single experiment), not necessarily an `Experiments` collection. Or add a
`fit_single(experiment)` method that avoids the wrapper entirely.

### 11.10 Missing `load()` Implementation

**Where:** `project/project.py`, line 142.

```python
def load(self, dir_path: str) -> None:
    ...
    console.print('Loading project is not implemented yet.')
    self._saved = True
```

**Symptom:** `save()` serialises all components to CIF files but `load()` is a
stub. The project claims to be "saved" after a load attempt that does nothing.

**Impact:** users cannot round-trip a project (save → close → reopen).
The `self._saved = True` line is misleading.

**Recommended fix:** implement `load()` that reads CIF files from the project
directory and reconstructs structures, experiments, and analysis. Until then,
remove the `self._saved = True` line and raise `NotImplementedError`.

### 11.11 `Structure` Does Not Override `_update_categories`

**Where:** `datablocks/structure/item/base.py`.

**Symptom:** `Structure` inherits the generic `DatablockItem._update_categories`
which iterates over all categories and calls `_update()` on each. But the
structure-specific logic (symmetry constraints) lives in
`_apply_symmetry_constraints()`, which is only called from the fitting
residual function via `structure._update_categories()` in `fitting.py` — **except that it isn't**: the base `_update_categories` only calls
`category._update()`, which is a no-op for `Cell`, `SpaceGroup`, and
`AtomSites`.

**Impact:** symmetry constraints are never automatically applied through the
standard `_update_categories` path. They are applied only when explicitly
called. If a user changes a space group name and then exports CIF, the cell
parameters will not reflect the new symmetry constraints.

**Recommended fix:** override `_update_categories` in `Structure` to call
`_apply_symmetry_constraints()` before (or instead of) the base category
iteration. The TODO comment in `datablock.py` already mentions this:

> "This should call apply_symmetry and apply_constraints in the case of
> structures."

### 11.12 Background Type Switching Loses Data

**Where:** `datablocks/experiment/item/bragg_pd.py`, `background_type.setter`.

```python
self.background = BackgroundFactory.create(new_type)
self._background_type = new_type
```

**Symptom:** when the user switches background type (e.g. from `'line-segment'`
to `'chebyshev'`), the entire background category is replaced with a fresh,
empty instance. Any background points or coefficients the user has defined are
silently discarded.

**Impact:** there is no warning, no confirmation, and no way to recover
the old background data. The same issue applies to `peak_profile_type`
switching.

**Recommended fix:** log a warning when the replacement discards user-defined
data. Optionally, keep a history or prompt for confirmation in interactive
contexts.

### 11.13 Parameter `unique_name` Is Duplicated

**Where:** `core/variable.py`.

**Symptom:** `GenericDescriptorBase.unique_name` (line 109) and
`GenericParameter.unique_name` (line 302) contain identical implementations:

```python
parts = [
    self._identity.datablock_entry_name,
    self._identity.category_code,
    self._identity.category_entry_name,
    self.name,
]
return '.'.join(filter(None, parts))
```

**Impact:** any change to the name resolution logic must be applied in two
places. Since `GenericParameter` inherits from `GenericDescriptorBase`, the
override is unnecessary.

**Recommended fix:** remove the `unique_name` property from
`GenericParameter`. The inherited version is identical.

### 11.14 Minimiser Variant Loss

**Where:** `analysis/minimizers/`.

**Symptom:** the pre-refactoring `MinimizerFactory` supported multiple
minimiser variants:
- `'lmfit'` (the engine)
- `'lmfit (leastsq)'` (specific algorithm)
- `'lmfit (least_squares)'` (another algorithm)

After the `FactoryBase` migration, only `'lmfit'` and `'dfols'` remain as
registered tags. The ability to select specific algorithm variants within an
engine was lost.

**Impact:** users who relied on selecting a specific lmfit algorithm (e.g.
`project.analysis.current_minimizer = 'lmfit (least_squares)'`) get a
`ValueError`.

**Recommended fix:** restore variant support, either as separate registered
classes (thin subclasses with different tags) or as a two-level selection
(engine + algorithm). The choice depends on whether variants need different
`TypeInfo`/`Compatibility` metadata.

### 11.15 `Project.parameters` Returns Empty List

**Where:** `project/project.py`, lines 127–131.

```python
@property
def parameters(self):
    """Return parameters from all components (TBD)."""
    return []
```

**Symptom:** `Project.parameters` is a required abstract property from
`GuardedBase` but always returns `[]`. Parameters are only accessible through
`project.structures.parameters` and `project.experiments.parameters`.

**Impact:** any code that generically calls `.parameters` on a `Project`
(e.g. a future generic export) gets nothing.

**Recommended fix:** aggregate parameters from all owned components:

```python
@property
def parameters(self):
    return self.structures.parameters + self.experiments.parameters
```

### 11.16 Summary of Issue Severity

| #     | Issue                                      | Severity | Type             |
| ----- | ------------------------------------------ | -------- | ---------------- |
| 11.1  | Dirty-flag guard disabled                  | Medium   | Performance      |
| 11.2  | `Analysis` not a `DatablockItem`           | Medium   | Consistency      |
| 11.3  | Class-level `_calculator`                  | Medium   | Correctness      |
| 11.4  | `_SUPPORTED` duplicates registry           | Low      | Maintainability  |
| 11.5  | Symmetry constraints trigger notifications | Low      | Performance      |
| 11.6  | `_key_for` mixes identity levels           | Low      | Correctness      |
| 11.7  | `create(**kwargs)` with `setattr`          | Medium   | API safety       |
| 11.8  | Ad-hoc update orchestration                | Low      | Maintainability  |
| 11.9  | Dummy `Experiments` wrapper                | Medium   | Fragility        |
| 11.10 | Missing `load()` implementation            | High     | Completeness     |
| 11.11 | `Structure` misses symmetry in updates     | High     | Correctness      |
| 11.12 | Type switching loses data silently         | Medium   | Data safety      |
| 11.13 | Duplicated `unique_name` property          | Low      | Maintainability  |
| 11.14 | Minimiser variant loss                     | Medium   | Feature loss     |
| 11.15 | `Project.parameters` returns `[]`          | Low      | Completeness     |

