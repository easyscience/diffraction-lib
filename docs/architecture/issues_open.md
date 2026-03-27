# EasyDiffraction — Open Issues

Prioritised list of issues, improvements, and design questions to
address. Items are ordered by a combination of user impact, blocking
potential, and implementation readiness. When an item is fully
implemented, remove it from this file and update `architecture.md` if
needed.

**Legend:** 🔴 High · 🟡 Medium · 🟢 Low

---

## 1. 🔴 Implement `Project.load()`

**Type:** Completeness

`save()` serialises all components to CIF files but `load()` is a stub
that raises `NotImplementedError`. Users cannot round-trip a project.

**Why first:** this is the highest-severity gap. Without it the save
functionality is only half useful — CIF files are written but cannot be
read back. Tutorials that demonstrate save/load are blocked.

**Fix:** implement `load()` that reads CIF files from the project
directory and reconstructs structures, experiments, and analysis
settings.

**Depends on:** nothing (standalone).

---

## 2. 🟡 Restore Minimiser Variant Support

**Type:** Feature loss + Design limitation

After the `FactoryBase` migration only `'lmfit'` and `'dfols'` remain as
registered tags. The ability to select a specific lmfit algorithm (e.g.
`'lmfit (leastsq)'`, `'lmfit (least_squares)'`) raises a `ValueError`.

The root cause is that `FactoryBase` assumes one class ↔ one tag;
registering the same class twice with different constructor arguments is
not supported.

**Fix:** decide on an approach (thin subclasses, extended registry, or
two-level selection) and implement. Thin subclasses is the quickest.

**Planned tags:**

| Tag                     | Description                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| `lmfit`                 | LMFIT library using the default Levenberg-Marquardt least squares method |
| `lmfit (leastsq)`       | LMFIT library with Levenberg-Marquardt least squares method              |
| `lmfit (least_squares)` | LMFIT library with SciPy's trust region reflective algorithm             |
| `dfols`                 | DFO-LS library for derivative-free least-squares optimization            |

**Trade-offs:**

| Approach                                                 | Pros                                                                   | Cons                                                                                                  |
| -------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **A. Thin subclasses** (one per variant)                 | Works today; each variant gets full metadata; no `FactoryBase` changes | Class proliferation; boilerplate                                                                      |
| **B. Extend registry to store `(class, kwargs)` tuples** | No extra classes; factory handles variants natively                    | `_supported_map` changes shape; `TypeInfo` moves from class attribute to registration-time data       |
| **C. Two-level selection** (`engine` + `algorithm`)      | Clean separation; engine maps to class, algorithm is a constructor arg | More complex API (`current_minimizer = ('lmfit', 'least_squares')`); needs new `FactoryBase` protocol |

**Depends on:** nothing (standalone, but should be decided before more
factories adopt variants).

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

## 4. 🔴 Refresh Constraint State Before Automatic Updates and Fitting

**Type:** Correctness

`ConstraintsHandler` is only synchronised from `analysis.aliases` and
`analysis.constraints` when the user explicitly calls
`project.analysis.apply_constraints()`. The normal fit / serialisation
path calls `constraints_handler.apply()` directly, so newly added or
edited aliases and constraints can be ignored until that manual sync
step happens.

**Why high:** this produces silently incorrect results. A user can
define constraints, run a fit, and believe they were applied when the
active singleton still contains stale state from a previous run or no
state at all.

**Fix:** before any automatic constraint application, always refresh the
singleton from the current `Aliases` and `Constraints` collections. The
sync should happen inside `Analysis._update_categories()` or inside the
constraints category itself, not only in a user-facing helper method.

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

**Depends on:** benefits from issue 1 (load/save) being designed first.

---

## 6. 🔴 Restrict `data_type` Switching to Compatible Types and Preserve Data Safety

**Type:** Correctness + Data safety

`Experiment.data_type` currently validates against all registered data
tags rather than only those compatible with the experiment's
`sample_form` / `scattering_type` / `beam_mode`. This allows users to
switch an experiment to an incompatible data collection class. The
setter also replaces the existing data object with a fresh empty
instance, discarding loaded data without warning.

**Why high:** the current API can create internally inconsistent
experiments and silently lose measured data, which is especially
dangerous for notebook and tutorial workflows.

**Fix:** filter supported data types through
`DataFactory.supported_for(...)` using the current experiment context,
and warn or block when a switch would discard existing data. If runtime
data-type switching is not a real user need, consider making `data`
effectively fixed after experiment creation.

**Depends on:** nothing.

---

## 7. 🟡 Eliminate Dummy `Experiments` Wrapper in Single-Fit Mode

**Type:** Fragility

Single-fit mode creates a throw-away `Experiments` collection per
experiment, manually forces `_parent` via `object.__setattr__`, and
passes it to `Fitter`. This bypasses `GuardedBase` parent tracking and
is fragile.

**Fix:** make `Fitter.fit()` accept a list of experiment objects (or a
single experiment) instead of requiring an `Experiments` collection. Or
add a `fit_single(experiment)` method.

**Depends on:** nothing, but simpler after issue 5 (Analysis refactor)
clarifies the fitting orchestration.

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

**Depends on:** benefits from issue 5 (Analysis as DatablockItem) and
issue 7 (fitter refactor).

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

## 12. 🟢 Add CIF Round-Trip Integration Test

**Type:** Quality

Ensuring every parameter survives a `save()` → `load()` cycle is
critical for reproducibility. A systematic integration test that creates
a project, populates all categories, saves, reloads, and compares all
parameter values would strengthen confidence in the serialisation layer.

**Depends on:** issue 1 (`Project.load()` implementation).

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

**Depends on:** issue 1 (`Project.load()` implementation).

---

## Summary

| #   | Issue                                      | Severity | Type                    |
| --- | ------------------------------------------ | -------- | ----------------------- |
| 1   | Implement `Project.load()`                 | 🔴 High  | Completeness            |
| 2   | Restore minimiser variants                 | 🟡 Med   | Feature loss            |
| 3   | Rebuild joint-fit weights                  | 🟡 Med   | Fragility               |
| 4   | Refresh constraint state before auto-apply | 🔴 High  | Correctness             |
| 5   | `Analysis` as `DatablockItem`              | 🟡 Med   | Consistency             |
| 6   | Restrict `data_type` switching             | 🔴 High  | Correctness/Data safety |
| 7   | Eliminate dummy `Experiments`              | 🟡 Med   | Fragility               |
| 8   | Explicit `create()` signatures             | 🟡 Med   | API safety              |
| 9   | Future enum extensions                     | 🟢 Low   | Design                  |
| 10  | Unify update orchestration                 | 🟢 Low   | Maintainability         |
| 11  | Document `_update` contract                | 🟢 Low   | Maintainability         |
| 12  | CIF round-trip integration test            | 🟢 Low   | Quality                 |
| 13  | Suppress redundant dirty-flag sets         | 🟢 Low   | Performance             |
| 14  | Finer-grained change tracking              | 🟢 Low   | Performance             |
| 15  | Validate joint-fit weights                 | 🟡 Med   | Correctness             |
| 16  | Persist per-experiment `calculator_type`   | 🟡 Med   | Completeness            |
