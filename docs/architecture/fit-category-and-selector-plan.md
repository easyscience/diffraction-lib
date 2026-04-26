# Configuration Category and Selector Plan

**Date:** 2026-04-26  
**Status:** Discussion draft - public API break acceptable

---

## 1. Goal

Unify user-selectable configuration into explicit categories owned by
the object where that configuration belongs:

- analysis-side `fit`
- experiment-side `calculation`
- project-side `display`

Target persisted configuration:

- `_fit.minimizer_type`
- `_fit.mode`
- `_calculation.calculator_type`
- `_display.plotter_type`
- `_display.tabler_type`

The aim is consistent UX, readable CIF, and a cleaner public model.
Compatibility aliases are not required; a public API break is
acceptable.

---

## 2. Current State

### 2.1 Analysis

Today, analysis configuration is split across two different patterns:

- `minimizer_type` is an owner-level proxy on `Analysis` backed by
  `Fitter.selection`
- `fit_mode` is a real category object containing a single `mode`
  descriptor
- `joint_fit_experiments` is a sibling collection on `Analysis`

This is functional, but the model is asymmetric:

- minimizer selection is persisted as a scalar setting on `_analysis`
- fit mode is persisted via a dedicated `fit_mode` category

### 2.2 Experiment

Experiment configuration also mixes patterns:

- `calculator_type` is an owner-level proxy on `ExperimentBase`
- `background_type`, `extinction_type`, and `peak_profile_type` are
  owner-level selectors for switchable categories
- `peak_profile_type` is already persisted through the `peak` category
  as `_peak.profile_type`

### 2.3 Project display

`Project` already owns `plotter` and `tabler` facades, but these are
constructed directly in `Project.__init__` and are not represented as a
persisted project configuration category. `project.cif` currently saves
only `_project.*` metadata via `ProjectInfo.as_cif()`, and loading uses
`project_info_from_cif()` to restore only that metadata.

---

## 3. UX Principle

From the user's perspective, backend selectors and switchable-category
selectors are the same kind of interaction:

- they choose between named alternatives
- they need discoverable listing APIs
- they should be persisted when they are part of saved project state
- in CIF they should look regular and unsurprising

Internally, they are not identical:

- switchable category selectors replace a whole category object
- backend selectors choose an execution engine or adapter
- semantic selectors choose a value such as `single` or `joint`

The public API and CIF should therefore look consistent even when the
internal mechanics differ.

Because a public break is acceptable, the plan should prefer the
cleanest end-state over temporary compatibility proxies.

---

## 4. Design Decisions For This Proposal

### 4.1 Public API reset is acceptable

The redesign should remove obsolete owner-level selector proxies instead
of carrying them forward.

Examples of names that should be removed rather than aliased long term:

- `analysis.minimizer_type`
- `analysis.fit_mode_type`
- `experiment.calculator_type`
- `project.plotter`
- `project.tabler`

### 4.2 Introduce a new `fit` category on `Analysis`

Add a new category package under `analysis/categories/fit/`.

This category will hold two descriptors:

- `minimizer_type`
- `mode`

Target CIF:

```cif
_fit.minimizer_type  lmfit
_fit.mode            joint
```

Target user API:

```python
project.analysis.fit.minimizer_type = 'lmfit'
project.analysis.fit.mode = 'joint'
```

This makes the persisted fitting configuration explicit and keeps both
settings together in one place.

The `fit` category should also own its own listing API:

```python
project.analysis.fit.show_minimizer_types()
project.analysis.fit.show_modes()
```

If access to the live minimizer backend is needed, it should also be
exposed through the category, for example via
`project.analysis.fit.minimizer`.

### 4.3 Keep `mode`, not `strategy`

Use `_fit.mode`, not `_fit.strategy`.

Reason:

- `single`, `joint`, and `sequential` describe the current fitting mode
- the word `strategy` is likely to be needed later for higher-level
  staged refinement workflows (for example, refining different groups of
  parameters in a preferred order)

So `strategy` should stay available for a future concept instead of
being reused now for the current mode selector.

### 4.4 Keep `peak_profile_type`

Do not rename `peak_profile_type`.

Reason:

- it already matches the actual peak category semantics
- it aligns with `_peak.profile_type`
- `peak_function` would be narrower and less accurate than `profile`

### 4.5 Treat `joint_fit_experiments` as a sibling, not a child

`joint_fit_experiments` must remain a direct child of `Analysis`, not a
child of `fit`.

The `fit` category stores scalar fitting configuration. The joint-fit
weights collection stores per-experiment data. They are related, but not
nested.

Target structure:

```text
Analysis
|- fit
|- joint_fit_experiments
|- aliases
`- constraints
```

### 4.6 Introduce a new `calculation` category on `Experiment`

Add a new category package under
`datablocks/experiment/categories/calculation/`.

This category will hold at least one persisted selector:

- `calculator_type`

Target CIF:

```cif
_calculation.calculator_type  cryspy
```

Target user API:

```python
project.experiments['hrpt'].calculation.calculator_type = 'cryspy'
project.experiments['hrpt'].calculation.show_calculator_types()
```

Recommended live-backend access:

```python
backend = project.experiments['hrpt'].calculation.calculator
```

This resolves the current asymmetry where calculator selection is saved
configuration but lives only as an owner-level proxy.

The category name should remain `calculation`, even though a public API
break is acceptable, because it cleanly separates:

- persisted calculation configuration
- the live calculator backend object

This gives a readable model without overloading one word for both the
saved selector and the runtime engine.

### 4.7 Introduce a new `display` category on `Project`

Add a project-side configuration category responsible for persisted
display-engine selection.

This category will hold:

- `plotter_type`
- `tabler_type`

Target CIF in `project.cif`:

```cif
_project.id               my_project
_project.title            'My Project'
_project.description      ?
_project.created          '26 Apr 2026 12:00:00'
_project.last_modified    '26 Apr 2026 12:00:00'

_display.plotter_type     plotly
_display.tabler_type      pandas
```

Target user API:

```python
project.display.plotter_type = 'plotly'
project.display.tabler_type = 'pandas'
project.display.show_plotter_types()
project.display.show_tabler_types()
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')
```

Recommended display access model:

- `project.display.plotter` returns the live `Plotter` facade
- `project.display.tabler` returns the live `TableRenderer` facade
- top-level `project.plotter` and `project.tabler` are removed from the
  public API

This keeps project-level UI preferences in `project.cif`, where they are
appropriate for CLI-driven reuse of a saved project.

---

## 5. Recommended Public Model After The Refactor

### 5.1 Selector families

After the redesign, the public model should explicitly distinguish three
selector families:

| Family                                      | User intent                       | Example                                                                     | CIF style                                                                      |
| ------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Backend selector                            | Choose execution backend          | `fit.minimizer_type`, `calculation.calculator_type`, `display.plotter_type` | `_fit.minimizer_type`, `_calculation.calculator_type`, `_display.plotter_type` |
| Switchable category implementation selector | Choose category implementation    | `experiment.background_type`                                                | category-owned type tag such as `_peak.profile_type`                           |
| Semantic value selector                     | Choose a scientific/analysis mode | `fit.mode`                                                                  | `_fit.mode`                                                                    |

The important UX point is that all three remain easy to inspect and set
in a similar way, even if they are not implemented by the same classes.

### 5.2 What changes for Analysis

Current:

```python
project.analysis.minimizer_type = 'lmfit'
project.analysis.fit_mode_type = 'joint'
```

Target:

```python
project.analysis.fit.minimizer_type = 'lmfit'
project.analysis.fit.mode = 'joint'
```

This removes the current asymmetry where one fitting selector is an
owner-level proxy and the other is a dedicated category.

### 5.3 What changes for Experiment

Current:

```python
project.experiments['hrpt'].calculator_type = 'cryspy'
backend = project.experiments['hrpt'].calculator
```

Target:

```python
project.experiments['hrpt'].calculation.calculator_type = 'cryspy'
backend = project.experiments['hrpt'].calculation.calculator
```

This moves persisted calculator selection and backend discovery into one
explicit experiment-side category.

### 5.4 What changes for Project display

Current:

```python
project.plotter.plot_meas_vs_calc(expt_name='hrpt')
project.tabler.render(df)
```

Target:

```python
project.display.plotter_type = 'plotly'
project.display.tabler_type = 'pandas'
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')
project.display.tabler.render(df)
```

This makes persisted display configuration explicit and colocates type
selection with the facade objects that use it.

---

## 6. Project.cif Design

### 6.1 Rationale

Display configuration is not analysis semantics, but it is valid
project-level configuration. Persisting it in `project.cif` is useful
for CLI-driven workflows because loading a saved project can restore the
preferred output engines before showing tables or plots.

### 6.2 Scope of `project.cif`

`project.cif` should become the home for:

- `_project.*` metadata
- `_display.*` configuration

It should not absorb analysis-side or experiment-side selectors.

### 6.3 Save/load refactor implied by this design

Today, save/load for `project.cif` is implemented through
`ProjectInfo.as_cif()` and `project_info_from_cif()`, which only handle
`_project.*` keys.

To support `_display.*`, the save/load path must be refactored so that
`project.cif` is treated as project-level configuration, not just
project metadata.

That refactor should:

1. write project metadata and project categories together into
   `project.cif`
2. parse `_project.*` into `ProjectInfo`
3. parse `_display.*` into `Project.display`

This is a deliberate redesign, not a small extension of
`ProjectInfo.as_cif()`.

---

## 8. Proposed Implementation Order

### Phase 1 - Fit category

1. Add `analysis/categories/fit/`.
2. Implement a `Fit` `CategoryItem` with descriptors `minimizer_type`
   and `mode`.
3. Move listing methods onto the category: `fit.show_minimizer_types()`
   and `fit.show_modes()`.
4. Initialize `Analysis.fit` instead of `Analysis._fit_mode`.
5. Remove public owner-level fitting selector proxies.
6. Update analysis CIF serialization/deserialization to use
   `_fit.minimizer_type` and `_fit.mode`.
7. Keep `joint_fit_experiments` as a sibling category.
8. Update docs, fixtures, and tests.

### Phase 2 - Experiment calculator configuration

1. Add `datablocks/experiment/categories/calculation/`.
2. Implement a `Calculation` `CategoryItem` with descriptor
   `calculator_type`.
3. Move supported-type listing onto the category via
   `calculation.show_calculator_types()`.
4. Move live backend access behind the category via
   `calculation.calculator`.
5. Remove public `experiment.calculator` and
   `experiment.calculator_type`.
6. Update dependent experiment code to read calculator selection from
   `experiment.calculation`.
7. Serialize and deserialize `_calculation.calculator_type` in
   experiment CIF.
8. Update docs, fixtures, and tests.

### Phase 3 - Project display configuration

1. Add a project-side `display` configuration object/category.
2. Implement descriptors `plotter_type` and `tabler_type`.
3. Move engine-listing APIs onto `display` via
   `display.show_plotter_types()` and `display.show_tabler_types()`.
4. Expose the live facades from `display` via `display.plotter` and
   `display.tabler`.
5. Remove public `project.plotter` and `project.tabler`.
6. Refactor `project.cif` save/load so it persists `_project.*` and
   `_display.*` together.
7. Update CLI entry points and docs to use `project.display.plotter` and
   `project.display.tabler`.
8. Update docs, fixtures, and tests.

### Phase 4 - Architecture text cleanup

Update `architecture.md` so the selector model is explained as three
public families instead of pretending every selector follows exactly one
pattern.

---

## 9. Migration Notes

Because the project is beta, the preferred direction is to update the
tests, docs, and saved examples directly rather than keep legacy naming
layers.

If this proposal is approved, the fit-related names to remove are:

- `fit_mode` category package
- `_analysis.minimizer_type`
- `_analysis.fit_mode_type`
- `analysis.minimizer_type`
- `analysis.fit_mode_type`
- `analysis.fit_mode`

Experiment-side names to remove:

- `experiment.calculator`
- `experiment.calculator_type`

Project-side names to remove:

- `project.plotter`
- `project.tabler`

Replacements:

- `fit` category package
- `_fit.minimizer_type`
- `_fit.mode`
- `analysis.fit`
- `experiment.calculation`
- `_calculation.calculator_type`
- `project.display`
- `_display.plotter_type`
- `_display.tabler_type`

---

## 10. Design Summary

Approved target for the next implementation discussion:

- introduce `Analysis.fit`
- serialize fitting config as `_fit.minimizer_type` and `_fit.mode`
- introduce `Experiment.calculation`
- serialize calculator selection as `_calculation.calculator_type`
- introduce `Project.display`
- persist display engine selection in `project.cif`
- keep `peak_profile_type`

This gives a cleaner and more user-readable model, aligns saved
configuration with the object that owns it, and accepts a one-time
public API break in exchange for a simpler long-term design.
