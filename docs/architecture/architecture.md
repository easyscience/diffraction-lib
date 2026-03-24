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

| Axis            | Options                             | Enum                 |
| --------------- | ----------------------------------- | -------------------- |
| Sample form     | powder, single crystal              | `SampleFormEnum`     |
| Scattering type | Bragg, total (PDF)                  | `ScatteringTypeEnum` |
| Beam mode       | constant wavelength, time-of-flight | `BeamModeEnum`       |
| Radiation probe | neutron, X-ray                      | `RadiationProbeEnum` |

> **Planned extensions:** 1D / 2D data dimensionality, polarised / unpolarised
> neutron beam.

### 1.2 Calculation Engines

External libraries perform the heavy computation:

| Engine    | Scope             |
| --------- | ----------------- |
| `cryspy`  | Bragg diffraction |
| `crysfml` | Bragg diffraction |
| `pdffit2` | Total scattering  |

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

`CollectionBase` provides a unified dict-like API over an ordered item list with
name-based indexing. All key operations — `__getitem__`, `__setitem__`,
`__delitem__`, `__contains__`, `remove()` — resolve keys through a single
`_key_for(item)` method that returns `category_entry_name` for category items or
`datablock_entry_name` for datablock items. Subclasses `CategoryCollection` and
`DatablockCollection` inherit this consistently.

### 2.2 GuardedBase — Controlled Attribute Access

`GuardedBase` is the root ABC. It enforces that only **declared `@property`
attributes** are accessible publicly:

- **`__getattr__`** rejects any attribute not declared as a `@property` on the
  class hierarchy. Shows diagnostics with closest-match suggestions on typos.
- **`__setattr__`** distinguishes:
  - **Private** (`_`-prefixed) — always allowed, no diagnostics.
  - **Read-only public** (property without setter) — blocked with a clear error.
  - **Writable public** (property with setter) — goes through the property
    setter, which is where validation happens.
  - **Unknown** — blocked with diagnostics showing allowed writable attrs.
- **Parent linkage** — when a `GuardedBase` child is assigned to another, the
  child's `_parent` is set automatically, forming an implicit ownership tree.
- **Identity** — every instance gets an `_identity: Identity` object for lazy
  CIF-style name resolution (`datablock_entry_name`, `category_code`,
  `category_entry_name`) by walking the `_parent` chain.

**Key design rule:** if a parameter has a public setter, it is writable for the
user. If only a getter — it is read-only. If internal code needs to set it, a
private method (underscore prefix) is used. See § 2.2.1 below for the full
pattern.

#### 2.2.1 Public Property Convention — Editable vs Read-Only

Every public parameter or descriptor exposed on a `GuardedBase` subclass follows
one of two patterns:

| Kind          | Getter | Setter | Internal mutation                  |
| ------------- | ------ | ------ | ---------------------------------- |
| **Editable**  | yes    | yes    | Via the public setter              |
| **Read-only** | yes    | no     | Via a private `_set_<name>` method |

**Editable property** — the user can both read and write the value. The setter
runs through `GuardedBase.__setattr__` and into the property setter, where
validation happens:

```python
@property
def name(self) -> str:
    """Human-readable name of the experiment."""
    return self._name


@name.setter
def name(self, new: str) -> None:
    self._name = new
```

**Read-only property** — the user can read but cannot assign. Any attempt to set
the attribute is blocked by `GuardedBase.__setattr__` with a clear error
message. If _internal_ code (factory builders, CIF loaders, etc.) needs to set
the value, it calls a private `_set_<name>` method instead of exposing a public
setter:

```python
@property
def sample_form(self) -> StringDescriptor:
    """Sample form descriptor (read-only for the user)."""
    return self._sample_form


def _set_sample_form(self, value: str) -> None:
    """Internal setter used by factory/CIF code during construction."""
    self._sample_form.value = value
```

**Why this matters:**

- `GuardedBase.__setattr__` uses the presence of a setter to decide writability.
  Adding a setter "just for internal use" would open the attribute to users.
- Private `_set_<name>` methods keep the public API surface minimal and
  intention-clear, while remaining greppable and type-safe.
- The pattern avoids string-based dispatch — every mutator has an explicit named
  method.

### 2.3 CategoryItem and CategoryCollection

| Aspect          | `CategoryItem`                     | `CategoryCollection`                      |
| --------------- | ---------------------------------- | ----------------------------------------- |
| CIF analogy     | Single category row                | Loop (table) of rows                      |
| Examples        | Cell, SpaceGroup, Instrument, Peak | AtomSites, Background, Data, LinkedPhases |
| Parameters      | All `GenericDescriptorBase` attrs  | Aggregated from all child items           |
| Serialisation   | `as_cif` / `from_cif`              | `as_cif` / `from_cif`                     |
| Update hook     | `_update(called_by_minimizer=)`    | `_update(called_by_minimizer=)`           |
| Update priority | `_update_priority` (default 10)    | `_update_priority` (default 10)           |
| Display         | `show()` on concrete subclasses    | `show()` on concrete subclasses           |
| Building items  | N/A                                | `add(item)`, `create(**kwargs)`           |

**Update priority:** lower values run first. This ensures correct execution
order within a datablock (e.g. background before data).

### 2.4 DatablockItem and DatablockCollection

| Aspect             | `DatablockItem`                             | `DatablockCollection`          |
| ------------------ | ------------------------------------------- | ------------------------------ |
| CIF analogy        | A single `data_` block                      | Collection of data blocks      |
| Examples           | Structure, BraggPdExperiment                | Structures, Experiments        |
| Category discovery | Scans `vars(self)` for categories           | N/A                            |
| Update cascade     | `_update_categories()` — sorted by priority | N/A                            |
| Parameters         | Aggregated from all categories              | Aggregated from all datablocks |
| Fittable params    | N/A                                         | Non-constrained `Parameter`s   |
| Free params        | N/A                                         | Fittable + `free == True`      |
| Dirty flag         | `_need_categories_update`                   | N/A                            |

When any `Parameter.value` is set, it propagates
`_need_categories_update = True` up to the owning `DatablockItem`. Serialisation
(`as_cif`) and plotting trigger `_update_categories()` if the flag is set.

### 2.5 Variable System — Parameters and Descriptors

```shell
GuardedBase
└── GenericDescriptorBase               # name, value (validated via AttributeSpec), description
    ├── GenericStringDescriptor         # _value_type = DataTypes.STRING
    └── GenericNumericDescriptor        # _value_type = DataTypes.NUMERIC, + units
        └── GenericParameter            # + free, uncertainty, fit_min, fit_max, constrained, uid
```

CIF-bound concrete classes add a `CifHandler` for serialisation:

| Class               | Base                       | Use case                     |
| ------------------- | -------------------------- | ---------------------------- |
| `StringDescriptor`  | `GenericStringDescriptor`  | Read-only or writable text   |
| `NumericDescriptor` | `GenericNumericDescriptor` | Read-only or writable number |
| `Parameter`         | `GenericParameter`         | Fittable numeric value       |

**Initialisation rule:** all Parameters/Descriptors are initialised with their
default values from `value_spec` (an `AttributeSpec`) **without any validation**
— we trust internal definitions. Changes go through public property setters,
which run both type and value validation.

**Mixin safety:** Parameter/Descriptor classes must not have init arguments so
they can be used as mixins safely (e.g. `PdTofDataPointMixin`).

### 2.6 Validation

`AttributeSpec` bundles `default`, `data_type`, `validator`, `allow_none`.
Validators include:

| Validator             | Purpose                                |
| --------------------- | -------------------------------------- |
| `TypeValidator`       | Checks Python type against `DataTypes` |
| `RangeValidator`      | `ge`, `le`, `gt`, `lt` bounds checking |
| `MembershipValidator` | Value must be in an allowed set        |
| `RegexValidator`      | Value must match a pattern             |

---

## 3. Experiment System

### 3.1 Experiment Type

An experiment's type is defined by the four enum axes and is **immutable after
creation**. This avoids the complexity of transforming all internal state when
the experiment type changes. The type is stored in an `ExperimentType` category
with four `StringDescriptor`s validated by `MembershipValidator`s. Public
properties are read-only; factory and CIF-loading code use private setters
(`_set_sample_form`, `_set_beam_mode`, `_set_radiation_probe`,
`_set_scattering_type`) during construction only.

### 3.2 Experiment Hierarchy

```shell
DatablockItem
└── ExperimentBase                   # name, type: ExperimentType, as_cif
    ├── PdExperimentBase             # + linked_phases, excluded_regions, peak, data
    │   ├── BraggPdExperiment        # + instrument, background (both via factories)
    │   └── TotalPdExperiment        # (no extra categories yet)
    └── ScExperimentBase             # + linked_crystal, extinction, instrument, data
        ├── CwlScExperiment
        └── TofScExperiment
```

Each concrete experiment class carries:

- `type_info: TypeInfo` — tag and description for factory lookup
- `compatibility: Compatibility` — which enum axis values it supports

### 3.3 Category Ownership

Every experiment owns its categories as private attributes with public read-only
or read-write properties:

```python
# Read-only — user cannot replace the object, only modify its contents
experiment.linked_phases  # CategoryCollection
experiment.excluded_regions  # CategoryCollection
experiment.instrument  # CategoryItem
experiment.peak  # CategoryItem
experiment.data  # CategoryCollection

# Type-switchable — recreates the underlying object
experiment.background_type = 'chebyshev'  # triggers BackgroundFactory.create(...)
experiment.peak_profile_type = 'thompson-cox-hastings'  # triggers PeakFactory.create(...)
```

**Type switching pattern:** `expt.background_type = 'chebyshev'` rather than
`expt.background.type = 'chebyshev'`. This keeps the API at the experiment level
and makes it clear that the entire category object is being replaced.

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

Symmetry constraints (cell metric, atomic coordinates, ADPs) are applied via the
`crystallography` module during `_update_categories()`.

---

## 5. Factory System

### 5.1 FactoryBase

All factories inherit from `FactoryBase`, which provides:

| Feature            | Method / Attribute           | Description                                       |
| ------------------ | ---------------------------- | ------------------------------------------------- |
| Registration       | `@Factory.register`          | Class decorator, appends to `_registry`           |
| Supported map      | `_supported_map()`           | `{tag: class}` from all registered classes        |
| Creation           | `create(tag)`                | Instantiate by tag string                         |
| Default resolution | `default_tag(**conditions)`  | Largest-subset matching on `_default_rules`       |
| Context creation   | `create_default_for(**cond)` | Resolve tag → create                              |
| Filtered query     | `supported_for(**filters)`   | Filter by `Compatibility` and `CalculatorSupport` |
| Display            | `show_supported(**filters)`  | Pretty-print table of type + description          |
| Tag listing        | `supported_tags()`           | List of all registered tags                       |

Each `__init_subclass__` gives every factory its own independent `_registry` and
`_default_rules`.

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

| Metadata            | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `TypeInfo`          | Stable tag for lookup/serialisation + human description |
| `Compatibility`     | Which enum axis values this class works with            |
| `CalculatorSupport` | Which calculation engines support this class            |

### 5.4 Registration Trigger

Concrete classes use `@Factory.register` decorators. To trigger registration,
each package's `__init__.py` must **explicitly import** every concrete class:

```python
# datablocks/experiment/categories/background/__init__.py
from .chebyshev import ChebyshevPolynomialBackground
from .line_segment import LineSegmentBackground
```

### 5.5 All Factories

| Factory             | Domain                | Tags resolve to                                             |
| ------------------- | --------------------- | ----------------------------------------------------------- |
| `BackgroundFactory` | Background categories | `LineSegmentBackground`, `ChebyshevPolynomialBackground`    |
| `PeakFactory`       | Peak profiles         | `CwlPseudoVoigt`, `TofPseudoVoigtIkedaCarpenter`, …         |
| `InstrumentFactory` | Instruments           | `CwlPdInstrument`, `TofPdInstrument`, …                     |
| `DataFactory`       | Data collections      | `PdCwlData`, `PdTofData`, `ReflnData`, `TotalData`          |
| `CalculatorFactory` | Calculation engines   | `CryspyCalculator`, `CrysfmlCalculator`, `PdffitCalculator` |
| `MinimizerFactory`  | Minimisers            | `LmfitMinimizer`, `DfolsMinimizer`, …                       |

> **Note:** `ExperimentFactory` and `StructureFactory` are _builder_ factories
> with `from_cif_path`, `from_cif_str`, `from_data_path`, and `from_scratch`
> classmethods. `ExperimentFactory` inherits `FactoryBase` and uses `@register`
> on all four concrete experiment classes; `_resolve_class` looks up the
> registered class via `default_tag()` + `_supported_map()`. `StructureFactory`
> is a plain class without `FactoryBase` inheritance (only one structure type
> exists today).

### 5.6 Tag Naming Convention

Tags are the user-facing identifiers for selecting types. They must be:

- **Consistent** — use the same abbreviations everywhere.
- **Hyphen-separated** — all lowercase, words joined by hyphens.
- **Semantically ordered** — from general to specific.
- **Unique within a factory** — but may overlap across factories.

#### Standard Abbreviations

| Concept             | Abbreviation | Never use                   |
| ------------------- | ------------ | --------------------------- |
| Powder              | `pd`         | `powder`                    |
| Single crystal      | `sc`         | `single-crystal`            |
| Constant wavelength | `cwl`        | `cw`, `constant-wavelength` |
| Time-of-flight      | `tof`        | `time-of-flight`            |
| Bragg (scattering)  | `bragg`      |                             |
| Total (scattering)  | `total`      |                             |

#### Complete Tag Registry

**Background tags**

| Tag            | Class                           |
| -------------- | ------------------------------- |
| `line-segment` | `LineSegmentBackground`         |
| `chebyshev`    | `ChebyshevPolynomialBackground` |

**Peak tags**

| Tag                                | Class                          |
| ---------------------------------- | ------------------------------ |
| `pseudo-voigt`                     | `CwlPseudoVoigt`               |
| `split-pseudo-voigt`               | `CwlSplitPseudoVoigt`          |
| `thompson-cox-hastings`            | `CwlThompsonCoxHastings`       |
| `tof-pseudo-voigt`                 | `TofPseudoVoigt`               |
| `tof-pseudo-voigt-ikeda-carpenter` | `TofPseudoVoigtIkedaCarpenter` |
| `tof-pseudo-voigt-back-to-back`    | `TofPseudoVoigtBackToBack`     |
| `gaussian-damped-sinc`             | `TotalGaussianDampedSinc`      |

**Instrument tags**

| Tag      | Class             |
| -------- | ----------------- |
| `cwl-pd` | `CwlPdInstrument` |
| `cwl-sc` | `CwlScInstrument` |
| `tof-pd` | `TofPdInstrument` |
| `tof-sc` | `TofScInstrument` |

**Data tags**

| Tag            | Class       |
| -------------- | ----------- |
| `bragg-pd-cwl` | `PdCwlData` |
| `bragg-pd-tof` | `PdTofData` |
| `bragg-sc`     | `ReflnData` |
| `total-pd`     | `TotalData` |

**Experiment tags**

| Tag            | Class               |
| -------------- | ------------------- |
| `bragg-pd`     | `BraggPdExperiment` |
| `total-pd`     | `TotalPdExperiment` |
| `bragg-sc-cwl` | `CwlScExperiment`   |
| `bragg-sc-tof` | `TofScExperiment`   |

**Calculator tags**

| Tag       | Class               |
| --------- | ------------------- |
| `cryspy`  | `CryspyCalculator`  |
| `crysfml` | `CrysfmlCalculator` |
| `pdffit`  | `PdffitCalculator`  |

**Minimizer tags**

| Tag                     | Class                                     |
| ----------------------- | ----------------------------------------- |
| `lmfit`                 | `LmfitMinimizer`                          |
| `lmfit (leastsq)`       | `LmfitMinimizer` (method=`leastsq`)       |
| `lmfit (least_squares)` | `LmfitMinimizer` (method=`least_squares`) |
| `dfols`                 | `DfolsMinimizer`                          |

> **Note:** minimizer variant tags (`lmfit (leastsq)`, `lmfit (least_squares)`)
> are planned but not yet re-implemented after the `FactoryBase` migration. See
> §11.8 and §11.9 for details.

### 5.7 Metadata Classification — Which Classes Get What

#### The Rule

> **If a concrete class is created by a factory, it gets `type_info`,
> `compatibility`, and `calculator_support`.**
>
> **If a `CategoryItem` only exists as a child row inside a
> `CategoryCollection`, it does NOT get these attributes — the collection
> does.**

#### Rationale

A `LineSegment` item (a single background control point) is never selected,
created, or queried by a factory. It is always instantiated internally by its
parent `LineSegmentBackground` collection. The meaningful unit of selection is
the _collection_, not the item. The user picks "line-segment background" (the
collection type), not individual line-segment points.

#### Singleton CategoryItems — factory-created (get all three)

| Class                          | Factory             |
| ------------------------------ | ------------------- |
| `CwlPdInstrument`              | `InstrumentFactory` |
| `CwlScInstrument`              | `InstrumentFactory` |
| `TofPdInstrument`              | `InstrumentFactory` |
| `TofScInstrument`              | `InstrumentFactory` |
| `CwlPseudoVoigt`               | `PeakFactory`       |
| `CwlSplitPseudoVoigt`          | `PeakFactory`       |
| `CwlThompsonCoxHastings`       | `PeakFactory`       |
| `TofPseudoVoigt`               | `PeakFactory`       |
| `TofPseudoVoigtIkedaCarpenter` | `PeakFactory`       |
| `TofPseudoVoigtBackToBack`     | `PeakFactory`       |
| `TotalGaussianDampedSinc`      | `PeakFactory`       |

#### Singleton CategoryItems — NOT factory-created (get `type_info` only, optionally `compatibility`)

| Class            | Notes                                                   |
| ---------------- | ------------------------------------------------------- |
| `Cell`           | Always present on every Structure. No factory selection |
| `SpaceGroup`     | Same as Cell                                            |
| `ExperimentType` | Intrinsically universal                                 |
| `Extinction`     | Only used in single-crystal experiments                 |
| `LinkedCrystal`  | Only single-crystal                                     |

#### CategoryCollections — factory-created (get all three)

| Class                           | Factory             |
| ------------------------------- | ------------------- |
| `LineSegmentBackground`         | `BackgroundFactory` |
| `ChebyshevPolynomialBackground` | `BackgroundFactory` |
| `PdCwlData`                     | `DataFactory`       |
| `PdTofData`                     | `DataFactory`       |
| `TotalData`                     | `DataFactory`       |
| `ReflnData`                     | `DataFactory`       |

#### CategoryItems that are ONLY children of collections (NO metadata)

| Class            | Parent collection               |
| ---------------- | ------------------------------- |
| `LineSegment`    | `LineSegmentBackground`         |
| `PolynomialTerm` | `ChebyshevPolynomialBackground` |
| `AtomSite`       | `AtomSites`                     |
| `PdCwlDataPoint` | `PdCwlData`                     |
| `PdTofDataPoint` | `PdTofData`                     |
| `TotalDataPoint` | `TotalData`                     |
| `Refln`          | `ReflnData`                     |
| `LinkedPhase`    | `LinkedPhases`                  |
| `ExcludedRegion` | `ExcludedRegions`               |

#### Non-category classes — factory-created (get `type_info` only)

| Class               | Factory             | Notes                                                    |
| ------------------- | ------------------- | -------------------------------------------------------- |
| `CryspyCalculator`  | `CalculatorFactory` | No `compatibility` — limitations expressed on categories |
| `CrysfmlCalculator` | `CalculatorFactory` | (same)                                                   |
| `PdffitCalculator`  | `CalculatorFactory` | (same)                                                   |
| `LmfitMinimizer`    | `MinimizerFactory`  | `type_info` only                                         |
| `DfolsMinimizer`    | `MinimizerFactory`  | (same)                                                   |
| `BraggPdExperiment` | `ExperimentFactory` | `type_info` + `compatibility` (no `calculator_support`)  |
| `TotalPdExperiment` | `ExperimentFactory` | (same)                                                   |
| `CwlScExperiment`   | `ExperimentFactory` | (same)                                                   |
| `TofScExperiment`   | `ExperimentFactory` | (same)                                                   |

---

## 6. Analysis

### 6.1 Calculator

The calculator performs the actual diffraction computation. It is currently
attached to the `Analysis` object (one per project). The `CalculatorFactory`
filters its registry by `engine_imported` (whether the third-party library is
available in the environment).

> **Design note:** for joint fitting of heterogeneous experiments (e.g. Bragg +
> PDF), the calculator should be attached per-experiment rather than globally.
> For sequential refinement of many datasets of the same type, a single shared
> calculator is sufficient. The current design uses a global calculator;
> per-experiment attachment is planned.

### 6.2 Minimiser

The minimiser drives the optimisation loop. `MinimizerFactory` creates instances
by tag (e.g. `'lmfit'`, `'dfols'`).

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

| Property              | Type          | Description                              |
| --------------------- | ------------- | ---------------------------------------- |
| `project.info`        | `ProjectInfo` | Metadata: name, title, description, path |
| `project.structures`  | `Structures`  | Collection of structure datablocks       |
| `project.experiments` | `Experiments` | Collection of experiment datablocks      |
| `project.analysis`    | `Analysis`    | Calculator, minimiser, fitting           |
| `project.summary`     | `Summary`     | Report generation                        |
| `project.plotter`     | `Plotter`     | Visualisation                            |

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
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.5,
    occupancy=0.5,
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
project.analysis.current_minimizer = 'lmfit'

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
expt = ExperimentFactory.from_data_path(
    name='sepd',
    data_path=data_path,
    beam_mode='time-of-flight',
)
expt.instrument.calib_d_to_tof_offset = 0.0
expt.instrument.calib_d_to_tof_linear = 7476.91
expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
expt.peak.broad_gauss_sigma_0 = 3.0
```

### 8.6 Total Scattering / PDF (tutorial ed-12)

```python
project.experiments.add_from_data_path(
    name='xray_pdf',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='xray',
    scattering_type='total',
)
project.experiments['xray_pdf'].peak_profile_type = 'gaussian-damped-sinc'
project.analysis.current_calculator = 'pdffit'
```

---

## 9. Design Principles

### 9.1 Naming and CIF Conventions

- Follow CIF naming conventions where possible. Deviate for better API design
  when necessary, but keep the spirit of CIF names.
- Reuse the concept of datablocks and categories from CIF.
- `DatablockItem` = one CIF `data_` block, `DatablockCollection` = set of
  blocks.
- `CategoryItem` = one CIF category, `CategoryCollection` = CIF loop.

### 9.2 Immutability of Experiment Type

The experiment type (the four enum axes) can only be set at creation time. It
cannot be changed afterwards. This avoids the complexity of maintaining
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

### 9.4 Switchable-Category Convention

Categories whose concrete implementation can be swapped at runtime (background,
peak profile, etc.) are called **switchable categories**. They follow a fixed
naming convention on the experiment:

| Facet           | Naming pattern                               | Example                                          |
| --------------- | -------------------------------------------- | ------------------------------------------------ |
| Current object  | `<category>` property (read-only)            | `expt.background`, `expt.peak`                   |
| Active type tag | `<category>_type` property (getter + setter) | `expt.background_type`, `expt.peak_profile_type` |
| Show supported  | `show_supported_<category>_types()`          | `expt.show_supported_background_types()`         |
| Show current    | `show_current_<category>_type()`             | `expt.show_current_peak_profile_type()`          |

**Design decisions:**

- The **experiment owns** the `_type` setter because switching replaces the
  entire category object (`self._background = BackgroundFactory.create(...)`).
- The **experiment owns** the `show_*` methods because they are one-liners that
  delegate to `Factory.show_supported(...)` and can pass experiment-specific
  context (e.g. `scattering_type`, `beam_mode` for peak filtering).
- Concrete category subclasses provide a public `show()` method for displaying
  the current content (not on the base `CategoryItem`/`CategoryCollection`).

### 9.5 Discoverable Supported Options

The user can always discover what is supported for the current experiment:

```python
expt.show_supported_peak_profile_types()
expt.show_supported_background_types()
project.analysis.show_supported_calculators()
project.analysis.show_available_minimizers()
```

Available calculators are filtered by `engine_imported` (whether the library is
installed) and can further be filtered by the experiment's categories via
`CalculatorSupport` metadata.

### 9.6 Enum Values as Tags

Enum values (`str, Enum`) serve as the single source of truth for user-facing
tag strings. Class `type_info.tag` values must match the corresponding enum
values so that enums can be used directly in `_default_rules` and in user-facing
API calls.

---

## 10. Issues

- **Open:** [`issues_open.md`](issues_open.md) — prioritised backlog.
- **Closed:** [`issues_closed.md`](issues_closed.md) — resolved items for
  reference.

When a resolution affects the architecture described above, the relevant
sections of this document are updated accordingly.
