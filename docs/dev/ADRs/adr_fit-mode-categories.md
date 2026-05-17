# ADR: Fit Mode Categories and Fit Execution API

## Status

Accepted and implemented.

## Date

2026-05-16

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

### Precedent: how `atom_site_aniso` handles a conditional category

The repository already has one closely related precedent: the
`atom_site_aniso` collection on a structure is only meaningful when at
least one `atom_site` has `adp_type` set to `Bani` or `Uani`. Its
implementation is instructive because it deliberately does **not** hide
the category from public discovery:

- `Structure.atom_site_aniso` is always present as a property and always
  appears in help output.
- When inactive, the collection is simply empty.
- A private `_sync_atom_site_aniso()` reconciles its contents from
  `atom_sites` whenever categories update: rows for anisotropic atoms
  are added, rows for isotropic or stale atoms are removed.
- CIF serialization naturally drops the empty loop, so there is no
  separate "serialize only when active" rule.

This is a viable alternative pattern for fit modes, and it is
intentionally rejected by this ADR (see _Alternatives Considered_). The
key differences that motivate a new pattern for fit modes are:

- `atom_site_aniso` rows are **derived** from a per-atom selector
  (`atom_site.adp_type`). For fit modes, the selector is owner-level
  (`Analysis.fitting_mode_type`) and the mode-specific categories
  (`joint_fit`, `sequential_fit`, `sequential_fit_extract`) carry
  independent, user-edited settings that cannot be derived from anything
  else.
- `atom_site_aniso` has one conditional category. Fit modes introduce a
  family of mutually exclusive categories; showing all of them as
  always-present empty surfaces would clutter `help()` output and invite
  users to configure a mode that is not active.
- For sequential fitting, configuration must be authoritative for CLI
  workflows. "Empty when inactive" is ambiguous on reload — was the mode
  never used, or was it cleared on a previous run?

Fit modes therefore call for an explicit **active-sibling** pattern (see
§2 and §7) rather than the auto-synced always-present pattern used by
`atom_site_aniso`.

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

Additional settings that apply to all fit modes can be added here later.
Verbosity remains a call-level or project-level concern and does not
need to be persisted in this category.

**Single source of truth.** `Analysis.fitting_mode_type` is the only
writable surface for the active mode, and the only place the mode is
stored at runtime. The CIF field `_fitting.mode_type` (§8) is
synthesized directly from `analysis.fitting_mode_type` at serialization
time and applied back to the selector on load. There is no mirror
descriptor on the `fitting` category. This keeps the runtime model free
of duplicated state.

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

Note that this is **not** the same mechanism as `peak_profile_type`.
`peak_profile_type` swaps the concrete class behind a single category
(`peak`); `fitting_mode_type` swaps which _sibling_ category
(`joint_fit` / `sequential_fit`) is active and visible. The `fitting`
category itself does not change shape. This is a new pattern — call it
the **active-sibling selector** — and it is documented here as a
first-class convention for owners that gate sibling categories on a
run-time choice. Future categories with the same shape should follow the
same naming and lifecycle rules.

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

When joint mode is active, `joint_fit` represents the experiments
participating in the joint fit. Auto-population and validation are
specified deterministically:

- On `fit()` in joint mode, any project experiment without a
  corresponding `joint_fit` row is added automatically with
  `weight = 1.0`.
- A `joint_fit` row whose `experiment_id` does not match any project
  experiment raises an error before fitting starts. It is not silently
  pruned, because that would mask user typos.
- Switching `fitting_mode_type` to `joint` does **not** auto-populate.
  Auto-population happens only at execution time so that intermediate
  configuration states are never silently mutated.

Execution requirements for joint fitting:

- at least two project experiments
- every joint-fit row references an existing experiment
- every participating experiment has one weight (after auto-population)

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

`max_workers` accepts either a positive integer or the token `auto`. It
is stored as a single descriptor and normalized to a positive integer by
a runtime resolver before being passed to the worker pool; consumers
never see the raw `auto` token. Whether the descriptor type is a
dedicated union descriptor or a string descriptor with validation is an
implementation detail.

`chunk_size` allows an unset value and serializes that unset value as
CIF null (`.`).

Relative `data_dir` values are resolved relative to the project
directory when the project has a saved path. For an unsaved project,
`fit()` raises a clear error if `data_dir` is relative — sequential
fitting requires either a saved project or an absolute `data_dir`. This
keeps saved projects portable across Python and CLI workflows and
rejects the ambiguous CWD-dependent case explicitly.

`reverse` is represented by a boolean descriptor. If the current
descriptor layer has no dedicated boolean descriptor, one is introduced
rather than storing boolean state as an arbitrary string. (Introducing a
boolean descriptor is a small prerequisite for this ADR; the
implementation plan should call it out separately.)

Execution requirements for sequential fitting:

- exactly one project structure
- exactly one template project experiment
- project has a saved path
- at least one free parameter
- `sequential_fit.data_dir` is set and resolves to input data files

### 6. Add a `sequential_fit_extract` category

Sequential fits often need per-file metadata such as temperature,
pressure, field strength, or other scan coordinates. This information is
scientifically important and is also used by parameter-series plots.

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
to a known output CSV column. Initial supported targets are numeric
descriptors under `experiment.diffrn`. `target` is validated at
`create()` time against the current template experiment and rejected if
it does not resolve to a writable numeric descriptor; this fails fast
rather than waiting until the first sequential run.

`pattern` is a regular expression applied **line by line** to the input
data file (`re.search` on each line until the first match). The regex
must contain exactly one capture group, and the captured text must be
convertible to `float`. To bound worst-case behaviour on untrusted CIF
input, patterns are validated at `create()` time and rejected if they
contain backreferences or nested quantifiers; a future revision may
adopt a timeout-based engine.

`required` controls failure behavior. If `required` is false and the
pattern is not found, the target value is left empty for that file. If
`required` is true, the file result is marked failed with a clear error.

Extracted values are written to `analysis/results.csv` under the column
name `diffrn.<field>` (dots are preserved). Downstream consumers such as
`display.fit.series(...)` must use that exact column name.

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
temperature = 'diffrn.ambient_temperature'
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
implementation, but the contract is:

- The hook can only **hide** members that class-MRO discovery already
  produced; it cannot inject members that do not exist on the class.
  This keeps `help()` consistent with `dir()` and IDE completion.
- Hidden members remain programmatically accessible. Direct attribute
  access to an inactive mode-specific category (e.g. reading
  `analysis.sequential_fit` while in `joint` mode) returns the
  underlying object unchanged. Mutating it does not raise, but its
  values are not serialized while the mode is inactive (§8). This avoids
  surprising errors in notebooks where a user is iterating on
  configuration before switching modes.

This hook is useful beyond fitting. Any object with conditional workflow
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
_fitting.mode_type sequential
```

Persist only the active mode-specific category.

Sequential example:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode_type sequential

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
_fitting.mode_type joint

loop_
_joint_fit.experiment_id
_joint_fit.weight
sepd  0.7
nomad 0.3
```

Single example:

```cif
_fitting.minimizer_type "lmfit (leastsq)"
_fitting.mode_type single
```

Inactive mode-specific categories should not be serialized. This avoids
stale settings from a previously selected mode affecting CLI behavior
after reload. Because `sequential_fit_extract` is part of the sequential
workflow, it is serialized only when the active fitting mode is
`sequential`.

### 9. Restore mode before mode-specific settings

Deserialization order must be:

1. restore the common `fitting` category
2. read `_fitting.mode_type`
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
example `--fitting-mode`, `--data-dir`, or `--max-workers`, but the core
model is that the saved project contains the selected mode and its
mode-specific settings. CLI overrides are **per-invocation only** and
are never written back to the project on disk. Persisting a new mode or
new settings requires an explicit save step.

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

This ADR does not require runtime compatibility aliases. Consistent with
the project's beta-stage policy of no legacy shims, loading an old
project that still contains `_fit.minimizer_type`, `_fit.mode`, or
`_joint_fit_experiments.*` raises a clear error pointing at the new CIF
names. There is no silent auto-migration on load.

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

### Name the selector `fit_mode_type`

Rejected.

`fit_mode_type` and `show_fit_mode_types()` would imply a public
`fit_mode` category, which does not exist. The project convention is
that switchable-category selector names begin with the public category
name (`peak_profile_type` for `peak`, `background_type` for
`background`). For a selector hosted on `Analysis` that gates the
`fitting`-related siblings, `fitting_mode_type` is the closest fit.

### Mirror `atom_site_aniso`: always present, auto-synced, empty when inactive

Rejected for fit modes (see _Context \u2014 Precedent_ for the
comparison).

`atom_site_aniso` keeps the category always visible and derives its
contents from a per-atom selector. Applying the same shape to fit modes
would mean `joint_fit`, `sequential_fit`, and `sequential_fit_extract`
always appear in `help()` and CIF, with auto-sync rules that try to
reconcile them with `fitting_mode_type`.

This is rejected because:

- The mode-specific categories carry independent user-edited state that
  cannot be derived from any other object.
- Three always-visible mutually exclusive categories make `help()`
  output and CIF files harder to read than a single active sibling.
- For CLI workflows, \"empty category\" and \"unused mode\" must be
  distinguishable on reload; explicit serialization of only the active
  category preserves that distinction.

The precedent is still informative: `atom_site_aniso` shows that the
codebase accepts non-uniform category visibility patterns when they fit
the underlying data model. The active-sibling pattern introduced here is
the right tool for an owner-level mode selector.

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

### Use `analysis.fitting.mode` as the public selector

Rejected for the public API.

Although `_fitting.mode_type` is the CIF spelling, the public selector
should follow the existing switchable-category owner style:

```python
project.analysis.fitting_mode_type = 'sequential'
```

A separate `fitting.mode` descriptor on the runtime `fitting` category
is also rejected: it would duplicate state already held by
`fitting_mode_type`. `_fitting.mode_type` is synthesized at
serialization time instead of being mirrored on a runtime object.

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

## Follow-up Questions

The core design in this ADR is implemented. The questions below are
follow-up design topics that may need future ADRs if behaviour changes.

### Architectural / API

- **Direct access to inactive mode categories.** \u00a77 specifies the
  lenient behaviour: reading `analysis.sequential_fit` in `joint` mode
  returns the underlying object, mutation does not raise, but values are
  not serialized. Open: is this the right trade-off, or should access
  raise a `ModeError` to prevent silent data loss on save?

### Data model

- **`joint_fit` and experiment lifecycle.** Stale rows raise at `fit()`
  time. Open: should `joint_fit` also listen for experiment-collection
  changes and prune (or warn) on experiment deletion, or remain passive
  until execution?
- **`joint_fit` weight bounds.** Default weight is `1.0`. Open: is
  `weight = 0` allowed (effective exclusion), and what is the upper
  bound, if any? Should weights share the validator used by free
  parameters?
- **`sequential_fit_extract` target scope.** Targets are initially
  numeric descriptors under `experiment.diffrn`. Open:
  - are nested descriptors (`diffrn.foo.bar`) allowed, or only one
    level?
  - is the same target reachable from two rules (last wins, error, or
    merge)?
  - how is the supported-prefix list extended when new
    sample-environment categories appear?
- **`sequential_fit_extract` failure aggregation.** A failed `required`
  rule marks the file failed. Open: does one failure abort the whole
  sequential run, just exclude that file from results, or apply a
  max-failure threshold?
- **Extraction caching.** Files may be re-read on resume or partial
  replay. Open: is extraction re-run each time, or cached alongside
  results in `analysis/results.csv`?

### Persistence & CLI

- **CIF round-trip for `auto` `max_workers`.** The on-disk value is the
  token `auto`. Open: when CLI overrides resolve `auto` to a concrete
  integer for one run, is that integer ever written back, or is the
  token always preserved on disk regardless of runtime resolution?
- **Serialization order for `_fitting.*`.** \u00a79 specifies
  deserialization order. Open: pin serialization order too (mode first,
  then `minimizer_type`, then mode-specific siblings) so generated files
  are stable for diffing?
- **Failure mid-sequential-run.** Open: if `fit()` fails partway through
  a sequential scan, what is the state of `analysis/results.csv` and the
  persisted `sequential_fit` \u2014 resumable, discarded, or left as-is
  for manual recovery?
- **CLI override of `sequential_fit_extract`.** Overrides are listed for
  `--fitting-mode`, `--data-dir`, `--max-workers`. Open: are extraction
  rules overridable from the CLI (for example
  `--extract id=temperature:target=...:pattern=...`), or only via the
  project file?

### Help & discovery

- **`dir()` consistency.** The hook hides members from `help()` only.
  Open: should `dir(analysis)` likewise hide inactive categories, or
  always reflect the full class surface (affects tab completion)?

### Scope

- **`single` mode \"future-proofing.\"** \u00a73 leaves `single_fit` as
  optional future work. Open: is there any current setting that would
  qualify \u2014 for example, per-experiment selection when a project
  contains multiple experiments and the user wants to run `single`
  against one of them?
- **Migration error timing.** Compatibility says loading old CIF raises.
  Open: does \"raises\" mean at load of `project.cif`, or at first
  access of `analysis`? This affects how users discover the break and
  whether a project can be partially loaded for inspection.

## Deferred Work

- Optional `single_fit` category if single-mode-specific settings are
  introduced.
- A separate ADR for changing switchable category selectors globally
  from owner-level names such as `peak_profile_type` toward
  category-owned selectors such as `peak.profile_type`.
