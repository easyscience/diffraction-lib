# EasyDiffraction — Open Issues

Prioritised list of issues, improvements, and design questions to
address. Items are ordered by a combination of user impact, blocking
potential, and implementation readiness. When an item is fully
implemented, remove it from this file and update `architecture.md` if
needed.

**Legend:** 🔴 High · 🟡 Medium · 🟢 Low

---

## 3. 🟡 Rebuild Joint-Fit Weights on Every Fit

**Type:** Fragility

`joint_fit_experiments` is created once when `fit_mode` becomes
`'joint'`. If experiments are added, removed, or renamed afterwards, the
weight collection is stale. Joint fitting can fail with missing keys or
run with incorrect weights.

**Fix:** rebuild or validate `joint_fit_experiments` at the start of
every joint fit. At minimum, `fit()` should assert that the weight keys
exactly match `project.experiments.names`.

**Depends on:** nothing.

---

## 5. 🟡 Make `Analysis` a `DatablockItem`

**Type:** Consistency

`Analysis` owns categories (`Aliases`, `Constraints`,
`JointFitExperiments`) but does not extend `DatablockItem`. Its ad-hoc
`_update_categories()` iterates over a hard-coded list and does not
participate in standard category discovery, parameter enumeration, or
CIF serialisation.

**Fix:** make `Analysis` extend `DatablockItem`, or extract a shared
`_update_categories()` protocol.

**Depends on:** nothing.

---

## 8. 🟡 Add Explicit `create()` Signatures on Collections

**Type:** API safety

`CategoryCollection.create(**kwargs)` accepts arbitrary keyword
arguments and applies them via `setattr`. Typos are silently dropped
(GuardedBase logs a warning but does not raise), so items are created
with incorrect defaults.

**Fix:** concrete collection subclasses (e.g. `AtomSites`, `Background`)
should override `create()` with explicit parameters for IDE autocomplete
and typo detection. The base `create(**kwargs)` remains as an internal
implementation detail.

**Depends on:** nothing.

---

## 9. 🟢 Add Future Enum Extensions

**Type:** Design improvement

The four current experiment axes will be extended with at least two
more:

| New axis            | Options                | Enum (proposed)          |
| ------------------- | ---------------------- | ------------------------ |
| Data dimensionality | 1D, 2D                 | `DataDimensionalityEnum` |
| Beam polarisation   | unpolarised, polarised | `PolarisationEnum`       |

These should follow the same `str, Enum` pattern and integrate into
`Compatibility` (new `FrozenSet` fields), `_default_rules`, and
`ExperimentType` (new `StringDescriptor`s with `MembershipValidator`s).

**Migration path:** existing `Compatibility` objects that don't specify
the new fields use `frozenset()` (empty = "any"), so all existing
classes remain compatible without changes.

**Depends on:** nothing.

---

## 10. 🟢 Unify Project-Level Update Orchestration

**Type:** Maintainability

`Project._update_categories(expt_name)` hard-codes the update order
(structures → analysis → one experiment). The `_update_priority` system
exists on categories but is not used across datablocks. The `expt_name`
parameter means only one experiment is updated per call, inconsistent
with joint-fit workflows.

**Fix:** consider a project-level `_update_priority` on datablocks, or
at minimum document the required update order. For joint fitting, all
experiments should be updateable in a single call.

**Depends on:** benefits from issue 5 (Analysis as DatablockItem).

---

## 11. 🟢 Document Category `_update` Contract

**Type:** Maintainability

`_update()` is an optional override with a no-op default. A clearer
contract would help contributors:

- **Active categories** (those that compute something, e.g.
  `Background`, `Data`) should have an explicit `_update()`
  implementation.
- **Passive categories** (those that only store parameters, e.g. `Cell`,
  `SpaceGroup`) keep the no-op default.

The distinction is already implicit in the code; making it explicit in
documentation (and possibly via a naming convention or flag) would
reduce confusion for new contributors.

**Depends on:** nothing.

---

## 13. 🟢 Suppress Redundant Dirty-Flag Sets in Symmetry Constraints

**Type:** Performance

Symmetry constraint application (cell metric, atomic coordinates, ADPs)
goes through the public `value` setter for each parameter, setting the
dirty flag repeatedly during what is logically a single batch operation.

No correctness issue — the dirty-flag guard handles this correctly. The
redundant sets are a minor inefficiency that only matters if profiling
shows it is a bottleneck.

**Fix:** introduce a private `_set_value_no_notify()` method on
`GenericDescriptorBase` for internal batch operations, or a context
manager / flag on the owning datablock to suppress notifications during
a batch.

**Depends on:** nothing, but low priority.

---

## 14. 🟢 Finer-Grained Parameter Change Tracking

**Type:** Performance

The current dirty-flag approach (`_need_categories_update` on
`DatablockItem`) triggers a full update of all categories when any
parameter changes. This is simple and correct. If performance becomes a
concern with many categories, a more granular approach could track which
specific categories are dirty. Only implement when profiling proves it
is needed.

**Depends on:** nothing, but low priority.

---

## 15. 🟡 Validate Joint-Fit Weights Before Residual Normalisation

**Type:** Correctness

Joint-fit weights currently allow invalid numeric values such as
negatives or an all-zero set. The residual code then normalises by the
total weight and applies `sqrt(weight)`, which can produce
division-by-zero or `nan` residuals.

**Fix:** require weights to be strictly positive, or at minimum validate
that all weights are non-negative and their total is greater than zero
before normalisation. This should fail with a clear user-facing error
instead of letting invalid floating-point values propagate into the
minimiser.

**Depends on:** related to issue 3, but independent.

---

## 17. 🟢 Use PDF-Specific CIF Names for Total Scattering

**Type:** Naming

The `TotalPdDataPoint` class reuses Bragg powder CIF tag names (e.g.
`_pd_data.point_id`, `_pd_proc.r`, `_pd_meas.intensity_total`) as
placeholders. These should be replaced with proper total-scattering /
PDF-specific CIF names.

**TODOs:**

- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L48)
  — `_pd_data.point_id`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L62)
  — `_pd_proc.r`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L74)
  — `_pd_meas.intensity_total`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L87)
  — `_pd_meas.intensity_total_su`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L99)
  — `_pd_calc.intensity_total`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L112)
  — `_pd_data.refinement_status`

**Depends on:** nothing.

---

## 18. 🟢 Move CIF v2→v1 Conversion Out of Calculator

**Type:** Maintainability

`PdffitCalculator.calculate_pattern` contains inline CIF v2→v1
conversion (dot-to-underscore rewriting). This should live in a shared
`io` module.

**TODOs:**

- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L118)

**Depends on:** nothing.

---

## 19. 🟢 Add Debug-Mode Logging for Calculator Imports

**Type:** Diagnostics

Several calculator modules have commented-out print statements for
import success/failure. These should be wired into the logging system
under a debug level.

**TODOs:**

- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L34)
- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L37)
- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L19)
- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L23)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L25)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L28)

**Depends on:** nothing.

---

## 20. 🟢 Redirect or Suppress CrysPy stderr Warnings

**Type:** UX

CrysPy emits warnings to stderr during pattern calculation. The code has
TODO markers to redirect these.

**TODOs:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L112)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L184)

**Depends on:** nothing.

---

## 21. 🟡 Clarify CrysPy TOF Background CIF Tag Names

**Type:** Correctness / Naming

The CrysPy calculator uses TOF background CIF tags
(`_tof_backgroundpoint_time`, `_tof_backgroundpoint_intensity`) and
hardcoded `0.0` intensity values marked with `TODO: !!!!????`. The
mapping and the hardcoded defaults need verification.

**TODOs:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L734)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L735)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L738)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L739)

**Depends on:** nothing.

---

## 22. 🟢 Check CrysPy Single-Crystal Instrument Mapping

**Type:** Correctness

`_cif_instrument_section` uses an empty `instrument_mapping` dict for
single crystal and a `TODO: Check this mapping!` marker.

**TODOs:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L506)

**Depends on:** nothing.

---

## 23. 🟢 Investigate PyCrysFML Pattern Length Discrepancy

**Type:** Correctness

CrysFML calculator adjusts pattern length post-calculation with a TODO
asking to investigate the origin of the off-by-one discrepancy. The same
epsilon workaround appears in the dict builder.

**TODOs:**

- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L124)
- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L253)

**Depends on:** nothing.

---

## 24. 🟢 Process Default Values on Experiment Creation

**Type:** Design

Default instrument/peak values for the CrysFML dict are filled in at
calculation time with inline fallbacks rather than being set at
experiment creation.

**TODOs:**

- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L233)

**Depends on:** nothing.

---

## 25. 🟡 Refactor Data `_update` Methods (Split and Unify)

**Type:** Maintainability

Multiple `_update` helpers in Bragg PD, Bragg SC, and Total PD data
classes have `TODO: split into multiple methods` or
`TODO: refactor _get_valid_linked_phases` markers. The update logic
should be decomposed and the `_get_valid_linked_phases` responsibility
should be narrowed. The Total PD and Bragg PD classes should also adapt
the pattern from `bragg_sc.py`.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L386)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L389)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L506)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L585)
- [bragg_sc.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py#L271)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L254)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L257)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L349)

**Depends on:** nothing.

---

## 26. 🟢 Clarify `dtype` Usage in Data Point Arrays

**Type:** Cleanup

Many array constructions pass `dtype=float` or `dtype=object` with a
`TODO: needed? DataTypes.NUMERIC?` comment. Decide whether explicit
dtype is needed and align with `DataTypes`.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L415)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L423)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L431)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L456)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L466)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L474)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L543)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L556)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L624)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L637)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L370)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L378)

**Depends on:** nothing.

---

## 27. 🟢 Handle Zero Uncertainty in Bragg PD Data

**Type:** Correctness

A temporary workaround exists for zero uncertainties in measured data.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L442)

**Depends on:** nothing.

---

## 28. 🟢 Clarify Bragg PD Data Collection Description

**Type:** Cleanup

`PdCwlDataCollection` has a commented-out `_description` and a
`TODO: ???` marker.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L482)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L304)

**Depends on:** nothing.

---

## 29. 🟡 Standardise CIF ID Validator Pattern Across Categories

**Type:** Consistency

Multiple category item classes use the same regex `r'^[A-Za-z0-9_]*$'`
for their id/label validators with an identical TODO about CIF label vs.
internal label conversion.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L43)
- [bragg_sc.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py#L39)
- [chebyshev.py](src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py#L52)
- [line_segment.py](src/easydiffraction/datablocks/experiment/categories/background/line_segment.py#L45)
- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L39)
- [default.py](src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L45)

**Depends on:** nothing.

---

## 30. 🟢 Make `refinement_status` Default an Enum

**Type:** Design

`bragg_pd.py` uses `default='incl'` as a raw string with a TODO to make
it an Enum. The `_pd_data.refinement_status` CIF name should also be
renamed to `calc_status`.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L113)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L118)

**Depends on:** nothing.

---

## 31. 🟢 Rename PD Data Point Mixins

**Type:** Naming

Mixin classes `PdDataPointBaseMixin` and `PdCwlDataPointMixin` have TODO
markers suggesting a rename to `BasePdDataPointMixin` and
`CwlPdDataPointMixin` for consistency.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L268)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L269)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L271)

**Depends on:** nothing.

---

## 32. 🟡 Move Common Methods to `DatablockCollection` Base Class

**Type:** Maintainability

Both `Experiments` and `Structures` collections duplicate methods
(`from_cif_str`, `from_cif_file`, `show`, `show_as_cif`, etc.) that
could live in the base `DatablockCollection`.

**TODOs:**

- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L29)
  — `Make abstract in DatablockCollection?`
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L65)
  — `Move to DatablockCollection?`
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L82)
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L145)
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L151)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L30)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L48)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L65)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L82)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L88)

**Depends on:** nothing.

---

## 33. 🟡 Make `DatablockItem._update_categories` Abstract

**Type:** Design

`DatablockItem._update_categories` has a TODO to make it abstract and
implement it in subclasses for structures (symmetry + constraints) and
experiments (calculation updates). Currently it is a concrete no-op.

**TODOs:**

- [datablock.py](src/easydiffraction/core/datablock.py#L39)

**Depends on:** related to issue 11.

---

## 34. 🟢 Auto-Extract `PeakProfileTypeEnum` from Peak Classes

**Type:** Design

Three related TODOs in `enums.py` ask whether `PeakProfileTypeEnum`
values can be auto-extracted from the actual peak profile classes in
`peak/cwl.py`, `tof.py`, `total.py` instead of being hardcoded, and
whether the same pattern can be reused for other enums.

**TODOs:**

- [enums.py](src/easydiffraction/datablocks/experiment/item/enums.py#L153)
- [enums.py](src/easydiffraction/datablocks/experiment/item/enums.py#L157)
- [enums.py](src/easydiffraction/datablocks/experiment/item/enums.py#L158)

**Depends on:** related to issue 9.

---

## 35. 🟢 Rename `BeamModeEnum` Members to CWL/TOF

**Type:** Naming

`BeamModeEnum.CONSTANT_WAVELENGTH` and `TIME_OF_FLIGHT` have a TODO to
be renamed to `CWL` and `TOF`.

**TODOs:**

- [enums.py](src/easydiffraction/datablocks/experiment/item/enums.py#L113)

**Depends on:** nothing.

---

## 36. 🟢 Consider a Common `EnumBase` with `default()` / `description()`

**Type:** Design

`BackgroundTypeEnum` and other enums repeat the same `default()` /
`description()` method pattern. A shared `EnumBase` would reduce
boilerplate.

**TODOs:**

- [enums.py](src/easydiffraction/datablocks/experiment/categories/background/enums.py#L10)

**Depends on:** related to issue 9.

---

## 37. 🟢 Rename Experiment `.type` Property

**Type:** Naming

`ExperimentBase.type` returns experimental metadata but the name shadows
the built-in `type`. A TODO suggests finding a better name.

**TODOs:**

- [base.py](src/easydiffraction/datablocks/experiment/item/base.py#L75)

**Depends on:** nothing.

---

## 38. 🟡 Fix `@typechecked` / gemmi Interaction in Factories

**Type:** Bug

Both `StructureFactory` and `ExperimentFactory` have `from_cif_str`
methods where `@typechecked` is commented out because it "fails to find
gemmi". They also share TODOs about adding minimal default configuration
for missing parameters and reading content from files.

**TODOs:**

- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L41)
- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L91)
- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L115)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L59)
  — `Add to core/factory.py?`
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L108)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L177)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L201)

**Depends on:** nothing.

---

## 39. 🟢 Improve `_update_priority` Handling in Categories

**Type:** Design

`CategoryItem` and `CategoryCollection` both define
`_update_priority = 10` with a TODO to set different defaults and use
them during CIF serialisation. The duplicated `_update` no-op methods
are also marked.

**TODOs:**

- [category.py](src/easydiffraction/core/category.py#L21)
- [category.py](src/easydiffraction/core/category.py#L23)
- [category.py](src/easydiffraction/core/category.py#L32)
- [category.py](src/easydiffraction/core/category.py#L174)
- [category.py](src/easydiffraction/core/category.py#L199)

**Depends on:** related to issues 10, 11.

---

## 40. 🟢 Implement Resetting `.constrained` to `False`

**Type:** Feature

`ConstraintsHandler` has a TODO to implement changing the `.constrained`
attribute back to `False` when constraints are removed.

**TODOs:**

- [singleton.py](src/easydiffraction/core/singleton.py#L37)

**Depends on:** nothing.

---

## 41. 🟢 Check Whether `_mark_dirty` in `_set_value` is Actually Used

**Type:** Cleanup

`GenericDescriptorBase._set_value` marks the parent datablock dirty with
a TODO questioning whether this path is exercised.

**TODOs:**

- [variable.py](src/easydiffraction/core/variable.py#L154)

**Depends on:** nothing.

---

## 42. 🟢 MkDocs Doesn't Unpack Types in Validation Module

**Type:** Docs

A TODO in `validation.py` notes that MkDocs doesn't unpack types
properly.

**TODOs:**

- [validation.py](src/easydiffraction/core/validation.py#L25)

**Depends on:** nothing.

---

## 43. 🟢 Fix Summary Display Inconsistencies

**Type:** UX

The summary module has TODOs about fixing description wrapping and
inconsistent header capitalisation.

**TODOs:**

- [summary.py](src/easydiffraction/summary/summary.py#L52)
- [summary.py](src/easydiffraction/summary/summary.py#L164)

**Depends on:** nothing.

---

## 44. 🟢 Merge Parameter Record Construction in Analysis

**Type:** Cleanup

`Analysis._params_to_dataframe` has TODOs to merge record construction
for `StringDescriptor`/`NumericDescriptor`/`Parameter` and to use `repr`
formatting for `StringDescriptor` values.

**TODOs:**

- [analysis.py](src/easydiffraction/analysis/analysis.py#L461)
- [analysis.py](src/easydiffraction/analysis/analysis.py#L462)

**Depends on:** nothing.

---

## 45. 🟢 Decide Default for Alias/Constraint Descriptors

**Type:** Design

`Aliases` and `Constraints` categories use `default='_'` with a
`TODO, Maybe None?` marker.

**TODOs:**

- [default.py](src/easydiffraction/analysis/categories/aliases/default.py#L40)
- [default.py](src/easydiffraction/analysis/categories/constraints/default.py#L33)

**Depends on:** nothing.

---

## 46. 🟢 Rename `JointFitExperiments` ID and Improve Descriptions

**Type:** Naming

`JointFitExperiments` uses `name='id'` with a TODO suggesting a better
name, and two description fields are incomplete.

**TODOs:**

- [default.py](src/easydiffraction/analysis/categories/joint_fit_experiments/default.py#L33)
- [default.py](src/easydiffraction/analysis/categories/joint_fit_experiments/default.py#L34)
- [default.py](src/easydiffraction/analysis/categories/joint_fit_experiments/default.py#L43)

**Depends on:** nothing.

---

## 47. 🟢 Improve Error Handling in Crystallography Utilities

**Type:** Diagnostics

`crystallography.py` logs errors with a TODO asking whether these should
raise `ValueError` or provide better diagnostics.

**TODOs:**

- [crystallography.py](src/easydiffraction/crystallography/crystallography.py#L39)
- [crystallography.py](src/easydiffraction/crystallography/crystallography.py#L45)
- [crystallography.py](src/easydiffraction/crystallography/crystallography.py#L84)

**Depends on:** nothing.

---

## 48. 🟢 Fix CrysPy TOF Instrument Default

**Type:** Bug workaround

`TofInstrument.calib_d_to_tof_quad` defaults to `-0.00001` because
CrysPy does not accept `0`.

**TODOs:**

- [tof.py](src/easydiffraction/datablocks/experiment/categories/instrument/tof.py#L95)

**Depends on:** upstream CrysPy fix.

---

## 49. 🟢 Automate Space Group CIF Name Variants

**Type:** Maintainability

`SpaceGroup.name_h_m` lists multiple CIF tag variants (with `.` and
`_`). A TODO asks to keep only the dotted version and automate variant
generation.

**TODOs:**

- [default.py](src/easydiffraction/datablocks/structure/categories/space_group/default.py#L52)

**Depends on:** nothing.

---

## 50. 🟢 Clarify `Cell._update` Usage of `called_by_minimizer`

**Type:** Cleanup

`Cell._update` deletes `called_by_minimizer` with a `TODO: ???`.

**TODOs:**

- [default.py](src/easydiffraction/datablocks/structure/categories/cell/default.py#L146)

**Depends on:** related to issue 11.

---

## 51. 🟢 Access Space Group from `AtomSites` for Wyckoff Letters

**Type:** Design

`AtomSite` needs the current space group to determine allowed Wyckoff
letters but currently returns a hardcoded list. Also, a missing Wyckoff
letter case needs a decision.

**TODOs:**

- [default.py](src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L163)
- [default.py](src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L179)
- [default.py](src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L353)

**Depends on:** nothing.

---

## 52. 🟢 Rename Line-Segment Background `y` to `intensity`

**Type:** Naming

`LineSegmentBackgroundPoint.y` has TODOs to rename to `intensity`.

**TODOs:**

- [line_segment.py](src/easydiffraction/datablocks/experiment/categories/background/line_segment.py#L67)
- [line_segment.py](src/easydiffraction/datablocks/experiment/categories/background/line_segment.py#L72)

**Depends on:** nothing.

---

## 53. 🟢 Move `show()` to `CategoryCollection` Base Class

**Type:** Maintainability

`ExcludedRegions.show()` and `BackgroundBase.show()` duplicate table-
rendering logic. The TODO suggests moving it to the base class.

**TODOs:**

- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L166)
- [base.py](src/easydiffraction/datablocks/experiment/categories/background/base.py#L19)

**Depends on:** nothing.

---

## 54. 🟢 Add `point_id` to Excluded Regions

**Type:** Completeness

`ExcludedRegion` has a TODO to add `point_id` similar to background
categories.

**TODOs:**

- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L33)

**Depends on:** nothing.

---

## 55. 🟢 Fix Jupyter Scroll Disabling for MkDocs

**Type:** Docs / UX

`display/__init__.py` has disabled `JupyterScrollManager` because it
breaks MkDocs builds.

**TODOs:**

- [**init**.py](src/easydiffraction/display/__init__.py#L15)

**Depends on:** nothing.

---

## 56. 🟢 Make ASCII Plot Width Configurable

**Type:** UX

`ascii.py` hardcodes `width = 60` with a TODO to make it configurable.

**TODOs:**

- [ascii.py](src/easydiffraction/display/plotters/ascii.py#L144)
- [ascii.py](src/easydiffraction/display/plotters/ascii.py#L98)

**Depends on:** nothing.

---

## 57. 🟢 Clean Up CIF Deserialisation Helpers

**Type:** Maintainability

`serialize.py` has several TODOs: verify methods after the
`format_param_value` section, extract a helper for quoted-string
stripping, find a better way to set `_item_type` on
`CategoryCollection`, rename it to `_item_cls`, and remove duplicated
`param_from_cif` logic.

**TODOs:**

- [serialize.py](src/easydiffraction/io/cif/serialize.py#L454)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L562)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L617)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L619)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L656)

**Depends on:** nothing.

---

## 58. 🟢 Move `as_cif` / `show_as_cif` from `ProjectInfo` to `io.cif.serialize`

**Type:** Maintainability

`ProjectInfo` methods `as_cif` and `show_as_cif` have TODOs suggesting
they belong in the serialisation module.

**TODOs:**

- [project_info.py](src/easydiffraction/project/project_info.py#L123)
- [project_info.py](src/easydiffraction/project/project_info.py#L128)

**Depends on:** nothing.

---

## 59. 🟢 Add CIF Name Validation or Normalisation in Parse

**Type:** Robustness

`io/cif/parse.py` has a TODO about adding a validator or normalisation
step.

**TODOs:**

- [parse.py](src/easydiffraction/io/cif/parse.py#L29)

**Depends on:** nothing.

---

## 60. 🟢 Unify `mkdir` Usage Across the Codebase

**Type:** Cleanup

`io/ascii.py` has a TODO to unify directory creation with other uses.

**TODOs:**

- [ascii.py](src/easydiffraction/io/ascii.py#L118)

**Depends on:** nothing.

---

## 61. 🟢 Clarify Logger Default Reaction Mode

**Type:** Design

`Logger._reaction` defaults to `Reaction.RAISE` with a
`TODO: not default?` marker.

**TODOs:**

- [logging.py](src/easydiffraction/utils/logging.py#L430)

**Depends on:** nothing.

---

## 62. 🟢 Complete Migration from `render_table` to `TableRenderer`

**Type:** Cleanup

`utils.py` has a temporary `render_table` utility that should be
replaced with `TableRenderer`.

**TODOs:**

- [utils.py](src/easydiffraction/utils/utils.py#L510)

**Depends on:** nothing.

---

## 63. 🟢 Fix Calculator `calculate_pattern` Signature Type

**Type:** Design

`CalculatorBase.calculate_pattern` takes `structure: Structures` but the
TODO asks whether it should be `Structure` (singular).

**TODOs:**

- [base.py](src/easydiffraction/analysis/calculators/base.py#L40)

**Depends on:** nothing.

---

## 64. 🟢 Check Whether `_not_used_if_loading_from_cif` Code is Needed

**Type:** Cleanup

`BraggPdExperiment` has a block marked
`TODO: Not used if loading from cif file?`.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/item/bragg_pd.py#L112)

**Depends on:** nothing.

---

## 65. 🟡 Replace All Bare `print()` Calls with Logging

**Type:** Code quality

~22 bare `print()` calls exist in `src/` (not `console.print()`, not
commented out). All output should go through `log` or `console` so that
verbosity is controllable. Key offenders: `fitting.py`, `sequential.py`,
`ascii.py`, `base.py` (experiment), calculator modules, `singleton.py`.

**Depends on:** nothing.

---

## 66. 🟡 Decide Error-Handling Strategy: `log.error` vs `raise`

**Type:** Design

The codebase mixes `log.error(msg)` (which may raise depending on
`Reaction` mode) and direct `raise ValueError(...)`. A consistent
strategy is needed: when to use `log.error` (user-facing, recoverable)
vs native exceptions (programmer errors, unrecoverable). This also
relates to the `Reaction` mode setting (issue 61).

**Depends on:** issue 61.

---

## 67. 🟡 Custom Validation for Parameter/Descriptor and Category Types

**Type:** Design

Parameters and Descriptors use `RangeValidator`, `RegexValidator`,
`MembershipValidator` for values but rely on `@typechecked` (only in
some places) for type checking. Category switchable types use different
validation paths. Decide whether to:

- Use custom validators for both types and values on Parameters.
- Use custom validators for category type setters.
- Standardise the approach across the codebase.

**Depends on:** issue 38 (`@typechecked` / gemmi interaction).

---

## 68. 🟢 Decide Whether to Apply `@typechecked` to All Public Methods

**Type:** Design

`@typechecked` is currently applied only in ~24 places (factories,
collections). Decide whether it should be applied systematically to all
public method signatures, or whether custom validation (issue 67) is
preferred.

**Depends on:** issue 67.

---

## 69. 🟢 Shorter Public API Names via `__init__.py` Re-Exports

**Type:** API ergonomics

Classes are imported in `__init__.py` files but users still need deep
paths to reach them. Consider whether top-level re-exports (e.g.
`from easydiffraction import Project, Structure, Experiment`) should
provide shorter access, and document the policy.

**Depends on:** nothing.

---

## 70. 🟡 Standardise Class Member Ordering and Visual Section Headers

**Type:** Code style

Agree on and enforce a consistent ordering within every class:

1. Class-level attributes / metadata
2. `__init__`
3. Private helper methods
4. Public properties (getters/setters)
5. Public methods

Each group should have a comment header (e.g.
`# --- Public properties ---`) for visual separation. Some classes
already use this pattern; apply it uniformly.

**Depends on:** nothing.

---

## 71. 🟢 Create `_update_priority` Reference Table for Categories

**Type:** Documentation

Create and maintain a table listing all categories that implement
`_update()`, sorted by their `_update_priority`. This makes the update
order explicit and helps catch priority conflicts.

**Depends on:** related to issues 11, 39.

---

## 72. 🟡 Warn on All Switchable-Category Type Changes

**Type:** UX / Consistency

Switching `background_type` already warns: "Switching background type
discards 1 existing background point(s)." The same warning pattern
should apply to all other switchable types (`peak_profile_type`,
`data_type`, etc.) so users know their values will be lost.

**Depends on:** nothing.

---

## 73. 🟢 Unify Setter Parameter Naming Convention

**Type:** Code style

Some setters use `new`, others use `value`, others use the attribute
name. For example:

```python
@id.setter
def id(self, new):
    self._id.value = new
```

Agree on a single convention (e.g. always `value`) and apply
consistently.

**Depends on:** nothing.

---

## 74. 🟡 Sync Property Type Hints with Private Attributes + Custom Lint

**Type:** Tooling / Correctness

Public property getters return `Parameter` / `StringDescriptor` etc.,
and setters accept `float` / `str` etc. These annotations must stay in
sync with the private `_attr` type. Currently there is no automated
check. Options:

- A custom script (like `param_consistency.py`) to verify sync.
- A ruff plugin or post-ruff check step.
- Also covers: enforcing `Base` suffix (not prefix), checking missing
  docstrings (issue 81), and other project-specific conventions.

**Depends on:** nothing.

---

## 75. 🟢 Add `show_supported_calculators()` on Analysis or Project

**Type:** API completeness

`show_calculator_types()` exists per-experiment, but there is no
project/analysis-level method to list all available calculator engines.
Users exploring the API have no single entry point to see what
calculators are installed.

**Depends on:** nothing.

---

## 76. 🟡 Consistent `_type` Suffix in Switchable-Category API Names

**Type:** Naming / Consistency

The switchable-category naming convention prescribes `<category>_type`
(getter/setter) and `show_supported_<category>_types()`. But some names
deviate: e.g. `show_minimizer_types()` instead of
`show_supported_minimizer_types()`, and `minimizer_type` instead of
`minimizer_type`. Audit and align all switchable-category APIs.

**Depends on:** nothing.

---

## 77. 🟡 Add `help()` to `Project` and Enrich Existing `help()` Methods

**Type:** API discoverability

`help()` exists on `CategoryItem`, `CollectionBase`, `DatablockItem`,
and `Analysis`, but **not on `Project`**. The user's primary entry point
lacks discoverability. Additionally, each `help()` level should guide
the user to the next level:

1. `project.help()` → attributes: info, experiments, structures,
   analysis, summary.
2. `project.experiments.help()` → list experiments and how to select.
3. `project.experiments['name'].help()` → list categories.
4. `experiment.peak.help()` → list public attributes.
5. `experiment.background.help()` → list items + array accessors.
6. `experiment.background['id'].help()` → list attributes.

**Depends on:** nothing.

---

## 79. 🟢 Verify Completeness of Analysis CIF Serialisation

**Type:** Correctness

`analysis_to_cif()` and `analysis_from_cif()` exist, but audit whether
**all** analysis state is persisted: aliases, constraints, fit mode,
joint-fit weights, minimiser type, calculator assignments. Any missing
fields means a loaded project silently differs from the saved one.

**Depends on:** related to issue 16.

---

## 80. 🟢 Resolve `Any` vs `object` Type Annotation Policy

**Type:** Code style

Both `Any` and `object` are used as generic parameter types. Current
pattern: `Any` inside containers (`dict[str, Any]`), `object` for
standalone params (often to avoid circular imports). Decide on a policy:

- Use protocol types / `TYPE_CHECKING` imports instead of `object`.
- Reserve `Any` for genuinely unknown types.
- Document when each is appropriate.

**Depends on:** nothing.

---

## 81. 🟡 Enforce Docstrings on All Public Methods

**Type:** Code quality

Some public methods (e.g. `plot_meas_vs_calc`, others) lack docstrings.
Decide:

- All public methods **must** have numpy-style docstrings.
- Private helpers: minimal one-liner docstring or none? Choose a policy.
- Enable a ruff rule (e.g. `D103`, `D102`) or add a custom check to
  enforce.

**Depends on:** nothing.

---

## 82. 🟢 Document `param-docstring-fix` and `notebook-prepare` Workflow

**Type:** Documentation

Two manual workflow steps are required between releases/changes:

1. `pixi run param-docstring-fix` — sync Parameter docstrings.
2. `pixi run notebook-prepare` — regenerate tutorial notebooks from
   scripts.

Document these in `CONTRIBUTING.md` or the architecture doc so they are
not forgotten.

**Depends on:** nothing.

---

## 83. 🟢 Remove Redundant Parameter Listing from Parameter Itself

**Type:** Cleanup

Parameters currently carry some form of self-listing metadata that is
redundant with the category/collection level. Remove it to keep the
single-responsibility principle.

**Depends on:** nothing.

---

## 84. 🟡 Serialise `None` as `.` in CIF Output

**Type:** Correctness

CIF output currently writes `None` as literal text for some fields (e.g.
`_diffrn.ambient_pressure None`). CIF convention uses `.` for
inapplicable values and `?` for unknown. The CIF writer should map
`None` → `.` (or `?` depending on semantics), and the reader should map
`.` → `None`.

**Depends on:** nothing.

---

## 85. 🟡 Retain Per-Experiment Fitted Parameters for Plotting

**Type:** Correctness / UX

In `single` fit mode, only the last experiment's fit results are
retained because structure parameters are overwritten on each iteration.
This means earlier experiments cannot be plotted correctly after
fitting.

**Fix:** after fitting each experiment, store a snapshot of its fitted
parameters (both structure and experiment) so that any experiment can be
re-plotted or inspected later. Also clarify: does `fit_results` need to
keep the last mutable parameter set after adding a snapshot?

**Depends on:** nothing (issue 78 resolved).

---

## 86. 🟢 Auto-Resolve `plot_param` X-Axis Descriptor and Add Units

**Type:** UX

`plot_param_series` currently requires the user to manually specify the
x-axis parameter (e.g. `x_axis='temperature'` → look up
`diffrn.ambient_temperature`). This should be auto-resolved from the
parameter name. Additionally, axis labels should include units (e.g.
"Temperature (K)").

**Depends on:** nothing.

---

## 87. 🟢 Redesign Tutorial Grouping and Categorisation

**Type:** Documentation / UX

The current tutorial index uses a flat `"level": "advanced"` tag. A
richer categorisation system is needed:

- Group by topic (matching the docs structure).
- Multiple difficulty levels.
- Multiple Python-knowledge levels.

**Depends on:** nothing.

---

## 88. 🟢 Fix Dataset 26 Description (47 Files, Not 57)

**Type:** Data

Dataset 26 description says "57 files" but should say "47 files":
`"Co2SiO4, D20 (ILL), 57 files, T from ~50K to ~500K"` →
`"Co2SiO4, D20 (ILL), 47 files, T from ~50K to ~500K"`.

**Depends on:** nothing.

---

## 89. 🟡 Parallel Independent Fits for Single/Independent Fit Mode

**Type:** Performance

In `single` (independent) fit mode, each experiment has its own
structure parameters and is completely independent. These fits could run
in parallel threads. Sequential mode, by contrast, must remain single-
threaded because each step's output is the next step's input.

**Depends on:** nothing (issue 78 resolved).

---

## 90. 🟢 Show Experiment Number/Total During Sequential Fitting

**Type:** UX

Currently prints: `Using experiment 🔬 'd20_30' for 'single' fitting`

Should print:
`Using experiment 🔬 'd20_30' (No. 30 of 47) for 'single' fitting`

**Depends on:** nothing.

---

## 91. 🟢 Disable TODO Comment Checks in CodeFactor PRs

**Type:** CI / Tooling

CodeFactor flags TODO comments as unresolved issues (rule C100) in PRs.
Since TODOs are tracked in `issues_open.md`, the CodeFactor check adds
noise. Disable the C100 rule or configure CodeFactor to ignore TODO
comments.

**Depends on:** nothing.

---

## 92. 🟢 Make `save()` Respect Verbosity Settings

**Type:** UX

`Project.save()` unconditionally prints progress via `console.print()`.
It should respect the logger's verbosity mode so that silent/quiet
operation is possible (e.g. in automated pipelines or tests).

**Depends on:** nothing.

---

## Summary

| #   | Issue                                            | Severity | Type             |
| --- | ------------------------------------------------ | -------- | ---------------- |
| 3   | Rebuild joint-fit weights                        | 🟡 Med   | Fragility        |
| 5   | `Analysis` as `DatablockItem`                    | 🟡 Med   | Consistency      |
| 8   | Explicit `create()` signatures                   | 🟡 Med   | API safety       |
| 9   | Future enum extensions                           | 🟢 Low   | Design           |
| 10  | Unify update orchestration                       | 🟢 Low   | Maintainability  |
| 11  | Document `_update` contract                      | 🟢 Low   | Maintainability  |
| 13  | Suppress redundant dirty-flag sets               | 🟢 Low   | Performance      |
| 14  | Finer-grained change tracking                    | 🟢 Low   | Performance      |
| 15  | Validate joint-fit weights                       | 🟡 Med   | Correctness      |
| 17  | Use PDF-specific CIF names                       | 🟢 Low   | Naming           |
| 18  | Move CIF v2→v1 conversion out of calculator      | 🟢 Low   | Maintainability  |
| 19  | Debug-mode logging for calculator imports        | 🟢 Low   | Diagnostics      |
| 20  | Redirect/suppress CrysPy stderr                  | 🟢 Low   | UX               |
| 21  | Clarify CrysPy TOF background CIF tags           | 🟡 Med   | Correctness      |
| 22  | Check SC instrument mapping in CrysPy            | 🟢 Low   | Correctness      |
| 23  | Investigate PyCrysFML pattern length discrepancy | 🟢 Low   | Correctness      |
| 24  | Process defaults on experiment creation          | 🟢 Low   | Design           |
| 25  | Refactor data `_update` methods                  | 🟡 Med   | Maintainability  |
| 26  | Clarify `dtype` usage in data arrays             | 🟢 Low   | Cleanup          |
| 27  | Handle zero uncertainty in Bragg PD              | 🟢 Low   | Correctness      |
| 28  | Clarify Bragg PD data collection description     | 🟢 Low   | Cleanup          |
| 29  | Standardise CIF ID validator pattern             | 🟡 Med   | Consistency      |
| 30  | Make `refinement_status` default an Enum         | 🟢 Low   | Design           |
| 31  | Rename PD data point mixins                      | 🟢 Low   | Naming           |
| 32  | Move common methods to `DatablockCollection`     | 🟡 Med   | Maintainability  |
| 33  | Make `_update_categories` abstract               | 🟡 Med   | Design           |
| 34  | Auto-extract `PeakProfileTypeEnum`               | 🟢 Low   | Design           |
| 35  | Rename `BeamModeEnum` members to CWL/TOF         | 🟢 Low   | Naming           |
| 36  | Common `EnumBase` class                          | 🟢 Low   | Design           |
| 37  | Rename experiment `.type` property               | 🟢 Low   | Naming           |
| 38  | Fix `@typechecked`/gemmi in factories            | 🟡 Med   | Bug              |
| 39  | Improve `_update_priority` handling              | 🟢 Low   | Design           |
| 40  | Implement resetting `.constrained` to `False`    | 🟢 Low   | Feature          |
| 41  | Check `_mark_dirty` in `_set_value`              | 🟢 Low   | Cleanup          |
| 42  | MkDocs type unpacking in validation              | 🟢 Low   | Docs             |
| 43  | Fix summary display inconsistencies              | 🟢 Low   | UX               |
| 44  | Merge parameter record construction              | 🟢 Low   | Cleanup          |
| 45  | Decide alias/constraint descriptor default       | 🟢 Low   | Design           |
| 46  | Rename `JointFitExperiments` id + descriptions   | 🟢 Low   | Naming           |
| 47  | Improve error handling in crystallography        | 🟢 Low   | Diagnostics      |
| 48  | Fix CrysPy TOF instrument default                | 🟢 Low   | Bug workaround   |
| 49  | Automate space group CIF name variants           | 🟢 Low   | Maintainability  |
| 50  | Clarify `Cell._update` minimizer param           | 🟢 Low   | Cleanup          |
| 51  | Access space group for Wyckoff letters           | 🟢 Low   | Design           |
| 52  | Rename line-segment `y` to `intensity`           | 🟢 Low   | Naming           |
| 53  | Move `show()` to `CategoryCollection`            | 🟢 Low   | Maintainability  |
| 54  | Add `point_id` to excluded regions               | 🟢 Low   | Completeness     |
| 55  | Fix Jupyter scroll disabling for MkDocs          | 🟢 Low   | Docs / UX        |
| 56  | Make ASCII plot width configurable               | 🟢 Low   | UX               |
| 57  | Clean up CIF deserialisation helpers             | 🟢 Low   | Maintainability  |
| 58  | Move `ProjectInfo` CIF methods to `serialize`    | 🟢 Low   | Maintainability  |
| 59  | Add CIF name validation in parse                 | 🟢 Low   | Robustness       |
| 60  | Unify `mkdir` usage                              | 🟢 Low   | Cleanup          |
| 61  | Clarify logger default reaction mode             | 🟢 Low   | Design           |
| 62  | Complete `render_table` → `TableRenderer`        | 🟢 Low   | Cleanup          |
| 63  | Fix calculator `calculate_pattern` signature     | 🟢 Low   | Design           |
| 64  | Check unused-if-loading-from-CIF code            | 🟢 Low   | Cleanup          |
| 65  | Replace all bare `print()` with logging          | 🟡 Med   | Code quality     |
| 66  | Error-handling strategy: `log.error` vs `raise`  | 🟡 Med   | Design           |
| 67  | Custom validation for params and category types  | 🟡 Med   | Design           |
| 68  | `@typechecked` on all public methods?            | 🟢 Low   | Design           |
| 69  | Shorter public API names via `__init__`          | 🟢 Low   | API ergonomics   |
| 70  | Standardise class member ordering + headers      | 🟡 Med   | Code style       |
| 71  | `_update_priority` reference table               | 🟢 Low   | Documentation    |
| 72  | Warn on all switchable-category type changes     | 🟡 Med   | UX               |
| 73  | Unify setter parameter naming                    | 🟢 Low   | Code style       |
| 74  | Sync property type hints + custom lint rules     | 🟡 Med   | Tooling          |
| 75  | `show_supported_calculators()` on Analysis       | 🟢 Low   | API completeness |
| 76  | Consistent `_type` suffix in switchable APIs     | 🟡 Med   | Naming           |
| 77  | Add `help()` to Project + enrich existing        | 🟡 Med   | Discoverability  |
| 79  | Verify analysis CIF serialisation completeness   | 🟢 Low   | Correctness      |
| 80  | Resolve `Any` vs `object` annotation policy      | 🟢 Low   | Code style       |
| 81  | Enforce docstrings on all public methods         | 🟡 Med   | Code quality     |
| 82  | Document `param-docstring-fix` workflow          | 🟢 Low   | Documentation    |
| 83  | Remove redundant parameter listing               | 🟢 Low   | Cleanup          |
| 84  | Serialise `None` as `.` in CIF output            | 🟡 Med   | Correctness      |
| 85  | Retain per-experiment fitted params for plotting | 🟡 Med   | Correctness      |
| 86  | Auto-resolve `plot_param` x-axis + add units     | 🟢 Low   | UX               |
| 87  | Redesign tutorial grouping/categorisation        | 🟢 Low   | Documentation    |
| 88  | Fix Dataset 26 description (47 not 57)           | 🟢 Low   | Data             |
| 89  | Parallel independent fits for single mode        | 🟡 Med   | Performance      |
| 90  | Show experiment number during sequential fitting | 🟢 Low   | UX               |
| 91  | Disable TODO checks in CodeFactor PRs            | 🟢 Low   | CI / Tooling     |
| 92  | Make `save()` respect verbosity                  | 🟢 Low   | UX               |
