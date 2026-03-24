# Design Document: `TypeInfo`, `Compatibility`, `CalculatorSupport`, and `FactoryBase`

**Date:** 2026-03-19  
**Status:** Proposed  
**Scope:** `easydiffraction` core infrastructure and all category/factory
modules

---

## 1. Motivation

The current codebase has several overlapping mechanisms for describing what a
concrete class _is_, what experimental conditions it works under, and which
factories can create it. This leads to:

- **Duplication.** Descriptions live on both enums (e.g.
  `BackgroundTypeEnum.description()`) and classes (e.g.
  `LineSegmentBackground._description`). Supported-combination knowledge lives
  in hand-built factory dicts _and_ implicitly in classes.
- **Scattered knowledge.** Adding a new variant (e.g. a new peak profile)
  requires editing three or more files: the class, the enum, and the factory's
  `_supported` dict.
- **Inconsistent factory patterns.** Each factory has its own shape: some use
  nested dicts with 1–3 levels, some use flat dicts with
  `'description'`/`'class'` sub-dicts, some have `_supported_map()` methods,
  others have `_supported` class attributes. Validation and `show_supported_*()`
  methods are reimplemented in every factory.

This design introduces three small, focused metadata objects and one shared
factory base class that together eliminate duplication, unify factories, and
make the system self-describing.

---

## 2. Existing Architecture (Relevant Parts)

### 2.1 Category Hierarchy

```
GuardedBase
├── CategoryItem          — single-instance category (e.g. Cell, SpaceGroup, Instrument, Peak)
└── CollectionBase
    └── CategoryCollection — multi-item collection (e.g. AtomSites, BackgroundBase, DataBase)
```

- **Singleton categories** are `CategoryItem` subclasses used directly on an
  experiment or structure. There is exactly one instance per parent. Examples:
  `Cell`, `SpaceGroup`, `ExperimentType`, `Extinction`, `LinkedCrystal`,
  `PeakBase` subclasses, `InstrumentBase` subclasses.
- **Collection categories** are `CategoryCollection` subclasses that hold many
  `CategoryItem` children. Examples: `AtomSites` (holds `AtomSite` items),
  `LineSegmentBackground` (holds `LineSegment` items), `PdCwlData` (holds
  `PdCwlDataPoint` items).

### 2.2 Current Factories

| Factory               | Location                                      | `_supported` shape                                                    |
| --------------------- | --------------------------------------------- | --------------------------------------------------------------------- |
| `PeakFactory`         | `experiment/categories/peak/factory.py`       | `{ScatteringType: {BeamMode: {ProfileType: Class}}}` (3-level nested) |
| `InstrumentFactory`   | `experiment/categories/instrument/factory.py` | `{ScatteringType: {BeamMode: {SampleForm: Class}}}` (3-level nested)  |
| `DataFactory`         | `experiment/categories/data/factory.py`       | `{SampleForm: {ScatteringType: {BeamMode: Class}}}` (3-level nested)  |
| `BackgroundFactory`   | `experiment/categories/background/factory.py` | `{BackgroundTypeEnum: Class}` (1-level flat)                          |
| `ExperimentFactory`   | `experiment/item/factory.py`                  | `{ScatteringType: {SampleForm: {BeamMode: Class}}}` (3-level nested)  |
| `CalculatorFactory`   | `analysis/calculators/factory.py`             | `{name: {description, class}}` (flat dict)                            |
| `MinimizerFactory`    | `analysis/minimizers/factory.py`              | `{name: {engine, method, description, class}}` (flat dict)            |
| `RendererFactoryBase` | `display/base.py`                             | `{engine_name: {description, class}}` (flat dict, abstract)           |

Each factory independently implements: lookup, validation, error messages,
`show_supported_*()` / `list_supported_*()`, and default selection — typically
60–130 lines of mostly-similar code.

### 2.3 Current Enums

- **Experimental-axis enums** (kept as-is): `SampleFormEnum`,
  `ScatteringTypeEnum`, `BeamModeEnum`, `RadiationProbeEnum` — defined in
  `experiment/item/enums.py`. Each has `.default()` and `.description()`.
- **Category-specific enums** (to be removed): `BackgroundTypeEnum` (in
  `background/enums.py`) and `PeakProfileTypeEnum` (in
  `experiment/item/enums.py`). These duplicate information that belongs on the
  concrete classes.

### 2.4 `Identity` (Unchanged)

`Identity` (in `core/identity.py`) resolves CIF hierarchy:
`datablock_entry_name`, `category_code`, `category_entry_name`. It is a
_separate concern_ from the metadata introduced here and remains untouched.

---

## 3. New Design

### 3.1 Overview

Three frozen dataclasses and one base factory class:

| Object              | Purpose                                           | Lives on                                              |
| ------------------- | ------------------------------------------------- | ----------------------------------------------------- |
| `TypeInfo`          | "What am I?" — stable tag + human description     | Every factory-created class                           |
| `Compatibility`     | "Under what experimental conditions?" — four axes | Every factory-created class with experimental scope   |
| `CalculatorSupport` | "Which calculators can handle me?"                | Every factory-created class that a calculator touches |
| `FactoryBase`       | Shared registration, lookup, listing, display     | Every factory (as base class)                         |

A new enum is also introduced:

| Enum             | Purpose                                                      |
| ---------------- | ------------------------------------------------------------ |
| `CalculatorEnum` | Closed set of calculator identifiers, replacing bare strings |

### 3.2 File Location

Metadata types live in a single file:

```
src/easydiffraction/core/metadata.py     — TypeInfo, Compatibility, CalculatorSupport
```

`CalculatorEnum` lives alongside the other experimental-axis enums:

```
src/easydiffraction/datablocks/experiment/item/enums.py  (add CalculatorEnum here)
```

`FactoryBase` lives in:

```
src/easydiffraction/core/factory.py
```

---

## 4. Detailed Specification

### 4.1 `TypeInfo`

```python
# core/metadata.py

from dataclasses import dataclass


@dataclass(frozen=True)
class TypeInfo:
    """Stable identity and human-readable description for a
    factory-created class.

    Attributes:
        tag: Short, stable string identifier used for serialization,
            user-facing selection, and factory lookup. Must be unique
            within a factory's registry. Examples: 'line-segment',
            'pseudo-voigt', 'cryspy'.
        description: One-line human-readable explanation. Used in
            show_supported() tables and documentation.
    """

    tag: str
    description: str = ''
```

**Replaces:**

- `BackgroundTypeEnum` values and `.description()` method
- `PeakProfileTypeEnum` values and `.description()` method
- `CalculatorFactory._potential_calculators` description strings
- `MinimizerFactory._available_minimizers` description strings
- `RendererFactoryBase._registry()` description strings
- `_description` class attributes on `LineSegmentBackground`,
  `ChebyshevPolynomialBackground`

### 4.2 `Compatibility`

```python
# core/metadata.py

from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Compatibility:
    """Experimental conditions under which a class can be used.

    Each field is a frozenset of enum values representing the set of
    supported values for that axis. An empty frozenset means
    "compatible with any value of this axis" (i.e. no restriction).

    The four axes mirror ExperimentType exactly:
        sample_form:     SampleFormEnum      (powder, single crystal)
        scattering_type: ScatteringTypeEnum   (bragg, total)
        beam_mode:       BeamModeEnum         (constant wavelength, time-of-flight)
        radiation_probe: RadiationProbeEnum   (neutron, xray)
    """

    sample_form: FrozenSet = frozenset()
    scattering_type: FrozenSet = frozenset()
    beam_mode: FrozenSet = frozenset()
    radiation_probe: FrozenSet = frozenset()

    def supports(self, **kwargs) -> bool:
        """Check if this compatibility matches the given conditions.

        Each kwarg key must be a field name, value must be an enum
        member. Returns True if every provided value is in the
        corresponding frozenset (or the frozenset is empty, meaning
        'any').

        Example::

            compat.supports(
                scattering_type=ScatteringTypeEnum.BRAGG,
                beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
            )
        """
        for axis, value in kwargs.items():
            allowed = getattr(self, axis)
            if allowed and value not in allowed:
                return False
        return True
```

**Replaces:**

- All nested `_supported` dicts in `PeakFactory`, `InstrumentFactory`,
  `DataFactory`, `ExperimentFactory`. The factory no longer manually encodes
  which enum combinations are valid — it queries each registered class's
  `compatibility.supports(...)`.

### 4.3 `CalculatorSupport`

```python
# core/metadata.py


@dataclass(frozen=True)
class CalculatorSupport:
    """Which calculation engines can handle this class.

    Attributes:
        calculators: Frozenset of CalculatorEnum values. Empty means
            "any calculator" (no restriction).
    """

    calculators: FrozenSet = frozenset()

    def supports(self, calculator) -> bool:
        """Check if a specific calculator can handle this class.

        Args:
            calculator: A CalculatorEnum value.

        Returns:
            True if the calculator is in the set, or if the set is
            empty (meaning any calculator is accepted).
        """
        if not self.calculators:
            return True
        return calculator in self.calculators
```

**Why separate from `Compatibility`:** Calculators are not an experimental axis
— they are an implementation concern. Mixing them into `Compatibility` creates
special cases (`if axis == 'calculators'`) and inconsistent naming (singular
axes vs. plural). Keeping them separate means `Compatibility` is perfectly
uniform (four parallel frozenset fields) and `CalculatorSupport` is a clean
single-purpose object.

### 4.4 `CalculatorEnum`

```python
# datablocks/experiment/item/enums.py (alongside existing enums)


class CalculatorEnum(str, Enum):
    """Known calculation engine identifiers."""

    CRYSPY = 'cryspy'
    CRYSFML = 'crysfml'
    PDFFIT = 'pdffit'
```

**Replaces:** Bare `'cryspy'` / `'crysfml'` / `'pdffit'` strings scattered
throughout the code. Provides type safety, IDE completion, and typo protection.

### 4.5 `FactoryBase`

```python
# core/factory.py

from __future__ import annotations
from typing import Any, Dict, List, Optional, Type

from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class FactoryBase:
    """Shared base for all factories.

    Provides a unified pattern: registration, supported-map building,
    lookup, listing, and display. Concrete factories inherit from this
    and only need to define:

        _registry:      list — populated by @register decorator
        _default_tag:   str  — fallback tag when caller passes None
                               and no conditions are given
        _default_rules: dict — context-dependent defaults (optional)

    Optionally override _supported_map() for special filtering (e.g.
    CalculatorFactory filters by engine_imported).
    """

    _registry: List[Type] = []
    _default_tag: str = ''
    _default_rules: Dict[frozenset, str] = {}

    def __init_subclass__(cls, **kwargs):
        """Each subclass gets its own independent registry and rules."""
        super().__init_subclass__(**kwargs)
        cls._registry = []
        if '_default_rules' not in cls.__dict__:
            cls._default_rules = {}

    @classmethod
    def register(cls, klass):
        """Class decorator to register a concrete class with this
        factory.

        Usage::

            @SomeFactory.register
            class MyClass(SomeBase):
                type_info = TypeInfo(...)
                ...

        Returns:
            The class, unmodified.
        """
        cls._registry.append(klass)
        return klass

    @classmethod
    def _supported_map(cls) -> Dict[str, Type]:
        """Build {tag: class} mapping from all registered classes.

        Each registered class must have a ``type_info`` attribute with
        a ``tag`` property.
        """
        return {klass.type_info.tag: klass for klass in cls._registry}

    @classmethod
    def supported_tags(cls) -> List[str]:
        """Return list of supported tags."""
        return list(cls._supported_map().keys())

    @classmethod
    def default_tag(cls, **conditions) -> str:
        """Resolve the default tag for the given experimental context.

        Looks up ``_default_rules`` using frozenset of condition items
        as key. Falls back to ``_default_tag`` if no rule matches.

        Args:
            **conditions: Experimental-axis values, e.g.
                scattering_type=ScatteringTypeEnum.BRAGG,
                beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.

        Returns:
            The default tag string.

        Resolution strategy: the rule whose key is the largest subset
        of the given conditions wins. This allows both broad rules
        (e.g. just scattering_type) and specific rules (e.g.
        scattering_type + beam_mode) to coexist. If no rule matches,
        ``_default_tag`` is returned.
        """
        if not cls._default_rules or not conditions:
            return cls._default_tag

        condition_set = frozenset(conditions.items())
        best_match_tag = cls._default_tag
        best_match_size = 0

        for rule_key, rule_tag in cls._default_rules.items():
            if rule_key <= condition_set and len(rule_key) > best_match_size:
                best_match_tag = rule_tag
                best_match_size = len(rule_key)

        return best_match_tag

    @classmethod
    def create(cls, tag: Optional[str] = None, **kwargs) -> Any:
        """Instantiate a registered class by tag.

        Args:
            tag: The type_info.tag value. If None, uses _default_tag.
            **kwargs: Passed to the class constructor.

        Returns:
            A new instance of the registered class.

        Raises:
            ValueError: If the tag is not in the registry.
        """
        if tag is None:
            tag = cls._default_tag
        supported = cls._supported_map()
        if tag not in supported:
            raise ValueError(f"Unsupported type: '{tag}'. Supported: {list(supported.keys())}")
        return supported[tag](**kwargs)

    @classmethod
    def create_default_for(cls, **conditions) -> Any:
        """Instantiate the default class for the given experimental
        context.

        Combines ``default_tag()`` with ``create()``. Use this when
        creating objects where the choice depends on experimental
        configuration.

        Args:
            **conditions: Experimental-axis values, e.g.
                scattering_type=ScatteringTypeEnum.BRAGG.

        Returns:
            A new instance of the resolved default class.
        """
        tag = cls.default_tag(**conditions)
        return cls.create(tag)

    @classmethod
    def supported_for(
        cls,
        *,
        calculator=None,
        **conditions,
    ) -> List[Type]:
        """Return classes matching experimental conditions and
        calculator.

        Args:
            calculator: Optional CalculatorEnum value. If given, only
                return classes whose calculator_support includes it.
            **conditions: Keyword arguments passed to
                Compatibility.supports(). Common keys:
                sample_form, scattering_type, beam_mode,
                radiation_probe.

        Returns:
            List of matching registered classes.
        """
        result = []
        for klass in cls._registry:
            compat = getattr(klass, 'compatibility', None)
            if compat and not compat.supports(**conditions):
                continue
            calc_support = getattr(klass, 'calculator_support', None)
            if calculator and calc_support and not calc_support.supports(calculator):
                continue
            result.append(klass)
        return result

    @classmethod
    def show_supported(
        cls,
        *,
        calculator=None,
        **conditions,
    ) -> None:
        """Pretty-print a table of supported types, optionally
        filtered by experimental conditions and/or calculator.

        Args:
            calculator: Optional CalculatorEnum filter.
            **conditions: Passed to Compatibility.supports().
        """
        matching = cls.supported_for(calculator=calculator, **conditions)
        columns_headers = ['Type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = [[klass.type_info.tag, klass.type_info.description] for klass in matching]
        console.paragraph('Supported types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
```

**What this replaces:** All per-factory implementations of `_supported_map()`,
`list_supported_*()`, `show_supported_*()`, `create()`, and validation
boilerplate.

---

## 5. Context-Dependent Defaults

### 5.1 The Problem

A single `_default_tag` per factory is insufficient. The correct default depends
on the experimental context:

| Factory             | Context              | Correct default                      |
| ------------------- | -------------------- | ------------------------------------ |
| `PeakFactory`       | Bragg + CWL          | `'pseudo-voigt'`                     |
| `PeakFactory`       | Bragg + TOF          | `'tof-pseudo-voigt-ikeda-carpenter'` |
| `PeakFactory`       | Total (any)          | `'gaussian-damped-sinc'`             |
| `CalculatorFactory` | Bragg (any)          | `'cryspy'`                           |
| `CalculatorFactory` | Total (any)          | `'pdffit'`                           |
| `InstrumentFactory` | CWL + Powder         | `'cwl-pd'`                           |
| `InstrumentFactory` | TOF + SC             | `'tof-sc'`                           |
| `DataFactory`       | Powder + Bragg + CWL | `'bragg-pd-cwl'`                     |
| `DataFactory`       | Powder + Total + any | `'total-pd'`                         |
| `BackgroundFactory` | (any)                | `'line-segment'`                     |
| `MinimizerFactory`  | (any)                | `'lmfit'`                            |

### 5.2 The Solution: `_default_rules` + `default_tag(**conditions)`

Each factory defines a `_default_rules` dict mapping frozensets of
`(axis, value)` pairs to default tags. The `default_tag()` method on
`FactoryBase` resolves the best match using subset matching: the rule whose key
is the _largest subset_ of the given conditions wins.

- **Broad rules** (e.g. `{('scattering_type', TOTAL)}`) match any experiment
  with `scattering_type=TOTAL`, regardless of beam mode.
- **Specific rules** (e.g. `{('scattering_type', BRAGG), ('beam_mode', TOF)}`)
  take priority over broader ones when both match because they have more keys.
- **`_default_tag`** is the fallback when no rule matches (e.g. when
  `default_tag()` is called with no conditions).

### 5.3 Two Creation Methods

`FactoryBase` provides two creation paths:

- **`create(tag)`** — explicit tag, used when the user or code knows exactly
  what it wants. Falls back to `_default_tag` if `tag` is `None`.
- **`create_default_for(**conditions)`** — context-dependent, used when creating objects during experiment construction. Resolves the correct default via `default_tag()`
  then creates it.

### 5.4 Examples

```python
# Explicit creation — user knows the tag
peak = PeakFactory.create('thompson-cox-hastings')

# Context-dependent default — during experiment construction
peak = PeakFactory.create_default_for(
    scattering_type=ScatteringTypeEnum.BRAGG,
    beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
)
# → resolves to 'tof-pseudo-voigt-ikeda-carpenter' → creates TofPseudoVoigtIkedaCarpenter

# Calculator with context-dependent default
calc = CalculatorFactory.create_default_for(
    scattering_type=ScatteringTypeEnum.TOTAL,
)
# → resolves to 'pdffit' → creates PdffitCalculator

# Simple default — no context
bg = BackgroundFactory.create()
# → uses _default_tag = 'line-segment' → creates LineSegmentBackground
```

---

## 6. Tag Naming Convention

### 6.1 Principles

Tags are the user-facing identifiers for selecting types. They must be:

- **Consistent** — use the same abbreviations everywhere.
- **Hyphen-separated** — all lowercase, words joined by hyphens.
- **Semantically ordered** — from general to specific.
- **Unique within a factory** — but may overlap across factories.

### 6.2 Standard Abbreviations

| Concept             | Abbreviation | Never use                   |
| ------------------- | ------------ | --------------------------- |
| Powder              | `pd`         | `powder`                    |
| Single crystal      | `sc`         | `single-crystal`            |
| Constant wavelength | `cwl`        | `cw`, `constant-wavelength` |
| Time-of-flight      | `tof`        | `time-of-flight`            |
| Bragg (scattering)  | `bragg`      |                             |
| Total (scattering)  | `total`      |                             |

### 6.3 Complete Tag Registry

#### Background tags

| Tag            | Class                           |
| -------------- | ------------------------------- |
| `line-segment` | `LineSegmentBackground`         |
| `chebyshev`    | `ChebyshevPolynomialBackground` |

#### Peak tags

| Tag                                | Class                          |
| ---------------------------------- | ------------------------------ |
| `pseudo-voigt`                     | `CwlPseudoVoigt`               |
| `split-pseudo-voigt`               | `CwlSplitPseudoVoigt`          |
| `thompson-cox-hastings`            | `CwlThompsonCoxHastings`       |
| `tof-pseudo-voigt`                 | `TofPseudoVoigt`               |
| `tof-pseudo-voigt-ikeda-carpenter` | `TofPseudoVoigtIkedaCarpenter` |
| `tof-pseudo-voigt-back-to-back`    | `TofPseudoVoigtBackToBack`     |
| `gaussian-damped-sinc`             | `TotalGaussianDampedSinc`      |

#### Instrument tags

| Tag      | Class             |
| -------- | ----------------- |
| `cwl-pd` | `CwlPdInstrument` |
| `cwl-sc` | `CwlScInstrument` |
| `tof-pd` | `TofPdInstrument` |
| `tof-sc` | `TofScInstrument` |

#### Data tags

| Tag            | Class       |
| -------------- | ----------- |
| `bragg-pd-cwl` | `PdCwlData` |
| `bragg-pd-tof` | `PdTofData` |
| `bragg-sc`     | `ReflnData` |
| `total-pd`     | `TotalData` |

#### Experiment tags

| Tag            | Class               |
| -------------- | ------------------- |
| `bragg-pd`     | `BraggPdExperiment` |
| `total-pd`     | `TotalPdExperiment` |
| `bragg-sc-cwl` | `CwlScExperiment`   |
| `bragg-sc-tof` | `TofScExperiment`   |

#### Calculator tags

| Tag       | Class               |
| --------- | ------------------- |
| `cryspy`  | `CryspyCalculator`  |
| `crysfml` | `CrysfmlCalculator` |
| `pdffit`  | `PdffitCalculator`  |

#### Minimizer tags

| Tag                   | Class                                     |
| --------------------- | ----------------------------------------- |
| `lmfit`               | `LmfitMinimizer`                          |
| `lmfit-leastsq`       | `LmfitMinimizer` (method=`leastsq`)       |
| `lmfit-least-squares` | `LmfitMinimizer` (method=`least_squares`) |
| `dfols`               | `DfolsMinimizer`                          |

---

## 7. Where Metadata Goes: CategoryItem vs. CategoryCollection

### 7.1 The Rule

> **If a concrete class is created by a factory, it gets `type_info`,
> `compatibility`, and `calculator_support`.**
>
> **If a `CategoryItem` only exists as a child row inside a
> `CategoryCollection`, it does NOT get these attributes — the collection
> does.**

### 7.2 Rationale

A `LineSegment` item (a single background control point) is never selected,
created, or queried by a factory. It is always instantiated internally by its
parent `LineSegmentBackground` collection. The meaningful unit of selection is
the _collection_, not the item. The user picks "line-segment background" (the
collection type), not individual line-segment points.

Similarly, `AtomSite` is a child of `AtomSites`, `PdCwlDataPoint` is a child of
`PdCwlData`, and `PolynomialTerm` is a child of `ChebyshevPolynomialBackground`.
None of these items are factory-created or user-selected.

Conversely, `Cell`, `SpaceGroup`, `Extinction`, and `InstrumentBase` subclasses
are `CategoryItem` subclasses used as singletons — they exist directly on a
parent (Structure or Experiment), and some of them _are_ factory-created
(instruments, peaks). These get the metadata.

### 7.3 Classification of All Current Classes

#### Singleton CategoryItems — factory-created (get all three)

| Class                          | Factory             | Metadata needed                                      |
| ------------------------------ | ------------------- | ---------------------------------------------------- |
| `CwlPdInstrument`              | `InstrumentFactory` | `type_info` + `compatibility` + `calculator_support` |
| `CwlScInstrument`              | `InstrumentFactory` | (same)                                               |
| `TofPdInstrument`              | `InstrumentFactory` | (same)                                               |
| `TofScInstrument`              | `InstrumentFactory` | (same)                                               |
| `CwlPseudoVoigt`               | `PeakFactory`       | (same)                                               |
| `CwlSplitPseudoVoigt`          | `PeakFactory`       | (same)                                               |
| `CwlThompsonCoxHastings`       | `PeakFactory`       | (same)                                               |
| `TofPseudoVoigt`               | `PeakFactory`       | (same)                                               |
| `TofPseudoVoigtIkedaCarpenter` | `PeakFactory`       | (same)                                               |
| `TofPseudoVoigtBackToBack`     | `PeakFactory`       | (same)                                               |
| `TotalGaussianDampedSinc`      | `PeakFactory`       | (same)                                               |

#### Singleton CategoryItems — NOT factory-created (get `type_info` only, optionally `compatibility` and `calculator_support` if useful)

| Class            | Notes                                                                                                                                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cell`           | Always present on every Structure. No factory selection. Could get `type_info` for self-description, but `compatibility` and `calculator_support` are not needed because there is no selection to filter. |
| `SpaceGroup`     | Same as Cell.                                                                                                                                                                                             |
| `ExperimentType` | Same. Intrinsically universal.                                                                                                                                                                            |
| `Extinction`     | Only used in single-crystal experiments. Could benefit from `compatibility` to declare this formally.                                                                                                     |
| `LinkedCrystal`  | Only single-crystal. Same reasoning.                                                                                                                                                                      |

For these non-factory-created singletons, adding `compatibility` is _optional
but useful_ for documentation and validation (e.g., to flag if `Extinction` is
mistakenly attached to a powder experiment). This is a future enhancement and
not required for the initial implementation.

#### CategoryCollections — factory-created (get all three)

| Class                           | Factory             | Metadata needed                                      |
| ------------------------------- | ------------------- | ---------------------------------------------------- |
| `LineSegmentBackground`         | `BackgroundFactory` | `type_info` + `compatibility` + `calculator_support` |
| `ChebyshevPolynomialBackground` | `BackgroundFactory` | (same)                                               |
| `PdCwlData`                     | `DataFactory`       | (same)                                               |
| `PdTofData`                     | `DataFactory`       | (same)                                               |
| `TotalData`                     | `DataFactory`       | (same)                                               |
| `ReflnData`                     | `DataFactory`       | (same)                                               |

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

These are internal row-level items. They have no factory, no user selection, no
experimental-condition filtering. They get nothing.

#### Non-category classes — factory-created (get `type_info` only)

| Class               | Factory             | Notes                                                                                                                                                                                                                |
| ------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CryspyCalculator`  | `CalculatorFactory` | `type_info` only. No `compatibility` or `calculator_support` — calculators don't have experimental restrictions in this sense (their limitations are expressed on the _categories they support_, not on themselves). |
| `CrysfmlCalculator` | `CalculatorFactory` | (same)                                                                                                                                                                                                               |
| `PdffitCalculator`  | `CalculatorFactory` | (same)                                                                                                                                                                                                               |
| `LmfitMinimizer`    | `MinimizerFactory`  | `type_info` only.                                                                                                                                                                                                    |
| `DfolsMinimizer`    | `MinimizerFactory`  | (same)                                                                                                                                                                                                               |
| `BraggPdExperiment` | `ExperimentFactory` | `type_info` + `compatibility`. No `calculator_support` — the experiment's compatibility is checked against its _categories'_ calculator support, not its own.                                                        |
| `TotalPdExperiment` | `ExperimentFactory` | (same)                                                                                                                                                                                                               |
| `CwlScExperiment`   | `ExperimentFactory` | (same)                                                                                                                                                                                                               |
| `TofScExperiment`   | `ExperimentFactory` | (same)                                                                                                                                                                                                               |

---

## 8. Complete Examples

### 8.1 Background

#### Before (3 files, ~95 lines for the factory + enum alone)

```
background/enums.py          — BackgroundTypeEnum with values + description() + default()
background/factory.py         — BackgroundFactory with _supported_map(), create(), validation
background/line_segment.py    — LineSegmentBackground._description = '...'
background/chebyshev.py       — ChebyshevPolynomialBackground._description = '...'
```

#### After

**`background/enums.py`** — deleted entirely.

**`background/factory.py`** — reduced to:

```python
from easydiffraction.core.factory import FactoryBase


class BackgroundFactory(FactoryBase):
    _default_tag = 'line-segment'
    # No _default_rules needed — background choice doesn't depend on
    # experimental context.
```

**`background/line_segment.py`**:

```python
from easydiffraction.core.metadata import Compatibility, CalculatorSupport, TypeInfo
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.background.base import BackgroundBase
from easydiffraction.datablocks.experiment.item.enums import (
    BeamModeEnum,
    CalculatorEnum,
)


@BackgroundFactory.register
class LineSegmentBackground(BackgroundBase):
    type_info = TypeInfo(
        tag='line-segment',
        description='Linear interpolation between points',
    )
    compatibility = Compatibility(
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self):
        super().__init__(item_type=LineSegment)

    # ...rest unchanged...
```

**`background/chebyshev.py`**:

```python
@BackgroundFactory.register
class ChebyshevPolynomialBackground(BackgroundBase):
    type_info = TypeInfo(
        tag='chebyshev',
        description='Chebyshev polynomial background',
    )
    compatibility = Compatibility(
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self):
        super().__init__(item_type=PolynomialTerm)

    # ...rest unchanged...
```

**Note:** `LineSegment` and `PolynomialTerm` (the child `CategoryItem` classes)
are unchanged — they get no metadata.

### 8.2 Peak Profiles

**`peak/factory.py`**:

```python
from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import (
    BeamModeEnum,
    ScatteringTypeEnum,
)


class PeakFactory(FactoryBase):
    _default_tag = 'pseudo-voigt'
    _default_rules = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'pseudo-voigt',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'tof-pseudo-voigt-ikeda-carpenter',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): 'gaussian-damped-sinc',
    }
```

**`peak/cwl.py`**:

```python
from easydiffraction.core.metadata import Compatibility, CalculatorSupport, TypeInfo
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory


@PeakFactory.register
class CwlPseudoVoigt(PeakBase, CwlBroadeningMixin):
    type_info = TypeInfo(tag='pseudo-voigt', description='Pseudo-Voigt profile')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class CwlSplitPseudoVoigt(PeakBase, CwlBroadeningMixin, EmpiricalAsymmetryMixin):
    type_info = TypeInfo(
        tag='split-pseudo-voigt',
        description='Split pseudo-Voigt with empirical asymmetry correction',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class CwlThompsonCoxHastings(PeakBase, CwlBroadeningMixin, FcjAsymmetryMixin):
    type_info = TypeInfo(
        tag='thompson-cox-hastings',
        description='Thompson–Cox–Hastings with FCJ asymmetry correction',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()
```

**`peak/tof.py`**:

```python
@PeakFactory.register
class TofPseudoVoigt(PeakBase, TofBroadeningMixin):
    type_info = TypeInfo(tag='tof-pseudo-voigt', description='TOF pseudo-Voigt profile')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class TofPseudoVoigtIkedaCarpenter(PeakBase, TofBroadeningMixin, IkedaCarpenterAsymmetryMixin):
    type_info = TypeInfo(
        tag='tof-pseudo-voigt-ikeda-carpenter',
        description='Pseudo-Voigt with Ikeda–Carpenter asymmetry correction',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class TofPseudoVoigtBackToBack(PeakBase, TofBroadeningMixin, IkedaCarpenterAsymmetryMixin):
    type_info = TypeInfo(
        tag='tof-pseudo-voigt-back-to-back',
        description='TOF back-to-back pseudo-Voigt with asymmetry',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()
```

**`peak/total.py`**:

```python
@PeakFactory.register
class TotalGaussianDampedSinc(PeakBase, TotalBroadeningMixin):
    type_info = TypeInfo(
        tag='gaussian-damped-sinc',
        description='Gaussian-damped sinc for pair distribution function analysis',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.PDFFIT}),
    )

    def __init__(self) -> None:
        super().__init__()
```

### 8.3 Instruments

**`instrument/factory.py`**:

```python
from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import (
    BeamModeEnum,
    SampleFormEnum,
)


class InstrumentFactory(FactoryBase):
    _default_tag = 'cwl-pd'
    _default_rules = {
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'cwl-pd',
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'cwl-sc',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'tof-pd',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'tof-sc',
    }
```

**`instrument/cwl.py`**:

```python
@InstrumentFactory.register
class CwlPdInstrument(CwlInstrumentBase):
    type_info = TypeInfo(tag='cwl-pd', description='CW powder diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG, ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({
            CalculatorEnum.CRYSPY,
            CalculatorEnum.CRYSFML,
            CalculatorEnum.PDFFIT,
        }),
    )

    def __init__(self) -> None:
        super().__init__()

    # ...existing parameter definitions unchanged...


@InstrumentFactory.register
class CwlScInstrument(CwlInstrumentBase):
    type_info = TypeInfo(tag='cwl-sc', description='CW single-crystal diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()
```

**`instrument/tof.py`**:

```python
@InstrumentFactory.register
class TofPdInstrument(InstrumentBase):
    type_info = TypeInfo(tag='tof-pd', description='TOF powder diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()

    # ...existing parameter definitions unchanged...


@InstrumentFactory.register
class TofScInstrument(InstrumentBase):
    type_info = TypeInfo(tag='tof-sc', description='TOF single-crystal diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()
```

### 8.4 Data Collections

**`data/factory.py`**:

```python
from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import (
    BeamModeEnum,
    SampleFormEnum,
    ScatteringTypeEnum,
)


class DataFactory(FactoryBase):
    _default_tag = 'bragg-pd-cwl'
    _default_rules = {
        frozenset({
            ('sample_form', SampleFormEnum.POWDER),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'bragg-pd-cwl',
        frozenset({
            ('sample_form', SampleFormEnum.POWDER),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'bragg-pd-tof',
        frozenset({
            ('sample_form', SampleFormEnum.POWDER),
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): 'total-pd',
        frozenset({
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
        }): 'bragg-sc',
    }
```

**`data/bragg_pd.py`** (collection classes only — data point items are
unchanged):

```python
@DataFactory.register
class PdCwlData(PdDataBase):
    type_info = TypeInfo(tag='bragg-pd-cwl', description='Bragg powder CWL data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self):
        super().__init__(item_type=PdCwlDataPoint)

    # ...rest unchanged...


@DataFactory.register
class PdTofData(PdDataBase):
    type_info = TypeInfo(tag='bragg-pd-tof', description='Bragg powder TOF data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self):
        super().__init__(item_type=PdTofDataPoint)

    # ...rest unchanged...
```

**`data/bragg_sc.py`**:

```python
@DataFactory.register
class ReflnData(CategoryCollection):
    type_info = TypeInfo(tag='bragg-sc', description='Bragg single-crystal reflection data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self):
        super().__init__(item_type=Refln)

    # ...rest unchanged...
```

**`data/total_pd.py`**:

```python
@DataFactory.register
class TotalData(TotalDataBase):
    type_info = TypeInfo(tag='total-pd', description='Total scattering (PDF) data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.PDFFIT}),
    )

    def __init__(self):
        super().__init__(item_type=TotalDataPoint)

    # ...rest unchanged...
```

### 8.5 Calculators

Calculators get `type_info` only. They don't need `compatibility` (they don't
have experimental restrictions on _themselves_) or `calculator_support` (they
_are_ calculators). Their limitations are expressed on the categories they
support — inverted.

**`calculators/factory.py`**:

```python
from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


class CalculatorFactory(FactoryBase):
    _default_tag = 'cryspy'
    _default_rules = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
        }): 'cryspy',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): 'pdffit',
    }

    @classmethod
    def _supported_map(cls):
        """Only include calculators whose engines are importable."""
        return {klass.type_info.tag: klass for klass in cls._registry if klass().engine_imported}
```

**`calculators/cryspy.py`**:

```python
@CalculatorFactory.register
class CryspyCalculator(CalculatorBase):
    type_info = TypeInfo(
        tag='cryspy',
        description='CrysPy library for crystallographic calculations',
    )
    engine_imported: bool = cryspy is not None
    # ...rest unchanged...
```

**`calculators/crysfml.py`**:

```python
@CalculatorFactory.register
class CrysfmlCalculator(CalculatorBase):
    type_info = TypeInfo(
        tag='crysfml',
        description='CrysFML library for crystallographic calculations',
    )
    engine_imported: bool = cfml_py_utilities is not None
    # ...rest unchanged...
```

**`calculators/pdffit.py`**:

```python
@CalculatorFactory.register
class PdffitCalculator(CalculatorBase):
    type_info = TypeInfo(
        tag='pdffit',
        description='PDFfit2 for pair distribution function calculations',
    )
    engine_imported: bool = PdfFit is not None
    # ...rest unchanged...
```

**Note on `engine_imported`:** `CalculatorFactory` is the only factory that
overrides `_supported_map()` to filter out calculators where
`engine_imported is False`. All other factories inherit the default
implementation from `FactoryBase`.

### 8.6 Experiment Types

**`experiment/item/factory.py`**:

```python
from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import (
    BeamModeEnum,
    SampleFormEnum,
    ScatteringTypeEnum,
)


class ExperimentFactory(FactoryBase):
    _default_tag = 'bragg-pd'
    _default_rules = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'bragg-pd',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'total-pd',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'bragg-sc-cwl',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'bragg-sc-tof',
    }

    # ...classmethods from_cif_path, from_cif_str, from_scratch,
    # from_data_path remain but internally use FactoryBase machinery...
```

**`experiment/item/bragg_pd.py`**:

```python
@ExperimentFactory.register
class BraggPdExperiment(PdExperimentBase):
    type_info = TypeInfo(
        tag='bragg-pd',
        description='Bragg powder diffraction experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    # No calculator_support — validated through categories
```

**`experiment/item/total_pd.py`**:

```python
@ExperimentFactory.register
class TotalPdExperiment(PdExperimentBase):
    type_info = TypeInfo(
        tag='total-pd',
        description='Total scattering (PDF) powder experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
```

**`experiment/item/bragg_sc.py`**:

```python
@ExperimentFactory.register
class CwlScExperiment(ScExperimentBase):
    type_info = TypeInfo(
        tag='bragg-sc-cwl',
        description='Bragg CWL single-crystal experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )


@ExperimentFactory.register
class TofScExperiment(ScExperimentBase):
    type_info = TypeInfo(
        tag='bragg-sc-tof',
        description='Bragg TOF single-crystal experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
```

### 8.7 Minimizers

```python
class MinimizerFactory(FactoryBase):
    _default_tag = 'lmfit'
    # No _default_rules — minimizer choice doesn't depend on
    # experimental context.
```

```python
@MinimizerFactory.register
class LmfitMinimizer(MinimizerBase):
    type_info = TypeInfo(
        tag='lmfit',
        description='LMFIT with Levenberg-Marquardt least squares',
    )


@MinimizerFactory.register
class DfolsMinimizer(MinimizerBase):
    type_info = TypeInfo(
        tag='dfols',
        description='DFO-LS derivative-free least-squares optimization',
    )
```

**Note on minimizer methods:** The current `MinimizerFactory` supports multiple
entries for `LmfitMinimizer` with different methods (e.g. `'lmfit (leastsq)'`,
`'lmfit (least_squares)'`). In the new design, these become separate
registrations with distinct tags:

```python
@MinimizerFactory.register
class LmfitLeastsqMinimizer(LmfitMinimizer):
    type_info = TypeInfo(
        tag='lmfit-leastsq',
        description='LMFIT with Levenberg-Marquardt least squares',
    )
    _method = 'leastsq'


@MinimizerFactory.register
class LmfitLeastSquaresMinimizer(LmfitMinimizer):
    type_info = TypeInfo(
        tag='lmfit-least-squares',
        description="LMFIT with SciPy's trust region reflective algorithm",
    )
    _method = 'least_squares'
```

Alternatively, if subclassing feels heavy, `MinimizerFactory` can override
`create()` to handle method dispatch. This is an implementation detail to
resolve during migration step 9.

---

## 9. How Factories Are Used (Consumer Side)

### 9.1 Creating an Object by Tag

```python
bg = BackgroundFactory.create('chebyshev')
peak = PeakFactory.create('pseudo-voigt')
calc = CalculatorFactory.create('cryspy')
```

### 9.2 Creating with Default (No Context)

```python
bg = BackgroundFactory.create()  # uses _default_tag = 'line-segment'
```

### 9.3 Creating with Context-Dependent Default

```python
# During experiment construction — the correct peak profile is chosen
# based on the experiment's scattering type and beam mode:
peak = PeakFactory.create_default_for(
    scattering_type=ScatteringTypeEnum.BRAGG,
    beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
)
# → resolves to 'tof-pseudo-voigt-ikeda-carpenter'
# → creates TofPseudoVoigtIkedaCarpenter

# The correct calculator is chosen based on scattering type:
calc = CalculatorFactory.create_default_for(
    scattering_type=ScatteringTypeEnum.TOTAL,
)
# → resolves to 'pdffit' → creates PdffitCalculator
```

### 9.4 Querying the Default Tag

```python
# What would the default peak be for this context?
tag = PeakFactory.default_tag(
    scattering_type=ScatteringTypeEnum.TOTAL,
    beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
)
# → 'gaussian-damped-sinc'
```

### 9.5 Context-Filtered Discovery

```python
# "What peak profiles work for Bragg CW experiments with cryspy?"
profiles = PeakFactory.supported_for(
    scattering_type=ScatteringTypeEnum.BRAGG,
    beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    calculator=CalculatorEnum.CRYSPY,
)
# → [CwlPseudoVoigt, CwlSplitPseudoVoigt, CwlThompsonCoxHastings]
```

### 9.6 Display

```python
PeakFactory.show_supported(
    scattering_type=ScatteringTypeEnum.BRAGG,
    beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
)
# Prints:
#   Type                             Description
#   pseudo-voigt                     Pseudo-Voigt profile
#   split-pseudo-voigt               Split pseudo-Voigt with empirical asymmetry ...
#   thompson-cox-hastings            Thompson–Cox–Hastings with FCJ asymmetry ...
```

### 9.7 Experiment's Convenience Methods

The existing per-experiment convenience methods become thin wrappers:

```python
# In PdExperimentBase or BraggPdExperiment:
def show_supported_peak_profile_types(self):
    PeakFactory.show_supported(
        scattering_type=self.type.scattering_type.value,
        beam_mode=self.type.beam_mode.value,
    )


def show_supported_background_types(self):
    BackgroundFactory.show_supported()
```

### 9.8 How Experiments Use `create_default_for`

Inside `PdExperimentBase.__init__`, the current code:

```python
# Before
self._peak_profile_type = PeakProfileTypeEnum.default(
    self.type.scattering_type.value,
    self.type.beam_mode.value,
)
self._peak = PeakFactory.create(
    scattering_type=self.type.scattering_type.value,
    beam_mode=self.type.beam_mode.value,
    profile_type=self._peak_profile_type,
)
```

Becomes:

```python
# After
self._peak = PeakFactory.create_default_for(
    scattering_type=self.type.scattering_type.value,
    beam_mode=self.type.beam_mode.value,
)
```

Similarly, `BraggPdExperiment.__init__`:

```python
# Before
self._instrument = InstrumentFactory.create(
    scattering_type=self.type.scattering_type.value,
    beam_mode=self.type.beam_mode.value,
    sample_form=self.type.sample_form.value,
)

# After
self._instrument = InstrumentFactory.create_default_for(
    scattering_type=self.type.scattering_type.value,
    beam_mode=self.type.beam_mode.value,
    sample_form=self.type.sample_form.value,
)
```

---

## 10. What Gets Deleted

| File / code                                         | Reason                                                    |
| --------------------------------------------------- | --------------------------------------------------------- |
| `background/enums.py` (`BackgroundTypeEnum`)        | Replaced by `type_info.tag` on each class                 |
| `PeakProfileTypeEnum` in `experiment/item/enums.py` | Replaced by `type_info.tag` on each class                 |
| `BackgroundFactory._supported_map()` body           | Inherited from `FactoryBase`                              |
| `PeakFactory._supported` / `_supported_map()` body  | Inherited from `FactoryBase`                              |
| `InstrumentFactory._supported_map()` body           | Inherited from `FactoryBase`                              |
| `DataFactory._supported` dict                       | Inherited from `FactoryBase`                              |
| `CalculatorFactory._potential_calculators` dict     | Replaced by `@register` + `type_info`                     |
| `CalculatorFactory.list_supported_calculators()`    | Inherited as `supported_tags()`                           |
| `CalculatorFactory.show_supported_calculators()`    | Inherited as `show_supported()`                           |
| `MinimizerFactory._available_minimizers` dict       | Replaced by `@register` + `type_info`                     |
| `MinimizerFactory.list_available_minimizers()`      | Inherited as `supported_tags()`                           |
| `MinimizerFactory.show_available_minimizers()`      | Inherited as `show_supported()`                           |
| All per-factory validation boilerplate              | Inherited from `FactoryBase.create()`                     |
| `_description` class attributes on backgrounds      | Replaced by `type_info.description`                       |
| Enum `description()` methods on deleted enums       | Replaced by `type_info.description`                       |
| Enum `default()` methods on deleted enums           | Replaced by `_default_rules` + `default_tag()` on factory |

---

## 11. What Gets Added

| File                                           | Contents                                                                                                              |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `core/metadata.py`                             | `TypeInfo`, `Compatibility`, `CalculatorSupport` dataclasses                                                          |
| `core/factory.py`                              | `FactoryBase` class with `register`, `create`, `create_default_for`, `default_tag`, `supported_for`, `show_supported` |
| `CalculatorEnum` in `experiment/item/enums.py` | New enum for calculator identifiers                                                                                   |

---

## 12. What Remains Unchanged

- `Identity` class in `core/identity.py` — separate concern (CIF hierarchy).
- `CategoryItem` and `CategoryCollection` base classes — no structural changes.
  The three metadata attributes are added on concrete subclasses, not on the
  base classes.
- `ExperimentType` category — still holds runtime enum values for the current
  experiment's configuration.
- `SampleFormEnum`, `ScatteringTypeEnum`, `BeamModeEnum`, `RadiationProbeEnum` —
  kept as-is (they represent the experiment axes). Their `.default()` and
  `.description()` methods remain.
- Child `CategoryItem` classes (`LineSegment`, `PolynomialTerm`, `AtomSite`,
  data point items, etc.) — no changes.
- All computation logic, CIF serialization, `_update()` methods, parameter
  definitions — no changes.

---

## 13. Migration Order

Implementation should proceed in this order:

1. **Create `core/metadata.py`** with `TypeInfo`, `Compatibility`,
   `CalculatorSupport`.
2. **Create `core/factory.py`** with `FactoryBase`.
3. **Add `CalculatorEnum`** to `experiment/item/enums.py`.
4. **Migrate `BackgroundFactory`** — simplest case (flat, 2 classes, no
   `_default_rules`). Delete `background/enums.py`. Update `line_segment.py` and
   `chebyshev.py`. Update all references to `BackgroundTypeEnum`.
5. **Migrate `PeakFactory`** — 7 classes, has `_default_rules`. Remove
   `PeakProfileTypeEnum` from `experiment/item/enums.py`. Update `cwl.py`,
   `tof.py`, `total.py`.
6. **Migrate `InstrumentFactory`** — 4 classes, has `_default_rules`. Update
   `cwl.py`, `tof.py`.
7. **Migrate `DataFactory`** — 4 collection classes, has `_default_rules`.
   Update `bragg_pd.py`, `bragg_sc.py`, `total_pd.py`.
8. **Migrate `CalculatorFactory`** — 3 classes, has `_default_rules`, overrides
   `_supported_map()`. Update `cryspy.py`, `crysfml.py`, `pdffit.py`.
9. **Migrate `MinimizerFactory`** — 2+ classes. Resolve the multi-method
   `LmfitMinimizer` pattern (subclass or factory override). Update `lmfit.py`,
   `dfols.py`.
10. **Migrate `ExperimentFactory`** — 4 experiment classes, has
    `_default_rules`. Note: `ExperimentFactory` has additional classmethods
    (`from_cif_path`, `from_cif_str`, `from_scratch`, `from_data_path`) that
    stay but internally use `FactoryBase` machinery. The `_resolve_class()`
    method is replaced by `create_default_for()` or `supported_for()`.
11. **Update consumer code** — `show_supported_*()` methods on experiment
    classes become thin wrappers around `Factory.show_supported(...)`. Replace
    `PeakProfileTypeEnum.default(st, bm)` calls with
    `PeakFactory.default_tag(scattering_type=st, beam_mode=bm)`. Replace
    `BackgroundTypeEnum.default()` with `BackgroundFactory.create()`. Replace
    `InstrumentFactory.create( scattering_type=..., beam_mode=..., sample_form=...)`
    with `InstrumentFactory.create_default_for(...)`.
12. **Update tests** — adjust imports, remove enum-based tests, add
    metadata-based tests. Test `default_tag()` with various condition
    combinations. Test `create_default_for()`. Test `supported_for()` filtering.

---

## 14. Design Principles Summary

1. **Single source of truth.** Each concrete class declares its own tag,
   description, compatibility, and calculator support. No duplication in enums
   or factory dicts.
2. **Separation of concerns.** `TypeInfo` (identity), `Compatibility`
   (experimental conditions), `CalculatorSupport` (engine support), and
   `Identity` (CIF hierarchy) are four distinct, non-overlapping objects.
3. **Uniform axes.** `Compatibility` has four parallel frozenset fields matching
   `ExperimentType`'s four axes. No special cases.
4. **Context-dependent defaults.** `_default_rules` on each factory maps
   experimental conditions to default tags. `default_tag()` and
   `create_default_for()` resolve the right default for any context. Falls back
   to `_default_tag` when no context is given.
5. **Consistent naming.** Tags use standard abbreviations (`pd`, `sc`, `cwl`,
   `tof`, `bragg`, `total`), are hyphen-separated, lowercase, and ordered from
   general to specific.
6. **Metadata on the right level.** Factory-created classes get metadata.
   Child-only `CategoryItem` classes don't. Collections that are the unit of
   selection get it; their row items don't.
7. **DRY factories.** `FactoryBase` provides registration, lookup, creation,
   context-dependent defaults, listing, and display. Concrete factories are
   typically 2–15 lines.
8. **Open for extension, closed for modification.** Adding a new variant = one
   new class with `@Factory.register` + three metadata attributes + optionally a
   new `_default_rules` entry. No other files need editing.
9. **Type safety.** `CalculatorEnum` replaces bare strings. Experimental-axis
   enums are reused from the existing codebase.
