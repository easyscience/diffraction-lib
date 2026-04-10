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

## 16. 🟡 Persist Per-Experiment `calculator_type`

**Type:** Completeness

The current architecture moved calculator selection to the experiment
level via `calculator_type`, but this selection is not written to CIF
during `save()` / `show_as_cif()`. Reloading or exporting a project
therefore loses explicit calculator choices and falls back to
auto-resolution.

**Fix:** serialise `calculator_type` as part of the experiment or
analysis state, and make sure `load()` restores it. The saved project
should represent the exact active calculator configuration, not just a
re-derivable default.

**Depends on:** nothing.

---

## Summary

| #   | Issue                                    | Severity | Type            |
| --- | ---------------------------------------- | -------- | --------------- |
| 2   | Restore minimiser variants               | 🟡 Med   | Feature loss    |
| 3   | Rebuild joint-fit weights                | 🟡 Med   | Fragility       |
| 5   | `Analysis` as `DatablockItem`            | 🟡 Med   | Consistency     |
| 8   | Explicit `create()` signatures           | 🟡 Med   | API safety      |
| 9   | Future enum extensions                   | 🟢 Low   | Design          |
| 10  | Unify update orchestration               | 🟢 Low   | Maintainability |
| 11  | Document `_update` contract              | 🟢 Low   | Maintainability |
| 13  | Suppress redundant dirty-flag sets       | 🟢 Low   | Performance     |
| 14  | Finer-grained change tracking            | 🟢 Low   | Performance     |
| 15  | Validate joint-fit weights               | 🟡 Med   | Correctness     |
| 16  | Persist per-experiment `calculator_type` | 🟡 Med   | Completeness    |
