# ADR: Fit Mode Categories and Fit Execution API

**Status:** Proposed  
**Date:** 2026-05-16

## Context

The current analysis API uses `project.analysis.fit` as both a category
and a callable execution entry point:

```python
project.analysis.fit.minimizer_type = 'lmfit (leastsq)'
project.analysis.fit.mode = 'joint'
project.analysis.fit()
```

This creates three problems:

- the same name, `fit`, represents both configuration and execution
- mode-specific configuration is not part of the normal switchable
  category pattern used elsewhere in the API
- `project.analysis.help()` always shows `joint_fit_experiments`, even
  when the active fit mode is not joint

The separate `fit_sequential(...)` method creates another inconsistency.
Sequential fitting is selected by `fit.mode = 'sequential'`, but the
actual run must be started through `fit_sequential(...)` because
sequential-specific settings such as `data_dir`, `max_workers`,
`chunk_size`, `file_pattern`, and `reverse` are currently method
arguments instead of persisted analysis configuration.

The rest of the API already has a clearer convention for switchable
categories. For example, peak profile selection is owned by the
experiment:

```python
project.experiments['hrpt'].show_peak_profile_types()
project.experiments['hrpt'].peak_profile_type = 'pseudo-voigt'
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
```

The owner-level selector switches or configures the active category
shape, and the active category exposes only the parameters that make
sense for that selected type.

Fit modes should follow the same conceptual pattern:

- the `Analysis` owner selects the fit mode
- common fitting configuration lives in a stable category
- mode-specific settings live in mode-specific sibling categories
- help output and CIF serialization reflect the active mode

This ADR intentionally does not preserve the existing public API as a
compatibility surface. The follow-up migration plan may describe file,
test, and documentation changes, but the target design is not required
to keep legacy runtime aliases.

## Decision

### 1. Split fitting configuration from fit execution

`Analysis.fit()` becomes the public operation that executes the current
fit mode.

Common fitting configuration moves to a dedicated category:

```python
project.analysis.fitting.minimizer_type = 'lmfit (leastsq)'
project.analysis.fit()
```

`project.analysis.fit` is no longer a category. It is an action method.

The common `fitting` category owns configuration shared by all fit
modes. Initially this includes:

- `minimizer_type`
- current selected mode as a persisted descriptor, mirrored from the
  owner-level selector

Additional settings that apply to all fit modes can be added here later.
Verbosity remains a call-level or project-level concern and does not
need to be persisted in this category.

### 2. Add an owner-level fitting-mode selector

`Analysis` owns the fitting-mode selector, following the existing
switchable-category style used by experiment categories.

The selector name must start with the public category name. This mirrors
`peak_profile_type` and `show_peak_profile_types()`: the category is
`peak`, and the selected aspect is the peak profile. For fitting, the
category is `fitting`, and the selected aspect is the fitting mode.

```python
project.analysis.show_fitting_mode_types()
project.analysis.fitting_mode_type = 'sequential'
```

The selector is backed by `FitModeEnum` and accepts:

- `single`
- `joint`
- `sequential`

`show_fitting_mode_types()` should show all fitting modes, mark the
current mode, and describe the execution requirements for each mode. It
should not hide `sequential` simply because the project currently has
only one experiment. Sequential fitting uses one template experiment
plus files from `sequential_fit.data_dir`, so filtering it out based on
experiment count is misleading.

The selector changes the active fit mode and controls which
mode-specific public categories are visible and serialized.

The names `fit_mode_type` and `show_fit_mode_types()` are rejected
because there is no public `fit_mode` category. They are less consistent
with the existing category selector convention.

### 3. Keep mode-specific categories as flat Analysis siblings

Mode-specific configuration lives in direct children of `Analysis`.
These categories are not nested under `fitting`.

Public API:

```python
project.analysis.fitting_mode_type = 'joint'
project.analysis.joint_fit.create(experiment_id='sepd', weight=0.7)
project.analysis.joint_fit.create(experiment_id='nomad', weight=0.3)
project.analysis.fit()
```

```python
project.analysis.fitting_mode_type = 'sequential'
project.analysis.sequential_fit.data_dir = 'data/d20_scan'
project.analysis.sequential_fit.file_pattern = '*.xye'
project.analysis.sequential_fit.max_workers = 'auto'
project.analysis.sequential_fit.reverse = True
project.analysis.fit()
```

There is no `single_fit` category initially because single fitting has
no mode-specific persisted settings. If single-mode settings are added
later, they should be placed in a `single_fit` category using the same
pattern.

### 4. Replace `joint_fit_experiments` with `joint_fit`

The user-facing joint-mode category is named `joint_fit`.

It is a collection keyed by experiment id. Each item contains:

- `experiment_id`
- `weight`

Suggested API:

```python
project.analysis.joint_fit.create(experiment_id='sepd', weight=0.7)
project.analysis.joint_fit.create(experiment_id='nomad', weight=0.3)
project.analysis.joint_fit['sepd'].weight = 0.8
```

When joint mode is active, `joint_fit` should represent the experiments
participating in the joint fit. Missing rows may be auto-created with a
neutral default weight when switching to joint mode or before execution,
but partially configured or stale rows must be validated before fitting.

Execution requirements for joint fitting:

- at least two project experiments
- every joint-fit row references an existing experiment
- every participating experiment has one weight

Weights remain relative weights. The fitting implementation may
normalize them internally.

### 5. Add a `sequential_fit` category

The user-facing sequential-mode category is named `sequential_fit`.

It is a single-item category with these persisted fields:

- `data_dir`
- `file_pattern`
- `max_workers`
- `chunk_size`
- `reverse`

Suggested defaults:

- `data_dir`: unset, required before execution
- `file_pattern`: `*`
- `max_workers`: `1`
- `chunk_size`: unset, resolved from `max_workers` at runtime
- `reverse`: `false`

`max_workers` should accept either a positive integer or the token
`auto`. It may be stored as a string descriptor and normalized by the
runtime resolver.

`chunk_size` should allow an unset value and serialize that unset value
as CIF null (`.`).

Relative `data_dir` values should be resolved relative to the project
directory when the project has a saved path. This keeps saved projects
portable across Python and CLI workflows.

`reverse` should be represented by a boolean descriptor. If the current
descriptor layer has no dedicated boolean descriptor, one should be
introduced rather than storing boolean state as an arbitrary string.

Execution requirements for sequential fitting:

- exactly one project structure
- exactly one template project experiment
- project has a saved path
- at least one free parameter
- `sequential_fit.data_dir` is set and resolves to input data files

### 6. Add a `sequential_fit_extract` category

Sequential fits often need per-file metadata such as temperature,
pressure, field strength, or other scan coordinates. This information
is scientifically important and is also used by parameter-series plots.

The current `extract_diffrn` callback solves this in Python notebooks,
but a Python callable cannot be serialized in a portable way or invoked
from the generic CLI. Replace that callback with a persisted extraction
rule collection named `sequential_fit_extract`.

Suggested API:

```python
project.analysis.sequential_fit_extract.create(
    id='temperature',
    target='diffrn.ambient_temperature',
    pattern=r'^TEMP\s+([0-9.]+)',
)
project.analysis.sequential_fit_extract.create(
    id='pressure',
    target='diffrn.ambient_pressure',
    pattern=r'^PRESSURE\s+([0-9.]+)',
)
```

Each extraction rule contains:

- `id`
- `target`
- `pattern`
- `required`

`target` is a descriptor path relative to the template experiment, for
example `diffrn.ambient_temperature`. It replaces the weaker name
`param_suffix`, because the rule is assigning to a known descriptor and
to a known output CSV column. The initial supported targets should be
numeric descriptors under `experiment.diffrn`.

`pattern` is a regular expression applied to the input data file. The
first match is used. The regex must contain exactly one capture group,
and the captured text must be convertible to `float`.

`required` controls failure behavior. If `required` is false and the
pattern is not found, the target value is left empty for that file. If
`required` is true, the file result should be marked failed with a clear
error.

The corresponding CIF fragment is:

```cif
loop_
_sequential_fit_extract.id
_sequential_fit_extract.target
_sequential_fit_extract.pattern
_sequential_fit_extract.required
temperature diffrn.ambient_temperature "^TEMP\s+([0-9.]+)" false
pressure    diffrn.ambient_pressure    "^PRESSURE\s+([0-9.]+)" false
```

During sequential fitting, each worker should:

1. load the data file
2. apply all `sequential_fit_extract` rules
3. assign extracted values to the target descriptors on the worker
   experiment
4. include those values in the result row as `diffrn.<field>` columns
5. run the fit

Dataset replay should also apply `diffrn.*` values from
`analysis/results.csv` back onto the template experiment. This keeps:

```python
temperature = expt.diffrn.ambient_temperature
project.display.fit.series(param, versus=temperature)
```

working after a sequential fit and after reloading a saved project.

A runtime-only Python hook may still be useful for advanced notebook
workflows, but it is not part of the persisted CLI-ready contract
defined by this ADR.

### 7. Make help output instance-aware

Help rendering should support instance-aware filtering through a common
hook rather than special-casing `Analysis` alone. Class-level MRO
discovery remains the default, but an object may filter or extend the
properties and methods shown by `help()` based on its current state.

The implementation should add an optional help-filter hook to the common
help path used by `render_object_help()`, `GuardedBase.help()`, and
`CategoryItem.help()`. The exact function names can be chosen during
implementation, but the contract is that an instance can hide inactive
properties or methods from the discovered help rows without changing the
underlying Python object layout.

This is useful beyond fitting. Any object with conditional workflow
surfaces, backend-dependent options, or selected-type-specific
categories can use the same mechanism later.

For this ADR, `Analysis.help()` must use instance-aware filtering. It
should not only inspect class-level properties because mode-specific
categories are conditional workflow surfaces.

The help output should show common analysis properties and only the
category relevant to the active fit mode.

For `single` mode, help should show fitting configuration and the
`fit()` operation, but no joint or sequential category:

```text
Properties
fitting
display

Methods
fit()
show_fitting_mode_types()
```

For `joint` mode, help should additionally show:

```text
joint_fit
```

For `sequential` mode, help should additionally show:

```text
sequential_fit
sequential_fit_extract
```

Inactive mode categories should not be advertised in help output. Direct
access to an inactive mode category may either raise a clear mode error
or remain an internal implementation detail, but the public discovery
surface should only show categories relevant to the selected mode.

### 8. Serialize common and active mode-specific categories

Persist common fitting configuration in `analysis/analysis.cif` using a
category name that matches the new Python category:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode sequential
```

Persist only the active mode-specific category.

Sequential example:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode sequential

_sequential_fit.data_dir "data/d20_scan"
_sequential_fit.file_pattern "*.xye"
_sequential_fit.max_workers auto
_sequential_fit.chunk_size .
_sequential_fit.reverse true

loop_
_sequential_fit_extract.id
_sequential_fit_extract.target
_sequential_fit_extract.pattern
_sequential_fit_extract.required
temperature diffrn.ambient_temperature "^TEMP\s+([0-9.]+)" false
```

Joint example:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode joint

loop_
_joint_fit.experiment_id
_joint_fit.weight
sepd  0.7
nomad 0.3
```

Single example:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode single
```

Inactive mode-specific categories should not be serialized. This avoids
stale settings from a previously selected mode affecting CLI behavior
after reload. Because `sequential_fit_extract` is part of the
sequential workflow, it is serialized only when the active fitting mode
is `sequential`.

### 9. Restore mode before mode-specific settings

Deserialization order must be:

1. restore the common `fitting` category
2. read `_fitting.mode`
3. set `analysis.fitting_mode_type`
4. restore the active mode-specific category, if present
5. restore active child collections such as `sequential_fit_extract`
6. restore other analysis categories such as aliases and constraints

This mirrors the switchable-category restoration pattern used by
experiment categories: the active mode is known before mode-specific
fields are loaded.

### 10. The CLI runs the configured fit mode

The top-level CLI `fit` command should load the project and execute:

```python
project.analysis.fit()
```

It should not need a separate `fit-sequential` command for the normal
case. Sequential mode can be run from CLI because its required settings
are persisted in `analysis/analysis.cif`.

CLI options may override saved configuration for one invocation, for
example `--fitting-mode`, `--data-dir`, or `--max-workers`, but the
core model is that the saved project contains the selected mode and its
mode-specific settings.

## Consequences

### Positive

- `fit()` has one meaning: execute fitting.
- `fitting` has one meaning: common fitting configuration.
- Fit modes follow the same owner-level selection style as existing
  switchable categories.
- `joint_fit` and `sequential_fit` are visible only when relevant.
- Sequential fitting becomes runnable from CLI without a special Python
  method call.
- Sequential scan metadata becomes serializable and CLI-friendly through
  `sequential_fit_extract`.
- Instance-aware help becomes a reusable capability for conditional
  public surfaces.
- CIF structure is flat, explicit, and aligned with public API names.
- Mode-specific configuration can grow independently without polluting
  the common fitting category.

### Trade-offs

- Help rendering needs an instance-aware extension hook instead of pure
  class-MRO discovery.
- Switching fit mode changes the visible public surface of `Analysis`,
  which requires clear help and error messages.
- The new API intentionally breaks the current `analysis.fit` category
  and `fit_sequential(...)` method shape.
- Regex extraction rules cover common file-header metadata but are less
  flexible than an arbitrary Python callback.

### Compatibility

This ADR does not require runtime compatibility aliases.

The following public API shapes are replaced by the new design:

- `project.analysis.fit.minimizer_type`
- `project.analysis.fit.mode`
- `project.analysis.fit_sequential(...)`
- `project.analysis.joint_fit_experiments`

The replacement API is:

- `project.analysis.fitting.minimizer_type`
- `project.analysis.fitting_mode_type`
- `project.analysis.joint_fit`
- `project.analysis.sequential_fit`
- `project.analysis.sequential_fit_extract`

The `project.analysis.fit()` spelling remains, but it changes from a
callable category invocation to a real `Analysis` method.

## Alternatives Considered

### Keep `analysis.fit` as a callable category

Rejected.

It keeps the current naming ambiguity where `fit` is both a category and
an operation. It also leaves no clean place for mode-specific
configuration without either nesting categories under `fit` or adding
always-visible sibling categories.

### Put all mode-specific settings into `fitting`

Rejected.

This would make `fitting` contain `data_dir`, `max_workers`, and
joint-fit weights even when those fields do not apply to the active
mode. It weakens help output and makes CIF harder to read.

### Use `analysis.fitting.mode = 'sequential'` as the public selector

Rejected for the public API.

Although `_fitting.mode` is a good serialized field, the public selector
should follow the existing switchable-category owner style:

```python
project.analysis.fitting_mode_type = 'sequential'
```

The `fitting.mode` descriptor may exist internally or as a read-only
mirror for CIF, but users should not be asked to set it directly.

### Replace the `fitting` category object per fit mode

Rejected.

A concrete `SequentialFitting` object could expose sequential fields
directly, but switching by assigning a property on the object being
replaced creates stale-reference hazards:

```python
fitting = project.analysis.fitting
project.analysis.fitting_mode_type = 'sequential'
# fitting may now point to the old object
```

Keeping `fitting` stable and adding active sibling mode categories gives
better long-term API stability.

### Persist inactive mode-specific categories

Rejected.

Persisting inactive categories would make saved projects ambiguous for
CLI workflows. The selected mode should determine which mode-specific
category is authoritative.

## Deferred Work

- Optional `single_fit` category if single-mode-specific settings are
  introduced.
- A separate ADR for changing switchable category selectors globally
  from owner-level names such as `peak_profile_type` toward
  category-owned selectors such as `peak.profile_type`.
- The implementation and migration plan for replacing the current
  `fit` category and `fit_sequential(...)` method.
