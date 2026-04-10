# EasyDiffraction Architecture

**Version:** 1.0  
**Date:** 2026-03-24  
**Status:** Living document — updated as the project evolves

---

## 1. Overview

EasyDiffraction is a Python library for crystallographic diffraction
analysis (Rietveld refinement, pair-distribution-function fitting,
etc.). It models the domain using **CIF-inspired abstractions** —
datablocks, categories, and parameters — while providing a high-level,
user-friendly API through a single `Project` façade.

### 1.1 Supported Experiment Dimensions

Every experiment is fully described by four orthogonal axes:

| Axis            | Options                             | Enum                 |
| --------------- | ----------------------------------- | -------------------- |
| Sample form     | powder, single crystal              | `SampleFormEnum`     |
| Scattering type | Bragg, total (PDF)                  | `ScatteringTypeEnum` |
| Beam mode       | constant wavelength, time-of-flight | `BeamModeEnum`       |
| Radiation probe | neutron, X-ray                      | `RadiationProbeEnum` |

> **Planned extensions:** 1D / 2D data dimensionality, polarised /
> unpolarised neutron beam.

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

`CollectionBase` provides a unified dict-like API over an ordered item
list with name-based indexing. All key operations — `__getitem__`,
`__setitem__`, `__delitem__`, `__contains__`, `remove()` — resolve keys
through a single `_key_for(item)` method that returns
`category_entry_name` for category items or `datablock_entry_name` for
datablock items. Subclasses `CategoryCollection` and
`DatablockCollection` inherit this consistently.

### 2.2 GuardedBase — Controlled Attribute Access

`GuardedBase` is the root ABC. It enforces that only **declared
`@property` attributes** are accessible publicly:

- **`__getattr__`** rejects any attribute not declared as a `@property`
  on the class hierarchy. Shows diagnostics with closest-match
  suggestions on typos.
- **`__setattr__`** distinguishes:
  - **Private** (`_`-prefixed) — always allowed, no diagnostics.
  - **Read-only public** (property without setter) — blocked with a
    clear error.
  - **Writable public** (property with setter) — goes through the
    property setter, which is where validation happens.
  - **Unknown** — blocked with diagnostics showing allowed writable
    attrs.
- **Parent linkage** — when a `GuardedBase` child is assigned to
  another, the child's `_parent` is set automatically, forming an
  implicit ownership tree.
- **Identity** — every instance gets an `_identity: Identity` object for
  lazy CIF-style name resolution (`datablock_entry_name`,
  `category_code`, `category_entry_name`) by walking the `_parent`
  chain.

**Key design rule:** if a parameter has a public setter, it is writable
for the user. If only a getter — it is read-only. If internal code needs
to set it, a private method (underscore prefix) is used. See § 2.2.1
below for the full pattern.

#### 2.2.1 Public Property Convention — Editable vs Read-Only

Every public parameter or descriptor exposed on a `GuardedBase` subclass
follows one of two patterns:

| Kind          | Getter | Setter | Internal mutation                  |
| ------------- | ------ | ------ | ---------------------------------- |
| **Editable**  | yes    | yes    | Via the public setter              |
| **Read-only** | yes    | no     | Via a private `_set_<name>` method |

**Editable property** — the user can both read and write the value. The
setter runs through `GuardedBase.__setattr__` and into the property
setter, where validation happens:

```python
@property
def name(self) -> str:
    """Human-readable name of the experiment."""
    return self._name


@name.setter
def name(self, new: str) -> None:
    self._name = new
```

**Read-only property** — the user can read but cannot assign. Any
attempt to set the attribute is blocked by `GuardedBase.__setattr__`
with a clear error message. If _internal_ code (factory builders, CIF
loaders, etc.) needs to set the value, it calls a private `_set_<name>`
method instead of exposing a public setter:

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

- `GuardedBase.__setattr__` uses the presence of a setter to decide
  writability. Adding a setter "just for internal use" would open the
  attribute to users.
- Private `_set_<name>` methods keep the public API surface minimal and
  intention-clear, while remaining greppable and type-safe.
- The pattern avoids string-based dispatch — every mutator has an
  explicit named method.

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

**Update priority:** lower values run first. This ensures correct
execution order within a datablock (e.g. background before data).

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
`_need_categories_update = True` up to the owning `DatablockItem`.
Serialisation (`as_cif`) and plotting trigger `_update_categories()` if
the flag is set.

### 2.5 Variable System — Parameters and Descriptors

```shell
GuardedBase
└── GenericDescriptorBase               # name, value (validated via AttributeSpec), description
    ├── GenericStringDescriptor         # _value_type = DataTypes.STRING
    └── GenericNumericDescriptor        # _value_type = DataTypes.NUMERIC, + units
        └── GenericParameter            # + free, uncertainty, fit_min, fit_max, constrained
```

CIF-bound concrete classes add a `CifHandler` for serialisation:

| Class               | Base                       | Use case                     |
| ------------------- | -------------------------- | ---------------------------- |
| `StringDescriptor`  | `GenericStringDescriptor`  | Read-only or writable text   |
| `NumericDescriptor` | `GenericNumericDescriptor` | Read-only or writable number |
| `Parameter`         | `GenericParameter`         | Fittable numeric value       |

**Initialisation rule:** all Parameters/Descriptors are initialised with
their default values from `value_spec` (an `AttributeSpec`) **without
any validation** — we trust internal definitions. Changes go through
public property setters, which run both type and value validation.

**Mixin safety:** Parameter/Descriptor classes must not have init
arguments so they can be used as mixins safely (e.g.
`PdTofDataPointMixin`).

### 2.6 Validation

`AttributeSpec` bundles `default`, `data_type`, `validator`,
`allow_none`. Validators include:

| Validator             | Purpose                                |
| --------------------- | -------------------------------------- |
| `TypeValidator`       | Checks Python type against `DataTypes` |
| `RangeValidator`      | `ge`, `le`, `gt`, `lt` bounds checking |
| `MembershipValidator` | Value must be in an allowed set        |
| `RegexValidator`      | Value must match a pattern             |

---

## 3. Experiment System

### 3.1 Experiment Type

An experiment's type is defined by the four enum axes and is **immutable
after creation**. This avoids the complexity of transforming all
internal state when the experiment type changes. The type is stored in
an `ExperimentType` category with four `StringDescriptor`s validated by
`MembershipValidator`s. Public properties are read-only; factory and
CIF-loading code use private setters (`_set_sample_form`,
`_set_beam_mode`, `_set_radiation_probe`, `_set_scattering_type`) during
construction only.

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

Every experiment owns its categories as private attributes with public
read-only or read-write properties:

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
experiment.extinction_type = 'becker-coppens'  # triggers ExtinctionFactory.create(...)
experiment.linked_crystal_type = 'default'  # triggers LinkedCrystalFactory.create(...)
experiment.excluded_regions_type = 'default'  # triggers ExcludedRegionsFactory.create(...)
experiment.linked_phases_type = 'default'  # triggers LinkedPhasesFactory.create(...)
```

**Type switching pattern:** `expt.background_type = 'chebyshev'` rather
than `expt.background.type = 'chebyshev'`. This keeps the API at the
experiment level and makes it clear that the entire category object is
being replaced.

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

Symmetry constraints (cell metric, atomic coordinates, ADPs) are applied
via the `crystallography` module during `_update_categories()`.

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

Each `__init_subclass__` gives every factory its own independent
`_registry` and `_default_rules`.

### 5.2 Default Rules

`_default_rules` maps frozensets of `(axis_name, enum_value)` tuples to
tag strings (preferably enum values for type safety):

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
        }): PeakProfileTypeEnum.JORGENSEN,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC,
    }
```

Resolution uses **largest-subset matching**: the rule whose frozenset is
the biggest subset of the given conditions wins. `frozenset()` acts as a
universal fallback.

### 5.3 Metadata on Registered Classes

Every `@Factory.register`-ed class carries three frozen dataclass
attributes:

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

Concrete classes use `@Factory.register` decorators. To trigger
registration, each package's `__init__.py` must **explicitly import**
every concrete class:

```python
# datablocks/experiment/categories/background/__init__.py
from .chebyshev import ChebyshevPolynomialBackground
from .line_segment import LineSegmentBackground
```

### 5.5 All Factories

| Factory                      | Domain                 | Tags resolve to                                              |
| ---------------------------- | ---------------------- | ------------------------------------------------------------ |
| `BackgroundFactory`          | Background categories  | `LineSegmentBackground`, `ChebyshevPolynomialBackground`     |
| `PeakFactory`                | Peak profiles          | `CwlPseudoVoigt`, `TofJorgensen`, `TofJorgensenVonDreele`, … |
| `InstrumentFactory`          | Instruments            | `CwlPdInstrument`, `TofPdInstrument`, …                      |
| `DataFactory`                | Data collections       | `PdCwlData`, `PdTofData`, `ReflnData`, `TotalData`           |
| `ExtinctionFactory`          | Extinction models      | `BeckerCoppensExtinction`                                    |
| `LinkedCrystalFactory`       | Linked-crystal refs    | `LinkedCrystal`                                              |
| `ExcludedRegionsFactory`     | Excluded regions       | `ExcludedRegions`                                            |
| `LinkedPhasesFactory`        | Linked phases          | `LinkedPhases`                                               |
| `ExperimentTypeFactory`      | Experiment descriptors | `ExperimentType`                                             |
| `CellFactory`                | Unit cells             | `Cell`                                                       |
| `SpaceGroupFactory`          | Space groups           | `SpaceGroup`                                                 |
| `AtomSitesFactory`           | Atom sites             | `AtomSites`                                                  |
| `AliasesFactory`             | Parameter aliases      | `Aliases`                                                    |
| `ConstraintsFactory`         | Parameter constraints  | `Constraints`                                                |
| `FitModeFactory`             | Fit-mode category      | `FitMode`                                                    |
| `JointFitExperimentsFactory` | Joint-fit weights      | `JointFitExperiments`                                        |
| `CalculatorFactory`          | Calculation engines    | `CryspyCalculator`, `CrysfmlCalculator`, `PdffitCalculator`  |
| `MinimizerFactory`           | Minimisers             | `LmfitMinimizer`, `DfolsMinimizer`, …                        |

> **Note:** `ExperimentFactory` and `StructureFactory` are _builder_
> factories with `from_cif_path`, `from_cif_str`, `from_data_path`, and
> `from_scratch` classmethods. `ExperimentFactory` inherits
> `FactoryBase` and uses `@register` on all four concrete experiment
> classes; `_resolve_class` looks up the registered class via
> `default_tag()` + `_supported_map()`. `StructureFactory` is a plain
> class without `FactoryBase` inheritance (only one structure type
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

| Tag                                  | Class                              |
| ------------------------------------ | ---------------------------------- |
| `pseudo-voigt`                       | `CwlPseudoVoigt`                   |
| `pseudo-voigt + empirical asymmetry` | `CwlPseudoVoigtEmpiricalAsymmetry` |
| `thompson-cox-hastings`              | `CwlThompsonCoxHastings`           |
| `jorgensen`                          | `TofJorgensen`                     |
| `jorgensen-von-dreele`               | `TofJorgensenVonDreele`            |
| `double-jorgensen-von-dreele`        | `TofDoubleJorgensenVonDreele`      |
| `gaussian-damped-sinc`               | `TotalGaussianDampedSinc`          |

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

**Extinction tags**

| Tag              | Class                     |
| ---------------- | ------------------------- |
| `becker-coppens` | `BeckerCoppensExtinction` |

**Linked-crystal tags**

| Tag       | Class           |
| --------- | --------------- |
| `default` | `LinkedCrystal` |

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

> **Note:** minimizer variant tags (`lmfit (leastsq)`,
> `lmfit (least_squares)`) are planned but not yet re-implemented after
> the `FactoryBase` migration. See `issues_open.md` for details.

### 5.7 Metadata Classification — Which Classes Get What

#### The Rule

> **If a concrete class is created by a factory, it gets `type_info`,
> `compatibility`, and `calculator_support`.**
>
> **If a `CategoryItem` only exists as a child row inside a
> `CategoryCollection`, it does NOT get these attributes — the
> collection does.**

#### Rationale

A `LineSegment` item (a single background control point) is never
selected, created, or queried by a factory. It is always instantiated
internally by its parent `LineSegmentBackground` collection. The
meaningful unit of selection is the _collection_, not the item. The user
picks "line-segment background" (the collection type), not individual
line-segment points.

#### Singleton CategoryItems — factory-created (get all three)

| Class                              | Factory                 |
| ---------------------------------- | ----------------------- |
| `CwlPdInstrument`                  | `InstrumentFactory`     |
| `CwlScInstrument`                  | `InstrumentFactory`     |
| `TofPdInstrument`                  | `InstrumentFactory`     |
| `TofScInstrument`                  | `InstrumentFactory`     |
| `CwlPseudoVoigt`                   | `PeakFactory`           |
| `CwlPseudoVoigtEmpiricalAsymmetry` | `PeakFactory`           |
| `CwlThompsonCoxHastings`           | `PeakFactory`           |
| `TofJorgensen`                     | `PeakFactory`           |
| `TofJorgensenVonDreele`            | `PeakFactory`           |
| `TotalGaussianDampedSinc`          | `PeakFactory`           |
| `BeckerCoppensExtinction`          | `ExtinctionFactory`     |
| `LinkedCrystal`                    | `LinkedCrystalFactory`  |
| `Cell`                             | `CellFactory`           |
| `SpaceGroup`                       | `SpaceGroupFactory`     |
| `ExperimentType`                   | `ExperimentTypeFactory` |
| `FitMode`                          | `FitModeFactory`        |

#### CategoryCollections — factory-created (get all three)

| Class                           | Factory                      |
| ------------------------------- | ---------------------------- |
| `LineSegmentBackground`         | `BackgroundFactory`          |
| `ChebyshevPolynomialBackground` | `BackgroundFactory`          |
| `PdCwlData`                     | `DataFactory`                |
| `PdTofData`                     | `DataFactory`                |
| `TotalData`                     | `DataFactory`                |
| `ReflnData`                     | `DataFactory`                |
| `ExcludedRegions`               | `ExcludedRegionsFactory`     |
| `LinkedPhases`                  | `LinkedPhasesFactory`        |
| `AtomSites`                     | `AtomSitesFactory`           |
| `Aliases`                       | `AliasesFactory`             |
| `Constraints`                   | `ConstraintsFactory`         |
| `JointFitExperiments`           | `JointFitExperimentsFactory` |

#### CategoryItems that are ONLY children of collections (NO metadata)

| Class                | Parent collection               |
| -------------------- | ------------------------------- |
| `LineSegment`        | `LineSegmentBackground`         |
| `PolynomialTerm`     | `ChebyshevPolynomialBackground` |
| `AtomSite`           | `AtomSites`                     |
| `PdCwlDataPoint`     | `PdCwlData`                     |
| `PdTofDataPoint`     | `PdTofData`                     |
| `TotalDataPoint`     | `TotalData`                     |
| `Refln`              | `ReflnData`                     |
| `LinkedPhase`        | `LinkedPhases`                  |
| `ExcludedRegion`     | `ExcludedRegions`               |
| `Alias`              | `Aliases`                       |
| `Constraint`         | `Constraints`                   |
| `JointFitExperiment` | `JointFitExperiments`           |

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

The calculator performs the actual diffraction computation. It is
attached per-experiment on the `ExperimentBase` object. Each experiment
auto-resolves its calculator on first access based on the data
category's `calculator_support` metadata and
`CalculatorFactory._default_rules`. The `CalculatorFactory` filters its
registry by `engine_imported` (whether the third-party library is
available in the environment).

The experiment exposes the standard switchable-category API:

- `calculator` — read-only property (lazy, auto-resolved on first
  access)
- `calculator_type` — getter + setter
- `show_supported_calculator_types()` — filtered by data category
  support
- `show_current_calculator_type()`

### 6.2 Minimiser

The minimiser drives the optimisation loop. `MinimizerFactory` creates
instances by tag (e.g. `'lmfit'`, `'dfols'`).

### 6.3 Fitter

`Fitter` wraps a minimiser instance and orchestrates the fitting
workflow:

1. Collect `free_parameters` from structures + experiments.
2. Record start values.
3. Build an objective function that calls the calculator.
4. Delegate to `minimizer.fit()`.
5. Sync results (values + uncertainties) back to parameters.

### 6.4 Analysis Object

`Analysis` is bound to a `Project` and provides the high-level API:

- Minimiser selection: `current_minimizer`,
  `show_available_minimizers()`
- Fit mode: `fit_mode` (`CategoryItem` with a `mode` descriptor
  validated by `FitModeEnum`); `'single'` fits each experiment
  independently, `'joint'` fits all simultaneously with weights from
  `joint_fit_experiments`.
- Joint-fit weights: `joint_fit_experiments` (`CategoryCollection` of
  per-experiment weight entries); sibling of `fit_mode`, not a child.
- Parameter tables: `show_all_params()`, `show_fittable_params()`,
  `show_free_params()`, `how_to_access_parameters()`
- Fitting: `fit()`, `show_fit_results()`
- Aliases and constraints (switchable categories with `aliases_type`,
  `constraints_type`, `fit_mode_type`, `joint_fit_experiments_type`)

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
| `project.verbosity`   | `str`         | Console output level (full/short/silent) |

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
├── summary.cif          # Summary report
├── structures/
│   └── lbco.cif         # One file per structure
├── experiments/
│   └── hrpt.cif         # One file per experiment
└── analysis/
    └── analysis.cif     # Analysis settings
```

### 7.3 Verbosity

`Project.verbosity` controls how much console output operations produce.
It is backed by `VerbosityEnum` (in `utils/enums.py`) and accepts three
values:

| Level    | Enum member            | Behaviour                                          |
| -------- | ---------------------- | -------------------------------------------------- |
| `full`   | `VerbosityEnum.FULL`   | Multi-line output with headers, tables, and detail |
| `short`  | `VerbosityEnum.SHORT`  | One-line status message per action                 |
| `silent` | `VerbosityEnum.SILENT` | No console output                                  |

The default is `'full'`.

```python
project.verbosity = 'short'
```

**Resolution order:** methods that produce console output (e.g.
`analysis.fit()`, `experiments.add_from_data_path()`) accept an optional
`verbosity` keyword argument. When the argument is `None` (the default),
the method reads `project.verbosity`. When a string is passed, it
overrides the project-level setting for that single call.

```python
# Use project-level default for all operations
project.verbosity = 'short'
project.analysis.fit()                         # → short mode

# Override for a single call
project.analysis.fit(verbosity='silent')       # → silent, project stays short
```

**Output styles per level:**

- **Data loading** — `full`: paragraph header + detail line; `short`:
  `✅ Data loaded: Experiment 🔬 'name'. N points.`; `silent`: nothing.
- **Fitting** — `full`: per-iteration progress table with improvement
  percentages; `short`: one-row-per-experiment summary table; `silent`:
  nothing.

---

## 8. User-Facing API Patterns

All examples below are drawn from the actual tutorials (`tutorials/`).

> **Notebook workflow:** Jupyter notebooks (`*.ipynb`) in
> `docs/docs/tutorials/` are generated artifacts. Edit only the
> corresponding `*.py` script, then run `pixi run notebook-prepare` to
> regenerate the notebook. Never edit `*.ipynb` files by hand.

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
# Calculator is auto-resolved per experiment; override if needed
project.experiments['hrpt'].show_supported_calculator_types()
project.experiments['hrpt'].calculator_type = 'cryspy'
project.analysis.current_minimizer = 'lmfit'

# Plot before fitting
project.plotter.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# Select free parameters
project.structures['lbco'].cell.length_a.free = True
project.experiments['hrpt'].linked_phases['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True

# Inspect free parameters
project.analysis.display.free_params()

# Fit and show results
project.analysis.fit()
project.analysis.display.fit_results()

# Plot after fitting
project.plotter.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

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
expt.peak_profile_type = 'jorgensen'
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
# Calculator is auto-resolved to 'pdffit' for total scattering experiments
```

---

## 9. Design Principles

### 9.1 Naming and CIF Conventions

- Follow CIF naming conventions where possible. Deviate for better API
  design when necessary, but keep the spirit of CIF names.
- Reuse the concept of datablocks and categories from CIF.
- `DatablockItem` = one CIF `data_` block, `DatablockCollection` = set
  of blocks.
- `CategoryItem` = one CIF category, `CategoryCollection` = CIF loop.
- **Free-flag encoding**: A parameter's free/fixed status is encoded in
  CIF via uncertainty brackets. `3.89` = fixed, `3.89(2)` = free with
  esd, `3.89()` = free without esd. There is no separate list of free
  parameters; the brackets are the single source of truth.

### 9.2 Immutability of Experiment Type

The experiment type (the four enum axes) can only be set at creation
time. It cannot be changed afterwards. This avoids the complexity of
maintaining different state transformations when switching between
fundamentally different experiment configurations.

### 9.3 Category Type Switching

In contrast to experiment type, categories that have multiple
implementations (peak profiles, backgrounds, instruments) can be
switched at runtime by the user. The API pattern uses a type property on
the **experiment**, not on the category itself:

```python
# ✅ Correct — type property on the experiment
expt.background_type = 'chebyshev'

# ❌ Not used — type property on the category
expt.background.type = 'chebyshev'
```

This makes it clear that the entire category object is being replaced
and simplifies maintenance.

### 9.4 Switchable-Category Convention

Categories whose concrete implementation can be swapped at runtime
(background, peak profile, etc.) are called **switchable categories**.
**Every category must be factory-based** — even if only one
implementation exists today. This ensures a uniform API, consistent
discoverability, and makes adding a second implementation trivial.

| Facet           | Naming pattern                               | Example                                          |
| --------------- | -------------------------------------------- | ------------------------------------------------ |
| Current object  | `<category>` property (read-only)            | `expt.background`, `expt.peak`                   |
| Active type tag | `<category>_type` property (getter + setter) | `expt.background_type`, `expt.peak_profile_type` |
| Show supported  | `show_supported_<category>_types()`          | `expt.show_supported_background_types()`         |
| Show current    | `show_current_<category>_type()`             | `expt.show_current_peak_profile_type()`          |

The convention applies universally:

- **Experiment:** `calculator_type`, `background_type`,
  `peak_profile_type`, `extinction_type`, `linked_crystal_type`,
  `excluded_regions_type`, `linked_phases_type`, `instrument_type`,
  `data_type`.
- **Structure:** `cell_type`, `space_group_type`, `atom_sites_type`.
- **Analysis:** `aliases_type`, `constraints_type`, `fit_mode_type`,
  `joint_fit_experiments_type`.

**Design decisions:**

- The **experiment owns** the `_type` setter because switching replaces
  the entire category object
  (`self._background = BackgroundFactory.create(...)`).
- The **experiment owns** the `show_*` methods because they are
  one-liners that delegate to `Factory.show_supported(...)` and can pass
  experiment-specific context (e.g. `scattering_type`, `beam_mode` for
  peak filtering).
- Concrete category subclasses provide a public `show()` method for
  displaying the current content (not on the base
  `CategoryItem`/`CategoryCollection`).

### 9.5 Discoverable Supported Options

The user can always discover what is supported for the current
experiment:

```python
expt.show_supported_peak_profile_types()
expt.show_supported_background_types()
expt.show_supported_calculator_types()
expt.show_supported_extinction_types()
expt.show_supported_linked_crystal_types()
expt.show_supported_excluded_regions_types()
expt.show_supported_linked_phases_types()
expt.show_supported_instrument_types()
expt.show_supported_data_types()
struct.show_supported_cell_types()
struct.show_supported_space_group_types()
struct.show_supported_atom_sites_types()
project.analysis.show_supported_aliases_types()
project.analysis.show_supported_constraints_types()
project.analysis.show_supported_fit_mode_types()
project.analysis.show_supported_joint_fit_experiments_types()
project.analysis.show_available_minimizers()
```

Available calculators are filtered by `engine_imported` (whether the
library is installed) and by the experiment's data category
`calculator_support` metadata.

### 9.6 Enums for Finite Value Sets

Every attribute, descriptor, or configuration option that accepts a
**finite, closed set of values** must be represented by a `(str, Enum)`
class. This applies to:

- Factory tags (§5.6) — e.g. `PeakProfileTypeEnum`, `CalculatorEnum`.
- Experiment-axis values — e.g. `SampleFormEnum`, `BeamModeEnum`.
- Category descriptors with enumerated choices — e.g. fit mode
  (`FitModeEnum.SINGLE`, `FitModeEnum.JOINT`).

The enum serves as the **single source of truth** for valid values,
their user-facing string representations, and their descriptions.
Benefits:

- **Autocomplete and typo safety** — IDEs list valid members;
  misspellings are caught at assignment time.
- **Greppable** — searching for `FitModeEnum.JOINT` finds every code
  path that handles joint fitting.
- **Type-safe dispatch** — `if mode == FitModeEnum.JOINT:` is checked by
  type checkers; `if mode == 'joint':` is not.
- **Consistent validation** — use `MembershipValidator` with the enum
  members instead of `RegexValidator` with hand-written patterns.

**Rule:** internal code must compare against enum members, never raw
strings. User-facing setters accept either the enum member or its string
value (because `str(EnumMember) == EnumMember.value` for `(str, Enum)`),
but internal dispatch always uses the enum:

```python
# ✅ Correct — compare with enum
if self._fit_mode.mode.value == FitModeEnum.JOINT:

# ❌ Wrong — compare with raw string
if self._fit_mode.mode.value == 'joint':
```

### 9.7 Flat Category Structure — No Nested Categories

Following CIF conventions, categories are **flat siblings** within their
owner (datablock or analysis object). A category must never be a child
of another category of a different type. Categories can reference each
other via IDs, but the ownership hierarchy is always:

```
Owner (DatablockItem / Analysis)
├── CategoryA   (CategoryItem or CategoryCollection)
├── CategoryB   (CategoryItem or CategoryCollection)
└── CategoryC   (CategoryItem or CategoryCollection)
```

Never:

```
Owner
└── CategoryA
    └── CategoryB   ← WRONG: CategoryB is a child of CategoryA
```

**Example — `fit_mode` and `joint_fit_experiments`:** `fit_mode` is a
`CategoryItem` holding the active strategy (`'single'` or `'joint'`).
`joint_fit_experiments` is a separate `CategoryCollection` holding
per-experiment weights. Both are direct children of `Analysis`, not
nested:

```python
# ✅ Correct — sibling categories on Analysis
project.analysis.fit_mode.mode = 'joint'
project.analysis.joint_fit_experiments['npd'].weight = 0.7

# ❌ Wrong — joint_fit_experiments as a child of fit_mode
project.analysis.fit_mode.joint_fit_experiments['npd'].weight = 0.7
```

In CIF output, sibling categories appear as independent blocks:

```
_analysis.fit_mode  joint

loop_
_joint_fit_experiment.id
_joint_fit_experiment.weight
npd  0.7
xrd  0.3
```

### 9.8 Property Docstring and Type-Hint Template

Every public property backed by a private `Parameter`,
`NumericDescriptor`, or `StringDescriptor` attribute must follow the
template below. The `description` field on the descriptor is the
**single source of truth**; docstrings and type hints are mechanically
derived from it.

**Definitions:**

| Symbol    | Meaning                                                                                |
| --------- | -------------------------------------------------------------------------------------- |
| `{desc}`  | `description` string without trailing period                                           |
| `{units}` | `units` string; omit the `({units})` parenthetical when absent/empty                   |
| `{Type}`  | Descriptor class name: `Parameter`, `NumericDescriptor`, or `StringDescriptor`         |
| `{ann}`   | Setter value annotation: `float` for numeric descriptors, `str` for string descriptors |

**Template — writable property:**

```python
@property
def length_a(self) -> Parameter:
    """Length of the a axis of the unit cell (Å).

    Reading this property returns the underlying ``Parameter``
    object. Assigning to it updates the parameter value.
    """
    return self._length_a

@length_a.setter
def length_a(self, value: float) -> None:
    self._length_a.value = value
```

**Template — read-only property:**

```python
@property
def length_a(self) -> Parameter:
    """Length of the a axis of the unit cell (Å).

    Reading this property returns the underlying ``Parameter``
    object.
    """
    return self._length_a
```

**Quick-reference table:**

| Element                | Text                                                                                                           |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| Getter summary line    | `"""{desc} ({units}).` (or `"""{desc}.` when unitless)                                                         |
| Getter body (writable) | `Reading this property returns the underlying ``{Type}`` object. Assigning to it updates the parameter value.` |
| Getter body (readonly) | `Reading this property returns the underlying ``{Type}`` object.`                                              |
| Setter docstring       | _(none — not rendered by griffe / MkDocs)_                                                                     |
| Getter annotation      | `-> {Type}`                                                                                                    |
| Setter annotation      | `value: {ann}` and `-> None`                                                                                   |

**Notes:**

- Getter docstrings have **no** `Args:` or `Returns:` sections.
- Setters have **no** docstring.
- Avoid markdown emphasis (`*a*`) in docstrings; use plain text to stay
  in sync with the `description` field.
- The CI tool `pixi run param-consistency-check` validates compliance;
  `pixi run param-consistency-fix` auto-fixes violations.

### 9.9 Lint Complexity Thresholds

The Pylint-style complexity limits in `pyproject.toml` are **intentional
code-quality guardrails**, not arbitrary numbers. A violation is a
signal that the function or class needs refactoring — not that the
threshold needs raising.

The project uses **ruff's defaults** for all PLR thresholds, with one
exception: `max-args` and `max-positional-args` are set to **6** instead
of the ruff default of 5, because ruff counts `self`/`cls` while
traditional pylint does not. Setting 6 in ruff matches pylint's standard
limit of 5 real parameters per function.

| Threshold             | Value | Rule    |
| --------------------- | ----- | ------- |
| `max-args`            | 6     | PLR0913 |
| `max-positional-args` | 6     | PLR0917 |
| `max-branches`        | 12    | PLR0912 |
| `max-statements`      | 50    | PLR0915 |
| `max-locals`          | 15    | PLR0914 |
| `max-nested-blocks`   | 5     | PLR1702 |
| `max-returns`         | 6     | PLR0911 |
| `max-public-methods`  | 20    | PLR0904 |

**Rules:**

- **Do not raise thresholds.** The current values represent the
  project's design intent for maximum acceptable complexity.
- **Do not add `# noqa` comments** (or any other mechanism) to silence
  complexity rules such as `PLR0912`, `PLR0913`, `PLR0914`, `PLR0915`,
  `PLR0917`, `PLR1702`.
- **Refactor the code instead:** extract helper functions, introduce
  parameter objects, flatten nesting, use early returns, etc.
- **For complex refactors** that touch many lines or change public API,
  propose a refactoring plan and wait for approval before proceeding.

---

## 10. Test Strategy

Every new feature, category, factory, or bug fix must ship with tests.
The project enforces a multi-layered testing approach that catches
regressions at different levels of abstraction.

### 10.1 Test Layers

| Layer                 | Location                | Runner command               | Scope                                                                                                                |
| --------------------- | ----------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Unit**              | `tests/unit/`           | `pixi run unit-tests`        | Single class or function in isolation. Fast, no I/O, no external engines.                                            |
| **Functional**        | `tests/functional/`     | `pixi run functional-tests`  | Multi-component workflows (e.g. create experiment → load data → fit). No external data files beyond tiny test stubs. |
| **Integration**       | `tests/integration/`    | `pixi run integration-tests` | End-to-end pipelines using real calculation engines (cryspy, crysfml, pdffit2) and real data files from `data/`.     |
| **Script (tutorial)** | `tools/test_scripts.py` | `pixi run script-tests`      | Runs each tutorial `*.py` script under `docs/docs/tutorials/` as a subprocess and checks for a zero exit code.       |
| **Notebook**          | `docs/docs/tutorials/`  | `pixi run notebook-tests`    | Executes every Jupyter notebook end-to-end via `nbmake`.                                                             |

### 10.2 Directory Structure Convention

The unit-test tree **mirrors** the source tree:

```
src/easydiffraction/<pkg>/<module>.py
    → tests/unit/easydiffraction/<pkg>/test_<module>.py
```

Two additional patterns are recognised:

1. **Supplementary coverage files** — `test_<module>_coverage.py`,
   `test_<module>_more.py`, etc. sit beside the main test file and add
   extra scenarios.
2. **Parent-level roll-up** — for category packages that contain only
   `default.py` and `factory.py`, a single `test_<package_name>.py` one
   directory up covers the whole package (e.g.
   `categories/test_experiment_type.py` covers
   `categories/experiment_type/default.py` and
   `categories/experiment_type/factory.py`).

The CI tool `pixi run test-structure-check` validates that every source
module has a corresponding test file and reports any gaps. Explicit name
aliases (e.g. `variable.py` tested by `test_parameters.py`) are declared
in `KNOWN_ALIASES` inside the tool script.

### 10.3 What to Test per Source Module Type

| Source module type               | Required tests                                                                                                                                             |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Core base class** (`core/`)    | Instantiation, public properties, validation edge cases, identity wiring.                                                                                  |
| **Factory** (`factory.py`)       | Registration check, `supported_tags()`, `default_tag()`, `create()` for each tag, `show_supported()` output, invalid-tag handling.                         |
| **Category** (`default.py`)      | Instantiation, all public properties (read + write where applicable), CIF round-trip (`as_cif` → `from_cif`), parameter enumeration.                       |
| **Enum** (`enums.py`)            | Membership of all members, `default()` method, `description()` for every member, `StrEnum` string equality.                                                |
| **Datablock item** (`base.py`)   | Construction, switchable-category full API (`<cat>`, `<cat>_type` get/set, `show_supported_<cat>_types`, `show_current_<cat>_type`), `show`/`show_as_cif`. |
| **Collection** (`collection.py`) | `create`, `add`, `remove`, `names`, `show_names`, `show_params`, iteration, duplicate-name handling.                                                       |
| **Calculator / Minimizer**       | `can_handle()` with compatible and incompatible experiment types, `_compute()` stub or mock.                                                               |
| **Display / IO**                 | Input → output for representative cases; file-not-found and malformed-input error paths.                                                                   |

### 10.4 Test Conventions

- **No test-ordering dependence.** Each test must be self-contained. Use
  `monkeypatch` to set `Logger._reaction` when the test expects a raised
  exception (another test may have leaked WARN mode via the global
  `Logger` singleton).
- **Error paths are tested explicitly.** Use `pytest.raises()` (with
  `monkeypatch` for Logger RAISE mode) for `log.error()` calls that
  specify `exc_type`.
- **`@typechecked` setters raise `typeguard.TypeCheckError`**, not
  `TypeError`. Tests must catch the correct exception.
- **Use `capsys` / `capfd`** for asserting console output from `show_*`
  methods.
- **Prefer `tmp_path`** (pytest fixture) for file-system tests.
- **No sleeping, no network calls, no real calculation engines** in unit
  tests.
- Test files carry the SPDX license header and a module-level docstring.
  They are exempt from most lint rules (ANN, D, DOC, INP001, S101, etc.)
  per `pyproject.toml`.

### 10.5 Coverage Threshold

The minimum line-coverage threshold is **70 %** (`fail_under = 70` in
`pyproject.toml`). The project aspires to test every code path; the
threshold is a safety net, not a target.

Run `pixi run unit-tests-coverage` for a per-module report.

---

## 11. Issues

- **Open:** [`issues_open.md`](issues_open.md) — prioritised backlog.
- **Closed:** [`issues_closed.md`](issues_closed.md) — resolved items
  for reference.

When a resolution affects the architecture described above, the relevant
sections of this document are updated accordingly.
