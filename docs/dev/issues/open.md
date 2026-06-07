# EasyDiffraction — Open Issues

Prioritised list of issues, improvements, and design questions to
address. Items are ordered by a combination of user impact, blocking
potential, and implementation readiness. When an item is fully
implemented, remove it from this file and update
[`adrs/index.md`](../adrs/index.md) or the relevant ADR if needed.

**Legend:** 🔴 High · 🟡 Medium · 🟢 Low

---

## 3. 🟡 Rebuild Joint-Fit Weights on Every Fit

**Type:** Fragility

`joint_fit` is created once when `fit.mode` becomes `'joint'`. If
experiments are added, removed, or renamed afterwards, the weight
collection is stale. Joint fitting can fail with missing keys or run
with incorrect weights.

**Fix:** rebuild or validate `joint_fit` at the start of every joint
fit. At minimum, `fit()` should assert that the weight keys exactly
match `project.experiments.names`.

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

**Depends on:** benefits from the CategoryOwner migration.

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

## 15. 🟡 Decide Whether Inactive Fit-Mode Categories Stay Lenient

**Type:** API design

`Analysis` currently allows direct access to inactive mode-specific
categories such as `joint_fit` or `sequential_fit`. The values remain
editable, but inactive sections are hidden from help and dropped during
serialization.

**Fix:** confirm whether this lenient access is the long-term contract,
or replace it with a dedicated mode error to prevent silent state loss
on save.

**Depends on:** nothing.

---

## 16. 🟡 Clarify `joint_fit` Lifecycle Outside Execution

**Type:** Fragility

`joint_fit` is validated and auto-populated at `fit()` time, but it does
not react when experiments are later renamed or removed.

**Fix:** decide whether `joint_fit` should stay passive until execution,
or listen for experiment lifecycle changes and prune or warn earlier.

**Depends on:** nothing.

---

## 17. 🟡 Define `joint_fit.weight` Bounds

**Type:** Data model

Joint-fit rows currently allow any non-negative weight, but the public
contract is still unclear about whether `0` means exclusion and whether
an upper bound should exist.

**Fix:** define the supported range and validator semantics for
`joint_fit.weight`.

**Depends on:** nothing.

---

## 18. 🟡 Define `sequential_fit_extract` Target Scope

**Type:** Data model

Sequential extract rules currently target one numeric descriptor under
`experiment.diffrn`. Open questions remain around nested targets,
duplicate rules writing the same target, and how additional supported
prefixes should be introduced when new environment categories appear.

**Fix:** pin the allowed target grammar and duplicate-target behaviour
in an ADR and validation rules.

**Depends on:** nothing.

---

## 19. 🟡 Decide Sequential Extraction Failure Policy

**Type:** Runtime behaviour

Today a failed required extract rule marks that file as failed and the
run continues. The overall aggregation policy is still undefined.

**Fix:** decide whether one failed file should abort the whole run,
remain an isolated row-level failure, or count toward a configurable
failure threshold.

**Depends on:** nothing.

---

## 20. 🟢 Decide Whether Sequential Extraction Should Be Cached

**Type:** Performance

Sequential metadata extraction currently re-reads input files when the
run is repeated or resumed.

**Fix:** decide whether extracted `diffrn.*` values should be cached in
`analysis/results.csv` only, or also in a dedicated reusable cache.

**Depends on:** nothing.

---

## 21. 🟢 Decide How Mid-Run Sequential Failures Persist

**Type:** Recovery design

If a sequential fit fails partway through, the recovery and persistence
contract for `analysis/results.csv` is not fully specified.

**Fix:** define whether partial CSV output is authoritative for resume,
left untouched for manual recovery, or replaced on the next run.

**Depends on:** nothing.

---

## 22. 🟢 Decide Whether CLI Should Override Extract Rules

**Type:** CLI design

The CLI can override mode and worker settings, but persisted
`sequential_fit_extract` rules are not yet overridable from the command
line.

**Fix:** decide whether extraction rules stay project-file-only or gain
an explicit CLI override syntax.

**Depends on:** nothing.

---

## 23. 🟢 Align `dir()` With Help Filtering

**Type:** Discoverability

`help()` now hides inactive analysis categories by fitting mode, while
`dir()` and tab completion still expose the full class surface.

**Fix:** decide whether `dir()` should mirror the help filter or remain
an always-complete developer surface.

**Depends on:** nothing.

---

## 24. 🟢 Decide Whether `single_fit` Needs a Future Category

**Type:** Scope planning

Single mode currently has no dedicated persisted category. Future
single-mode settings could require one, but the threshold is not yet
defined.

**Fix:** decide what concrete single-mode behaviour would justify a
`single_fit` category instead of keeping the mode configuration on the
owner only.

**Depends on:** nothing.

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

## 16. 🟢 Add Serial Pattern-Generation Benchmarks

**Type:** Performance

The dev environment previously installed `pytest-benchmark`, but the
repository does not currently define any benchmark tests. At the same
time, the integration, script, and notebook pytest tasks all run with
`pytest-xdist`, so benchmark plugins only add warning noise and do not
provide reliable performance regression coverage.

Performance regressions are still worth tracking, especially for single
diffraction-pattern calculation where backend or profile changes can
quietly slow interactive workflows.

**Fix:** add a dedicated serial benchmark task outside the normal
parallel pytest suite. Benchmark representative single-pattern
calculations on fixed datasets and calculators, run without `-n auto`,
and define regression thresholds only after measurements are stable on a
controlled runner.

**Depends on:** nothing.

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

## 116. 🟡 cryspy Diverges on TOF Jorgensen–Von Dreele Lorentzian

**Type:** Correctness

For time-of-flight powder data using the Jorgensen–Von Dreele peak
profile, the `cryspy` backend diverges from FullProf and `crysfml`
whenever the Lorentzian term (`broad_lorentz_gamma_*`) is non-zero. On
the Si Verification reference case the profile difference reaches ≈22%
with an integrated-intensity ratio ≈0.72–0.76, while `crysfml` matches
FullProf to <1%. When the Lorentzian term is
zero (NaCaAlF) `cryspy` agrees to <1%, which localises the problem to
the cryspy translation of the pseudo-Voigt (Gaussian ⊗ Lorentzian)
mixing for TOF.

**Fix:** verify how `broad_lorentz_gamma_*` is passed to cryspy for the
`jorgensen-von-dreele` profile and reconcile the convention with
crysfml/FullProf.

**Visible on:** the Si TOF Verification page
(`pd-neut-tof_jvd_si`), whose closeness table flags the `cryspy` rows in
red — reported via a non-raising agreement check, not enforced, so CI
stays green. Re-introduce a strict check, or skip the page via
`docs/docs/verification/ci_skip.txt`, once work on the cryspy backend
begins.

**Depends on:** nothing.

---

## 117. 🟡 Add SyCos/SySin Systematic Peak-Position Corrections

**Type:** Feature / Experiment model

FullProf models systematic peak-position aberrations with `SyCos`
(sample displacement) and `SySin` (transparency), shifting peaks as a
function of angle on top of the `Zero` offset. EasyDiffraction has no
category for these, so it cannot reproduce datasets that use them. The
cryspy side is implemented in
[cryspy PR #46](https://github.com/ikibalin/cryspy/pull/46) (see
[issue #38](https://github.com/ikibalin/cryspy/issues/38)); the
EasyDiffraction side — an instrument-category parameter pair plus the
calculator wiring — is still to do.

A prepared verification page,
`docs/docs/verification/pd-neut-cwl_tch-fcj_lab6.py`, uses the issue #38
LaB6 dataset and is skipped via `ci_skip.txt`. Finishing it also needs a
custom ¹¹B scattering length, the Thompson–Cox–Hastings profile, and a
FullProf-style polynomial background, which that dataset relies on.

**Fix:** add `SyCos`/`SySin` to the CWL instrument category, pass them
to the calculators, then un-skip the LaB6 page.

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

## 93. 🟢 Decide Future of `show_residual` in `plot_meas_vs_calc`

**Type:** API cleanup

Powder Bragg plots now show the residual row by default when
`show_residual=None`, but the public `show_residual` argument still
exists and some call sites still pass `show_residual=True` explicitly.
The API should be clarified: either keep the argument as a compatibility
option, remove it, or standardize a single meaning across powder and
single-crystal plots.

**TODOs:**

- [plotting.py](src/easydiffraction/display/plotting.py#L459)
- [\_\_main\_\_.py](src/easydiffraction/__main__.py#L105)

**Depends on:** nothing.

---

## 94. 🟢 Revisit Powder `refln` Phase Labels and Row IDs

**Type:** Naming / CIF UX

The implemented powder reflection category uses `phase_id` throughout
(`experiment.refln`, `PowderReflnRecord`, Bragg tick labels) and assigns
global sequential row ids. This matches the current implementation, but
the archived planning notes left two follow-up questions open:

1. whether `structure_id` would be clearer than `phase_id` in the public
   API / CIF output, and
2. whether phase-prefixed row ids would make CIF inspection and
   debugging easier than simple `1`, `2`, `3`, ...

**TODOs:**

- [refln_pd.py](src/easydiffraction/datablocks/experiment/categories/data/refln_pd.py#L37)
- [refln_pd.py](src/easydiffraction/datablocks/experiment/categories/data/refln_pd.py#L154)
- [base.py](src/easydiffraction/display/plotters/base.py#L24)

**Depends on:** nothing.

---

## 40. 🟢 Implement Resetting `.user_constrained` to `False`

**Type:** Feature

`ConstraintsHandler` has a TODO to implement changing the
`.user_constrained` attribute back to `False` when constraints are
removed.

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

## 46. 🟢 Improve `JointFitItem` Descriptions

**Type:** Naming

`JointFitItem` uses `name='experiment_id'`, but two description fields
are still incomplete.

**TODOs:**

- [default.py](src/easydiffraction/analysis/categories/joint_fit/default.py#L31)
- [default.py](src/easydiffraction/analysis/categories/joint_fit/default.py#L32)
- [default.py](src/easydiffraction/analysis/categories/joint_fit/default.py#L41)

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

Document these in `CONTRIBUTING.md` or a relevant ADR so they are not
forgotten.

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

## 95. 🟡 Re-Enable DREAM Multiprocessing in Direct Python Scripts

**Type:** Performance / Script runtime

On macOS and other spawn-based platforms, direct Bayesian tutorial
execution via `python script.py` or wrappers such as
`pixi run tutorial docs/docs/tutorials/ed-21.py` can fail during BUMPS
`MPMapper` startup because worker processes re-import `__main__` and
re-execute top-level tutorial code. The current defensive workaround is
to fall back to serial execution for these direct-script entry points,
which avoids the crash but disables DREAM multiprocessing and causes a
large performance drop.

Observed behavior for `ed-21` today:

- Jupyter execution and `easydiffraction PROJECT_DIR fit` both appear to
  use working parallel DREAM and complete `361/361` in about 40 seconds.
- Direct Python-script execution of the same tutorial runs `361/361` in
  about 220 seconds, consistent with the serial fallback path.

**Possible solution:** keep the existing tracker-state cleanup before
pickling and mapper startup, but replace the blanket serial fallback
with an EasyDiffraction-controlled multiprocessing context policy. For
direct Python script entry points, prefer a `fork` context when
available so workers do not re-import the tutorial top level. Keep the
existing behavior for import-safe module entry points such as
`easydiffraction PROJECT_DIR fit` and for platforms where `fork` is
unavailable. Document the tradeoff clearly because `fork` on macOS is
less conservative than `spawn`.

**Depends on:** related to issue 89, but independent.

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
Since TODOs are tracked in `issues/open.md`, the CodeFactor check adds
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

## 93. 🟡 Eliminate Flicker in Live Progress Tables

**Type:** UX

The shared `ActivityIndicator` / Rich `Live` region used by single fit,
sequential fit, and DREAM sampling visibly flickers in terminals
whenever the live renderable grows (new rows appended) or is updated at
a moderate rate. The effect is most pronounced in sequential fit because
rows are added more frequently than in single fit.

**Findings from current investigation:**

- Both single fit (`FitProgressTracker._refresh_activity_indicator`) and
  sequential fit (`_report_chunk_progress`) push a fresh
  `build_table_renderable(...)` into
  `ActivityIndicator.update(content=...)` on each progress event. The
  Rich `Table` instance is rebuilt from scratch every time.
- `_TerminalLiveHandle` / `ActivityIndicator` start `rich.live.Live`
  with `auto_refresh=True`,
  `refresh_per_second=1/_SPINNER_FRAME_SECONDS` (≈10 Hz), and
  `vertical_overflow='visible'`. At every refresh tick, Rich re-renders
  the full multi-line region (table + spinner line), which on many
  terminals causes a visible flicker that scales with row count.
- Earlier attempts to mitigate this in sequential fit by switching to a
  single-line spinner-only `Live` and printing rows above it (so Rich's
  print-above-live mechanism handled them) removed flicker entirely, but
  produced a different visual style from single fit and could not show
  the closing border during the run. That approach was reverted for
  consistency with single fit; flicker came back with it.
- `vertical_overflow='visible'` is required so the growing table is not
  clipped, but it also forces Rich to repaint the whole region rather
  than scroll/append.
- The spinner animation itself drives the refresh rate; lowering
  `refresh_per_second` reduces flicker frequency but makes the spinner
  feel sluggish.
- Single fit appears smoother in practice mainly because content changes
  are throttled (`FIT_PROGRESS_UPDATE_SECONDS = 5.0`) and rows grow
  slowly; the underlying mechanism is the same and it still flickers
  when many iterations are appended quickly.

**Possible directions (not yet evaluated):**

- Decouple spinner refresh from content refresh: drive `Live` at a low
  `refresh_per_second` (e.g. 2–4 Hz) and update content explicitly only
  when a new row arrives, while animating the spinner via the label
  string rather than Rich's renderable diff.
- Render the table once as static `console.print(...)` above a
  single-line spinner-only `Live`, and re-print only the _new_ row(s) on
  each update — restore the streaming approach but emit the bottom
  border at the end (accept the trade-off that the closing border is not
  visible during the run, or print it as part of every update with ANSI
  cursor movement).
- Use `rich.live.Live(transient=False, auto_refresh=False)` and call
  `live.refresh()` manually only when content changes; let the spinner
  animate via a separate background timer or label updates.
- Investigate `rich.progress.Progress` with custom columns and a table
  panel — Rich has optimised diff rendering there.
- Evaluate the actual cause on macOS Terminal / iTerm2 / VS Code
  terminal separately — flicker behaviour differs across emulators.

**Depends on:** nothing. Affects single fit, sequential fit, and DREAM
sampler progress displays — any fix should keep their visuals consistent
(issue #93 should be solved for all three at once).

---

## 102. 🟢 Drop Compute-and-Ignore `result_kind` Validation in CIF Restore

**Type:** Dead code / clarity **Source:** Review 8 finding F7.
**Recommended:** fold into the emcee-minimizer plan.

`_restore_persisted_fit_state`
([serialize.py:595-611](../../../src/easydiffraction/io/cif/serialize.py))
calls `FitResultKindEnum(result_kind_value)` purely for the warning side
effect; the result is discarded. After P1.10 absorbed the
Bayesian-specific categories there is nothing else to do per
`result_kind`.

**Fix:** replace with a validator helper that takes a string and logs
the warning, or move the warning into `fit_result.result_kind` setter so
invalid values are caught on read. Either removes the "compute and
ignore" pattern.

**Depends on:** nothing.

---

## 104. 🟢 Tighten `FitParameterItem.posterior_summary` NaN Behaviour

**Type:** Robustness / partial-data edge case **Source:** Review 8
finding F9.

`FitParameterItem.has_posterior_summary` returns `True` if any posterior
field is set, and `posterior_summary` then builds a
`PosteriorParameterSummary` whose missing floats become `NaN`. A
hand-edited or partially-written CIF row with only
`posterior_gelman_rubin = 1.02` and the rest unset produces a summary
whose `median`, `standard_deviation`, and both interval bounds are
`NaN`. Downstream plotting and the `display.fit_results` table render
NaN intervals — harder to debug than a clean "no posterior" outcome.

The deterministic-fit case is fine: deterministic fits set all required
fields to `None`, so `has_posterior_summary()` returns `False`.

**Fix:** tighten `has_posterior_summary` to require the core stats (at
least `posterior_median` and one interval bound) before emitting a
summary, or split the dataclass into required-statistics and
optional-diagnostics components.

**Depends on:** nothing.

---

## 105. 🟢 Remove Orphaned Fit-Result Reset Helper

**Type:** Cleanup **Source:** `minimizer-input-output-split` review 6.

`Analysis._clear_fit_result_projection` is a private method with no
callers after `_clear_persisted_fit_state` switched to replacing
`self._fit_result` with a fresh paired result instance.

**TODOs:**

- [analysis.py](src/easydiffraction/analysis/analysis.py#L1217)

**Fix:** delete the unused helper, or reintroduce a caller only if a
future fit-result reset path genuinely needs to preserve the active
instance.

**Depends on:** nothing.

---

## 106. 🟢 Document `FitResultBase.result_kind` Default Rationale

**Type:** Code readability **Source:** `minimizer-input-output-split`
review 6.

Most `FitResultBase` descriptors use `default=None, allow_none=True` so
pre-fit CIF output serializes unknown values as `?`. `result_kind`
intentionally keeps a valid enum default because it drives deterministic
versus Bayesian projection handling, but that exception is not
documented in code.

**TODOs:**

- [base.py](src/easydiffraction/analysis/categories/fit_result/base.py#L44)

**Fix:** add a short code comment near the `result_kind` descriptor
explaining why it keeps a concrete default while unknown result values
use `None`.

**Depends on:** nothing.

---

## 107. 🟡 Validate Generated CIF Report Against Official IUCr Dictionaries

**Type:** Test coverage

The runtime gemmi self-check in the IUCr CIF writer was removed (it
validated our own deterministic output at write time and depended on
dictionaries under `tmp/iucr-dicts/`; see the §2.5 amendment in
[`iucr-cif-tag-alignment.md`](../adrs/accepted/iucr-cif-tag-alignment.md)).
That spec-compliance guarantee now needs to live in a dev-time test
instead.

**Fix:** add a unit or functional test that renders both a powder and a
single-crystal IUCr report CIF and validates every emitted tag against
the latest official COMCIFS `cif_core.dic` and `cif_pow.dic`.
Requirements:

- Cover both powder (`_pd_*`, profile/reflection loops) and
  single-crystal report outputs.
- Do **not** read `tmp/` at runtime — pass the dictionaries explicitly
  as a committed test fixture (or fetch them in test setup and pass the
  path in). The check belongs in the test suite, not in the user's write
  path.
- Parse the DDLm/CIF2 form correctly: the current dictionaries use
  `save_<name>` frames with `_definition.id`, which the removed helper's
  `save__tag` regex and a plain `gemmi.cif.read_file` could not handle.
  Use gemmi's DDL reader or a scan adapted to the DDLm layout.
- Allow the project's private `_easydiffraction_*` extension namespace.

**Depends on:** nothing.

---

## 108. 🟢 Smarter Automatic Bond Detection (Near-Neighbour Analysis)

**Type:** UX / Visualization

crysview generates bonds with the cif_core distance rule
(`min_bond_distance_cutoff ≤ d ≤ r_bond(A) + r_bond(B) + bond_distance_incr`),
then prunes to the first coordination shell — a contact survives only if
it is within `1.3×` the nearer atom's nearest-neighbour distance
(`COORDINATION_SHELL_FACTOR` in `display/structure/builder.py`). This
stop-gap handles the common cases (e.g. LBCO renders just the Co–O
octahedron) without a new dependency, but the fixed factor is still a
heuristic: it can over-prune strongly distorted shells (e.g. elongated
Jahn–Teller octahedra) or under-prune others, and it is not yet
user-configurable.

**Fix:** consider a robust, configurable near-neighbour algorithm for
automatic "reasonable" bonding — e.g. a Voronoi / solid-angle method
such as pymatgen's `CrystalNN` or `VoronoiNN`, which weights neighbours
by solid angle instead of a single relative cutoff. The Voronoi route is
the most robust across arbitrary structures but introduces a heavyweight
dependency (pymatgen), so it needs a dependency decision; an
ASE/Jmol-style multiplicative covalent tolerance is lighter but, like
the current factor, cannot separate shells when ionic-cation covalent
radii are large.

**Depends on:** dependency decision for pymatgen (if the Voronoi route
is chosen).

---

## 109. 🟢 Let More Tables Adapt to Terminal Width

**Type:** UX / Display

`list_tutorials` now renders its table at the real terminal width via a
new optional `width` parameter threaded through the table render path
(`render_table` → `TableRenderer.render` → backend `render`; Rich
applies it, the HTML backend ignores it). Every other table and all log
output still go through the shared Rich console, whose width is floored
at `ConsoleManager._MIN_CONSOLE_WIDTH = 130` ("to avoid cramped
layouts"). On a standard ~80-column terminal that floor makes wide
tables overflow and soft-wrap badly.

**Fix:** decide on a global policy — either have `_detect_width` trust
the detected terminal width (keeping 130 only as a fallback when
detection fails), or pass the terminal width into more table call sites
the way `list_tutorials` now does. A global change affects every table
(fit results, parameters, ...) and all logs, so weigh it against the
deliberate minimum-width choice.

**Depends on:** related to issue 62.

---

## 110. 🟢 Render Styled Multi-Line Table Cells in the HTML Backend

**Type:** Display / Notebook parity

`list_tutorials` shows a two-line cell in the terminal — a colored title
on the first line and a dimmed description on the second — using Rich
markup and an embedded newline. The Jupyter table backend
(`PandasTableBackend`) cannot render this: `_strip_rich_markup` only
matches a single full-cell `[color]text[/color]`, and HTML collapses the
newline, so the markup would show as literal text. `list_tutorials` is
therefore gated via `in_jupyter()` to show only the plain title in
notebooks, which drops the description and the color there.

**Fix:** teach the HTML backend to render the same styling — translate
embedded newlines to `<br>`, map `[dim]` to reduced opacity, and accept
multiple/mixed markup tags per cell — then remove the terminal-only gate
in `list_tutorials` so notebooks also get the styled two-line entry.

**Depends on:** related to issue 62.

---

## 111. 🟢 Add Test Coverage for `list_tutorials` Two-Line Rendering

**Type:** Test coverage

The `list_tutorials` table gained a styled two-line cell (colored title
plus dimmed description), a terminal-only `in_jupyter()` gate that falls
back to the plain title, and a new optional `width` parameter on the
table render path. Existing tests only assert that titles appear in the
output.

**Fix:** add unit tests for the description line appearing in the
terminal (non-Jupyter) path, the Jupyter-gated path showing the plain
title with no literal Rich markup, and the `width` parameter sizing the
rendered Rich table. Run `pixi run fix` / `check` / `unit-tests` to
confirm the shared-renderer signature change.

**Depends on:** nothing.

---

## 112. 🟢 Suppress the Redundant Row-Index Column in Tables

**Type:** Display / UX

`TableRenderer._prepare_dataframe` bumps the DataFrame index to 1-based,
and both the Rich and pandas backends always render it as the first
column. For tables that already carry an explicit identifier — e.g.
`list_tutorials`, whose `id` column duplicates that 1-based counter —
the leading index column is redundant and reads as a duplicate.

**Fix:** add an opt-out (e.g. a `show_index` flag on the render path) so
callers with their own id column can hide the auto-generated index, or
only render the index column when no explicit id column is present.

**Depends on:** nothing.

---

## 113. 🟡 Cross-Repository Validation Harness (nightly)

**Type:** Test infrastructure

Deferred cross-repository work for the
[Test Suite and Validation Strategy](../adrs/accepted/test-suite-and-validation.md)
ADR (§7, §8). The harness code lives in `diffraction-lib`; the corpus,
results database, and benchmark/reference history live in the
`diffraction` data repository, fetched at runtime and written back by a
nightly job that installs easydiffraction from PyPI (acceptance-style).

**Items:**

- **COD corpus check.** Download ~100–200 CIF files from the
  Crystallography Open Database, load each, and record per-file status
  (`ok` / `partial` + missing fields / `fail`) in a git-diffable CSV
  keyed and ordered by COD id. Add a `--recheck-failed` flag to re-run
  only the failed/partial entries after fixes (instead of new random
  files). Extend with per-engine calculation results on the corpus.
- **Generative fuzzing.** Randomly generate ~100–200 structures (random
  space group, cell, 1–10 atoms with random coordinates/ADP/occupancy),
  compute patterns across engines, and record disagreements in the same
  database.
- **Benchmark history + gate.** Commit `pytest-benchmark` baseline JSON
  to the data repository and add a regression threshold once timing
  variance is characterised on a controlled runner. (The serial
  benchmark task itself now exists — see issue 16 — this is the
  history/gating remainder.)
- **External-software comparison.** Add FullProf (then GSAS-II/TOPAS)
  pre-calculated profiles as zipped projects in the data repository so
  the Verification pages can overlay them against easydiffraction.

**Depends on:** the `diffraction` data repository; cross-repo
coordination.

---

## 114. 🟢 External Link Checking in the Docs Gate

**Type:** CI / Documentation

The fast docs gate (`docs-build` + `link-check` + `spell-check`) catches
broken nav/internal links and typos on every push, but does not yet
check external URLs. Add a `lychee` link checker (with an allowlist for
rate-limited/unstable domains), coordinated with the
[Documentation CI and Build Verification](../adrs/suggestions/documentation-ci-build.md)
ADR. Run it nightly or on pull requests to avoid flakiness from external
sites. Also covers link-checking of URLs that appear only inside
executed notebook output cells (a feature that does not exist yet).

**Depends on:** nothing.

---

## 115. 🟢 Expand Cross-Engine Verification Coverage

**Type:** Test coverage / Documentation

The Verification docs section ships with the framework and the first
cross-engine comparison page (constant-wavelength powder, cryspy ↔
crysfml). Extend it to the remaining supported combinations declared by
the calculator support matrix — time-of-flight powder (cryspy ↔ crysfml)
and single crystal — so every valid experiment/instrument combination is
documented and regression-checked at least once. Each new page is a
calculation-only `.py` under `docs/docs/verification/` wired into
`script-tests` and `notebook-tests`, with explicit metric tolerances.

**Depends on:** nothing.

---

## Summary

| #   | Issue                                             | Severity | Type                         |
| --- | ------------------------------------------------- | -------- | ---------------------------- |
| 3   | Rebuild joint-fit weights                         | 🟡 Med   | Fragility                    |
| 5   | `Analysis` as `DatablockItem`                     | 🟡 Med   | Consistency                  |
| 8   | Explicit `create()` signatures                    | 🟡 Med   | API safety                   |
| 9   | Future enum extensions                            | 🟢 Low   | Design                       |
| 10  | Unify update orchestration                        | 🟢 Low   | Maintainability              |
| 11  | Document `_update` contract                       | 🟢 Low   | Maintainability              |
| 13  | Suppress redundant dirty-flag sets                | 🟢 Low   | Performance                  |
| 14  | Finer-grained change tracking                     | 🟢 Low   | Performance                  |
| 15  | Validate joint-fit weights                        | 🟡 Med   | Correctness                  |
| 17  | Use PDF-specific CIF names                        | 🟢 Low   | Naming                       |
| 18  | Move CIF v2→v1 conversion out of calculator       | 🟢 Low   | Maintainability              |
| 19  | Debug-mode logging for calculator imports         | 🟢 Low   | Diagnostics                  |
| 20  | Redirect/suppress CrysPy stderr                   | 🟢 Low   | UX                           |
| 21  | Clarify CrysPy TOF background CIF tags            | 🟡 Med   | Correctness                  |
| 22  | Check SC instrument mapping in CrysPy             | 🟢 Low   | Correctness                  |
| 23  | Investigate PyCrysFML pattern length discrepancy  | 🟢 Low   | Correctness                  |
| 24  | Process defaults on experiment creation           | 🟢 Low   | Design                       |
| 25  | Refactor data `_update` methods                   | 🟡 Med   | Maintainability              |
| 26  | Clarify `dtype` usage in data arrays              | 🟢 Low   | Cleanup                      |
| 27  | Handle zero uncertainty in Bragg PD               | 🟢 Low   | Correctness                  |
| 28  | Clarify Bragg PD data collection description      | 🟢 Low   | Cleanup                      |
| 29  | Standardise CIF ID validator pattern              | 🟡 Med   | Consistency                  |
| 30  | Make `refinement_status` default an Enum          | 🟢 Low   | Design                       |
| 31  | Rename PD data point mixins                       | 🟢 Low   | Naming                       |
| 32  | Move common methods to `DatablockCollection`      | 🟡 Med   | Maintainability              |
| 33  | Make `_update_categories` abstract                | 🟡 Med   | Design                       |
| 34  | Auto-extract `PeakProfileTypeEnum`                | 🟢 Low   | Design                       |
| 35  | Rename `BeamModeEnum` members to CWL/TOF          | 🟢 Low   | Naming                       |
| 36  | Common `EnumBase` class                           | 🟢 Low   | Design                       |
| 37  | Rename experiment `.type` property                | 🟢 Low   | Naming                       |
| 38  | Fix `@typechecked`/gemmi in factories             | 🟡 Med   | Bug                          |
| 39  | Improve `_update_priority` handling               | 🟢 Low   | Design                       |
| 40  | Reset `.user_constrained` to `False`              | 🟢 Low   | Feature                      |
| 41  | Check `_mark_dirty` in `_set_value`               | 🟢 Low   | Cleanup                      |
| 42  | MkDocs type unpacking in validation               | 🟢 Low   | Docs                         |
| 43  | Fix summary display inconsistencies               | 🟢 Low   | UX                           |
| 44  | Merge parameter record construction               | 🟢 Low   | Cleanup                      |
| 45  | Decide alias/constraint descriptor default        | 🟢 Low   | Design                       |
| 46  | Improve `JointFitItem` descriptions               | 🟢 Low   | Naming                       |
| 47  | Improve error handling in crystallography         | 🟢 Low   | Diagnostics                  |
| 48  | Fix CrysPy TOF instrument default                 | 🟢 Low   | Bug workaround               |
| 49  | Automate space group CIF name variants            | 🟢 Low   | Maintainability              |
| 50  | Clarify `Cell._update` minimizer param            | 🟢 Low   | Cleanup                      |
| 52  | Rename line-segment `y` to `intensity`            | 🟢 Low   | Naming                       |
| 53  | Move `show()` to `CategoryCollection`             | 🟢 Low   | Maintainability              |
| 54  | Add `point_id` to excluded regions                | 🟢 Low   | Completeness                 |
| 55  | Fix Jupyter scroll disabling for MkDocs           | 🟢 Low   | Docs / UX                    |
| 56  | Make ASCII plot width configurable                | 🟢 Low   | UX                           |
| 57  | Clean up CIF deserialisation helpers              | 🟢 Low   | Maintainability              |
| 58  | Move `ProjectInfo` CIF methods to `serialize`     | 🟢 Low   | Maintainability              |
| 59  | Add CIF name validation in parse                  | 🟢 Low   | Robustness                   |
| 60  | Unify `mkdir` usage                               | 🟢 Low   | Cleanup                      |
| 61  | Clarify logger default reaction mode              | 🟢 Low   | Design                       |
| 62  | Complete `render_table` → `TableRenderer`         | 🟢 Low   | Cleanup                      |
| 63  | Fix calculator `calculate_pattern` signature      | 🟢 Low   | Design                       |
| 64  | Check unused-if-loading-from-CIF code             | 🟢 Low   | Cleanup                      |
| 65  | Replace all bare `print()` with logging           | 🟡 Med   | Code quality                 |
| 66  | Error-handling strategy: `log.error` vs `raise`   | 🟡 Med   | Design                       |
| 67  | Custom validation for params and category types   | 🟡 Med   | Design                       |
| 68  | `@typechecked` on all public methods?             | 🟢 Low   | Design                       |
| 69  | Shorter public API names via `__init__`           | 🟢 Low   | API ergonomics               |
| 70  | Standardise class member ordering + headers       | 🟡 Med   | Code style                   |
| 71  | `_update_priority` reference table                | 🟢 Low   | Documentation                |
| 73  | Unify setter parameter naming                     | 🟢 Low   | Code style                   |
| 74  | Sync property type hints + custom lint rules      | 🟡 Med   | Tooling                      |
| 75  | `show_supported_calculators()` on Analysis        | 🟢 Low   | API completeness             |
| 79  | Verify analysis CIF serialisation completeness    | 🟢 Low   | Correctness                  |
| 80  | Resolve `Any` vs `object` annotation policy       | 🟢 Low   | Code style                   |
| 81  | Enforce docstrings on all public methods          | 🟡 Med   | Code quality                 |
| 82  | Document `param-docstring-fix` workflow           | 🟢 Low   | Documentation                |
| 83  | Remove redundant parameter listing                | 🟢 Low   | Cleanup                      |
| 84  | Serialise `None` as `.` in CIF output             | 🟡 Med   | Correctness                  |
| 85  | Retain per-experiment fitted params for plotting  | 🟡 Med   | Correctness                  |
| 86  | Auto-resolve `plot_param` x-axis + add units      | 🟢 Low   | UX                           |
| 87  | Redesign tutorial grouping/categorisation         | 🟢 Low   | Documentation                |
| 88  | Fix Dataset 26 description (47 not 57)            | 🟢 Low   | Data                         |
| 89  | Parallel independent fits for single mode         | 🟡 Med   | Performance                  |
| 95  | Re-enable DREAM multiprocessing in direct scripts | 🟡 Med   | Performance / Script runtime |
| 90  | Show experiment number during sequential fitting  | 🟢 Low   | UX                           |
| 91  | Disable TODO checks in CodeFactor PRs             | 🟢 Low   | CI / Tooling                 |
| 92  | Make `save()` respect verbosity                   | 🟢 Low   | UX                           |
| 93  | Eliminate flicker in live progress tables         | 🟡 Med   | UX                           |
| 105 | Remove orphaned fit-result reset helper           | 🟢 Low   | Cleanup                      |
| 106 | Document `FitResultBase.result_kind` default      | 🟢 Low   | Code readability             |
| 107 | Validate CIF report vs IUCr dictionaries          | 🟡 Med   | Test coverage                |
| 108 | Smarter automatic bond detection (near-neighbour) | 🟢 Low   | UX / Visualization           |
| 109 | Let more tables adapt to terminal width           | 🟢 Low   | UX / Display                 |
| 110 | Styled multi-line table cells in HTML backend     | 🟢 Low   | Display / Notebook parity    |
| 111 | Test coverage for `list_tutorials` rendering      | 🟢 Low   | Test coverage                |
| 112 | Suppress redundant row-index column in tables     | 🟢 Low   | Display / UX                 |
| 113 | Cross-repository validation harness (nightly)     | 🟡 Med   | Test infrastructure          |
| 114 | External link checking in the docs gate           | 🟢 Low   | CI / Documentation           |
| 115 | Expand cross-engine verification coverage         | 🟢 Low   | Test coverage                |
