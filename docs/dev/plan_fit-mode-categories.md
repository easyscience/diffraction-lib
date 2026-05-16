# Implementation Plan: Fit Mode Categories and Fit Execution API

**ADR:**
[adr_fit-mode-categories.md](ADR-suggestions/adr_fit-mode-categories.md)
**Branch:** `feature/fit-mode-categories` **Status:** Phase 2 completed

## Scope

This plan implements only the parts of the ADR that are fully specified.
Items still in the ADR's _Open Questions_ section are explicitly out of
scope:

- Help-filter hook surface beyond `GuardedBase` (no `CategoryItem` hook
  needed in this step).
- `dir()` consistency with `help()` filtering.
- `single_fit` category.
- After each Phase 1 step, **stage the listed files with explicit paths
  and commit locally** using the suggested commit message before
  starting the next step. Do not batch multiple plan steps into one
  commit. Do not stage unrelated working changes.
- After completing all Phase 1 steps, **stop and ask the user to
  review** before starting Phase 2.
- If implementation uncovers a serious requirement, risk, design issue,
  or scope change not covered by this plan or the ADR, stop and ask the
  user before proceeding. Record the unresolved issue in this file when
  useful.
- Do not delete or replace existing functionality silently. Each step
  below lists what is removed and what replaces it; do not add removals
  beyond that list without confirmation.

## Status checklist

### Phase 1 — Implementation

- [x] Step 0: Create the implementation branch
- [x] Step 1: Add `BoolDescriptor` to `core/variable.py`
- [x] Step 2: Introduce the `fitting` category (replaces `fit` config
      surface; non-callable, no `mode` field)
- [x] Step 3: Wire `Analysis.fitting`, `Analysis.fitting_mode_type`,
      `Analysis.show_fitting_mode_types()`, and
      `Analysis._set_fitting_mode_type()`
- [x] Step 4: Rename `joint_fit_experiments` → `joint_fit`, rename item
      field `id` → `experiment_id`
- [x] Step 5: Add the `sequential_fit` category (single item)
- [x] Step 6: Add the `sequential_fit_extract` category (collection)
- [x] Step 7: Make `Analysis.fit()` a real method dispatching on
      `fitting_mode_type`
- [x] Step 8: Migrate sequential execution to read from `sequential_fit`
      / `sequential_fit_extract` (drop `fit_sequential()` and the
      `extract_diffrn` Python callback)
- [x] Step 9: Add `joint_fit` auto-population and validation in `fit()`
- [x] Step 10: Add the instance-aware help-filter hook on `GuardedBase`
      and wire `Analysis._help_filter`
- [x] Step 11: Update CIF serialization to synthesize
      `_fitting.mode_type` and serialize only the active mode-specific
      category
- [x] Step 12: Update CIF deserialization order and add the old-format
      error
- [x] Step 13: Update tutorials, docs, and `__init__.py` exports; run
      `pixi run fix` to regenerate package-structure docs
- [x] Phase 1 review gate — stop and request user review

### Phase 2 — Verification

- [x] Step 14: Tests and project-wide verification

## Architecture decisions already locked

These flow directly from the ADR. The implementing agent must not
revisit them:

- The public selector is **`fitting_mode_type`**. Reject any alternative
  spelling.
- `fitting.mode` does **not** exist as a runtime descriptor.
  `_fitting.mode_type` in CIF is synthesised from
  `Analysis.fitting_mode_type` on save and applied back on load.
- `fitting` is **not** callable. Calling `project.analysis.fitting(...)`
  must raise the standard `TypeError` (do not add an explicit
  `__call__`).
- `project.analysis.fit()` is an `Analysis` method, not a category.
- Mode-specific categories (`joint_fit`, `sequential_fit`,
  `sequential_fit_extract`) are direct children of `Analysis`.
- Inactive mode categories remain programmatically accessible (lenient
  access; \u00a77 of the ADR). They are hidden from `help()` and not
  serialized.
- Loading an old CIF that still contains `_fit.*`,
  `_joint_fit_experiments.*`, or related stale categories raises a clear
  error on first access of `analysis` (no silent auto-migration).

---

## Phase 1 steps

Each step lists: files to change, what to do, what to remove, and a
suggested commit message. Stage with explicit paths and commit before
moving to the next step.

### Step 0: Create the implementation branch

**Tasks**

1. Verify the working tree is clean (`git status`). If there are
   unrelated dirty files, stop and ask the user.
2. Create and switch to the implementation branch:

   ```bash
   git switch -c feature/fit-mode-categories
   ```

3. Do not push the branch. All commits are local until the user asks for
   a push.

No commit for this step.

### Step 1: Add `BoolDescriptor`

**Files**

- `src/easydiffraction/core/variable.py`

**Why first.** `sequential_fit.reverse` requires a real boolean
descriptor with CIF binding. Today the codebase only has
`_BOOL_SPEC_TEMPLATE` used internally by `GenericParameter.free`.

**Reference reading.** Open `src/easydiffraction/core/variable.py` and
read, in order, `GenericDescriptorBase`, `GenericStringDescriptor`, and
`StringDescriptor`. The two new classes are exact structural copies of
these two, with `str` replaced by `bool` and `DataTypes.STR` replaced by
`DataTypes.BOOL`. Do not invent any new validation hook — reuse what
`GenericStringDescriptor` already calls.

**Tasks**

1. Add `GenericBoolDescriptor(GenericDescriptorBase)` immediately after
   `GenericStringDescriptor` in the same file. Implement only the
   members that `GenericStringDescriptor` overrides; for every other
   member, defer to the base class. Specifically:
   - `__init__(self, name: str, description: str = '', value_spec: AttributeSpec | None = None) -> None`
     — default `value_spec` to
     `AttributeSpec(data_type=DataTypes.BOOL, default=False)` if `None`
     is passed.
   - `value` property (getter and setter) returning `bool`, using the
     same `self._value_spec.validated(...)` call site as
     `GenericStringDescriptor.value.setter` does (look for that exact
     call in the file and copy it verbatim, swapping the attribute
     name).
2. Add `BoolDescriptor(GenericBoolDescriptor)` immediately after
   `StringDescriptor`. Mirror `StringDescriptor` line-for-line, only
   changing the parent class.
3. Serialization contract:
   - On write, emit `true` for `True` and `false` for `False`.
   - On read, accept `true`, `True`, `TRUE`, `false`, `False`, `FALSE`
     (case-insensitive). Treat the CIF null token `.` as "keep the
     descriptor's current default" (i.e. do not raise).
   - Any other token raises through the existing validator path that
     `StringDescriptor` already uses for invalid values.
   - If the existing `StringDescriptor` CIF round-trip is handled by a
     shared helper rather than per-class code, route through that same
     helper and add the bool coercion there. Do not duplicate logic.
4. Do **not** change existing `GenericParameter.free` handling. The new
   descriptor is additive.
5. If, after reading the file, the structural copy turns out to require
   more than a one-class addition (for example, the CIF handler dispatch
   is type-keyed elsewhere and needs a new branch), stop and ask the
   user before adding cross-cutting changes.

**Suggested commit**

```
Add BoolDescriptor for CIF-bound boolean values
```

### Step 2: Introduce the `fitting` category

**Files**

- new package: `src/easydiffraction/analysis/categories/fitting/`
  - `__init__.py`
  - `factory.py` (delegates to `FactoryBase`, mirroring
    `categories/fit/factory.py`)
  - `default.py`
- `src/easydiffraction/analysis/__init__.py` — the canonical place where
  existing analysis categories are explicitly imported. Verify this by
  reading the file and locating the existing
  `from easydiffraction.analysis.categories.fit ...` import; add the
  parallel `from ...categories.fitting ...` import next to it.

**Tasks**

1. Create `Fitting(CategoryItem)` registered via
   `@FittingFactory.register`. Tag: `'default'`.
2. Fields:
   - `minimizer_type` — `StringDescriptor` with the same enum and CIF
     handler as today's `Fit.minimizer_type`, but the CIF name becomes
     `_fitting.minimizer_type`.
3. **Do not** add a `mode` field. The mode lives on `Analysis` only.
4. The class must not be callable. Do not add `__call__`.
5. Add a `Fitting.as_cif` property returning the
   `_fitting.minimizer_type` key-value line(s). Mirror the structure
   used by `Fit.as_cif` today but with the new prefix.
6. Add a `Fitting.from_cif(block)` method that reads
   `_fitting.minimizer_type`. It must ignore `_fitting.mode_type` (that
   is consumed at the analysis level — see Step 12).
7. Update package `__init__.py` to explicitly import the new class so
   the factory registers (per project rule: no pkgutil/importlib
   auto-discovery).

**Do not yet** remove the old `fit` category package. Step 7 removes it.
Keeping both packages temporarily lets earlier steps compile.

**Suggested commit**

```
Add fitting category replacing fit configuration surface
```

### Step 3: Wire `Analysis.fitting` and the mode selector

**Files**

- `src/easydiffraction/analysis/analysis.py`

**Tasks**

1. In `Analysis.__init__`, create
   `self._fitting = FittingFactory.create(FittingFactory.default_tag())`.
   Keep the existing `self._fit = FitFactory.create(...)` for now; Step
   7 removes it.
2. Add `self._fitting_mode_type: FitModeEnum = FitModeEnum.default()`.
3. Add public surface on `Analysis`:
   - `@property fitting` → returns `self._fitting` (read-only).
   - `@property fitting_mode_type` → returns
     `self._fitting_mode_type.value` (str).
   - `@fitting_mode_type.setter` → validates against `FitModeEnum`, then
     sets `self._fitting_mode_type` and prints the usual
     `console.paragraph(...)` confirmation used by other
     switchable-category setters. Reject unknown values with the
     standard `log.warning(...)` early return (mirror
     `peak_profile_type` setter).
   - `def show_fitting_mode_types(self) -> None` — print a table listing
     all members of `FitModeEnum`, marking the current with `*` and
     including each member's `description()`. Do **not** filter modes
     based on project state (the ADR says sequential must be shown even
     with one experiment).
   - `def _set_fitting_mode_type(self, value: str) -> None` — silent
     setter used by CIF restore; validates and sets without console
     output.
4. **`FitModeEnum` location decision (locked).** Keep `FitModeEnum` at
   `src/easydiffraction/analysis/categories/fit/enums.py` for this step
   (the old `fit` package still exists). In Step 7, move the file to
   `src/easydiffraction/analysis/enums.py` as part of removing the old
   package. Do not pre-move it here.
5. Ensure `FitModeEnum.description()` returns a short, one-line string
   per member. If missing, add it using these exact texts:
   - `single` — `'Fit one experiment at a time.'`
   - `joint` —
     `'Fit several experiments together with shared parameters.'`
   - `sequential` —
     `'Fit one experiment against a series of data files.'`

**Do not** yet make `Analysis.fit()` a method. That happens in Step 7.
The current `Analysis.fit` property still returns the old `Fit` category
at this point.

**Suggested commit**

```
Add fitting_mode_type selector and fitting accessor on Analysis
```

### Step 4: Rename `joint_fit_experiments` → `joint_fit`

**Files**

- rename package directory:
  `src/easydiffraction/analysis/categories/joint_fit_experiments/` →
  `src/easydiffraction/analysis/categories/joint_fit/`
- inside, update class names:
  - `JointFitExperiment` → `JointFitItem`
  - `JointFitExperiments` → `JointFitCollection` (locked; do not rename
    to anything else, even if other collections in the repo use a
    different suffix)
- field rename inside `JointFitItem`:
  - `id` → `experiment_id`
  - CIF name `_joint_fit_experiment.id` → `_joint_fit.experiment_id`
  - CIF name `_joint_fit_experiment.weight` → `_joint_fit.weight`
- `src/easydiffraction/analysis/analysis.py`:
  - rename `self._joint_fit_experiments` → `self._joint_fit`
  - rename property `joint_fit_experiments` → `joint_fit`
- `src/easydiffraction/io/cif/serialize.py`:
  - update references in `analysis_to_cif` and `analysis_from_cif`
- any test, tutorial, or doc references — grep the entire repo:

  ```bash
  grep -rIn 'joint_fit_experiment' src/ tests/ docs/ tutorials/ tools/
  ```

  Update every match. Per the ADR's Compatibility section, no runtime
  aliases are added.

**Tasks**

1. Move files; update imports.
2. Rename classes and fields.
3. Update CIF handlers to new names.
4. Update CIF loop column order: `experiment_id`, then `weight`.
5. The collection key remains the experiment id; the public indexing
   form is `joint_fit['sepd']`, where `'sepd'` matches `experiment_id`.
6. Keep the existing
   `RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$')` on
   `experiment_id`.
7. Keep `weight` as `NumericDescriptor` with the existing
   `RangeValidator()`. Weight bounds beyond non-negative are an open
   question; do not change them in this step.

**Suggested commit**

```
Rename joint_fit_experiments category to joint_fit
```

### Step 5: Add the `sequential_fit` category

**Files**

- new package: `src/easydiffraction/analysis/categories/sequential_fit/`
  - `__init__.py`
  - `factory.py`
  - `default.py`
- `src/easydiffraction/analysis/analysis.py`

**Tasks**

1. Define `SequentialFit(CategoryItem)` (single-item, not a collection)
   registered via `@SequentialFitFactory.register`.
2. Fields and CIF handlers:
   - `data_dir`: `StringDescriptor`, default unset (empty string). CIF:
     `_sequential_fit.data_dir`.
   - `file_pattern`: `StringDescriptor`, default `'*'`. CIF:
     `_sequential_fit.file_pattern`.
   - `max_workers`: `StringDescriptor` validated by
     `RegexValidator(pattern=r'^(auto|[1-9]\d*)$')`. Default `'1'`. CIF:
     `_sequential_fit.max_workers`. The on-disk value is preserved
     verbatim; resolution to an int happens only at runtime in Step 8.
   - `chunk_size`: nullable integer field. CIF:
     `_sequential_fit.chunk_size`. Before writing this field,
     **investigate first**: grep for `allow_none` in
     `src/easydiffraction/core/validation.py` and for nullable
     descriptor precedents elsewhere in `src/easydiffraction/`.
     - If a nullable numeric pattern already exists (for example a
       `RangeValidator(allow_none=True)` or a dedicated descriptor),
       reuse it.
     - If no precedent exists, implement `chunk_size` as a
       `StringDescriptor` validated by
       `RegexValidator(pattern=r'^([1-9]\d*|\.)$')`, default `'.'`, and
       convert to `int | None` at runtime in Step 8 (`.` → `None`). Note
       this fallback in the commit message. Do not introduce a new
       nullable descriptor class as part of this step — escalate to the
       user if you think one is needed.
   - `reverse`: `BoolDescriptor` (Step 1), default `False`. CIF:
     `_sequential_fit.reverse`.
3. Add `SequentialFit.as_cif` and `SequentialFit.from_cif(block)`
   following the existing single-item category convention.
4. In `Analysis.__init__`, create
   `self._sequential_fit = SequentialFitFactory.create(...)` and expose
   it as a read-only property `sequential_fit`. Mutation while in joint
   or single mode is allowed but values are not serialized (see Steps 10
   and 11).
5. Add the helper `Analysis._resolve_sequential_data_dir() -> Path`
   that:
   - returns the descriptor value verbatim if it is an absolute path,
   - returns `project_path / data_dir` if the project has a saved path
     and the value is relative,
   - **raises** with a clear message for an unsaved project with a
     relative value. Use the same exception path that the current
     `fit_sequential(...)` uses when the project path is missing — grep
     `src/easydiffraction/analysis/` for `project path` or equivalent
     and reuse that exception type. Do not introduce a new exception
     class.

**Suggested commit**

```
Add sequential_fit category with persisted scan settings
```

### Step 6: Add the `sequential_fit_extract` category

**Files**

- new package:
  `src/easydiffraction/analysis/categories/sequential_fit_extract/`
  - `__init__.py`
  - `factory.py`
  - `default.py`
- `src/easydiffraction/analysis/analysis.py`

**Tasks**

1. Define `SequentialFitExtractItem(CategoryItem)` and
   `SequentialFitExtractCollection(CategoryCollection)`, registered via
   the factory pattern.
2. Item fields and CIF handlers:
   - `id`: `StringDescriptor`, primary key for the collection. CIF:
     `_sequential_fit_extract.id`. Reuse the
     `RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$')`.
   - `target`: `StringDescriptor`. CIF:
     `_sequential_fit_extract.target`. Structural validation at
     `create()` time:
     - exactly two dotted segments
     - first segment is the literal `diffrn`
     - second segment matches `^[A-Za-z_][A-Za-z0-9_]*$` Implement
       structural validation as a small helper
       `_validate_extract_target_shape(value: str) -> None` next to the
       class. Do **not** validate that the second segment is a real
       numeric attribute on a template experiment at `create()` time —
       extraction rules may be created before any experiment exists.
       Attribute-existence validation happens instead in Step 8,
       immediately before sequential execution starts (when a template
       experiment is guaranteed to exist). Nested targets beyond one
       level are an explicit ADR open question — reject them at the
       shape-check step.
   - `pattern`: `StringDescriptor`. CIF:
     `_sequential_fit_extract.pattern`. Validate at `create()` time only
     that:
     - the regex compiles via `re.compile(value)`,
     - it has exactly one capture group
       (`re.compile(value).groups == 1`). Do **not** add the static
       check for backreferences or nested quantifiers. Defending against
       ReDoS is an ADR open question; the project trust boundary for CIF
       input is already "user-controlled," so this is acceptable for v1.
       Record this decision in the step's commit message body.
   - `required`: `BoolDescriptor` (Step 1), default `False`. CIF:
     `_sequential_fit_extract.required`.
3. The collection's `create(...)` method validates `target` and
   `pattern` synchronously and raises before the row is added.
4. In `Analysis.__init__`, instantiate
   `self._sequential_fit_extract = SequentialFitExtractCollection()` and
   expose as a read-only property `sequential_fit_extract`.

**Do not** implement extraction caching, max-failure thresholds, or
nested targets. Each is an explicit ADR open question.

**Suggested commit**

```
Add sequential_fit_extract category for scan metadata rules
```

### Step 7: Make `Analysis.fit()` a real method (entry-point only)

**Scope of this step.** Step 7 only re-routes how fitting is invoked. It
introduces `Analysis.fit()` and the private dispatch helpers, removes
the old `fit` category and `fit_sequential(...)` entry point, and moves
`FitModeEnum`. It does **not** yet rewrite `sequential.py` to consume
`sequential_fit` / `sequential_fit_extract` — that is Step 8. The
temporary contract between Steps 7 and 8 is that `_run_sequential` calls
the existing sequential entry point from `sequential.py` with arguments
read from `analysis.sequential_fit` (and `extract_diffrn=None`). The old
sequential code path still accepts the callback parameter at the end of
Step 7; Step 8 removes it.

**Reference reading.** Before editing, open:

- `src/easydiffraction/analysis/categories/fit/default.py` — read
  `Fit.__call__` (line ~205) and `Fit.run(...)`. Note what `self`
  members it reads (likely `self._project` or similar back-pointer) and
  what other `Analysis`-level state it touches.
- `src/easydiffraction/analysis/analysis.py` — read the existing
  `fit_sequential(...)` (line ~745) and the current `_run_fit(...)`
  (line ~451). These three call sites are the prior art for the new
  dispatch helpers.

**Files**

- `src/easydiffraction/analysis/analysis.py`
- remove package: `src/easydiffraction/analysis/categories/fit/`
- move `enums.py` from that package to
  `src/easydiffraction/analysis/enums.py` and update imports
- update `src/easydiffraction/io/cif/serialize.py` to drop references to
  `analysis.fit` as a config category (the actual `_fitting.*` write
  happens in Step 11)

**Tasks**

1. Add three private methods on `Analysis` with these exact signatures:

   ```python
   def _run_single(self) -> None: ...
   def _run_joint(self) -> None: ...
   def _run_sequential(self) -> None: ...
   ```

   - Copy the body of `Fit.__call__`'s single-mode branch into
     `_run_single`, replacing references to `self` (the `Fit` instance)
     with references to `self` (the `Analysis` instance) and
     `self.fitting` for `minimizer_type`. If `Fit.__call__` reads other
     `Analysis` state via a back-pointer, switch to the direct `self.`
     form.
   - Copy the joint-mode branch into `_run_joint` the same way.
   - `_run_sequential` is the smallest method: it reads `data_dir`,
     `file_pattern`, `max_workers`, `chunk_size`, `reverse` from
     `self.sequential_fit`, resolves `data_dir` via
     `self._resolve_sequential_data_dir()` (Step 5), and calls the
     existing private entry point in
     `src/easydiffraction/analysis/sequential.py` (the one that
     `fit_sequential(...)` currently delegates to via `_fit_seq`). Pass
     `extract_diffrn=None` for now — Step 8 removes that parameter from
     the callee.

2. Define `Analysis.fit(self) -> None`:

   ```python
   def fit(self) -> None:
       mode = self._fitting_mode_type
       if mode is FitModeEnum.SINGLE:
           self._run_single()
       elif mode is FitModeEnum.JOINT:
           self._run_joint()
       elif mode is FitModeEnum.SEQUENTIAL:
           self._run_sequential()
       else:  # pragma: no cover — enum exhausted
           raise ValueError(f'Unknown fit mode: {mode!r}')
   ```

   Use `is` against the enum members, not string comparison.

3. Remove the existing `fit` property on `Analysis`. The new `fit`
   method replaces it. Remove `Analysis.fit_sequential(...)` entirely
   (no alias).
4. Move `FitModeEnum` from `analysis/categories/fit/enums.py` to
   `analysis/enums.py`. Update every import.
5. Delete the `categories/fit/` package.
6. Repository-wide rewrite:

   ```bash
   grep -rIn 'analysis\.fit\.\|analysis\.fit_sequential\|categories\.fit\b' \
       src/ tests/ docs/ tutorials/ tools/
   ```

   Apply these mechanical replacements:
   - `analysis.fit.minimizer_type` → `analysis.fitting.minimizer_type`
   - `analysis.fit.mode = '<x>'` → `analysis.fitting_mode_type = '<x>'`
   - `analysis.fit_sequential(data_dir=..., ...)` → set the equivalent
     fields on `analysis.sequential_fit`, then call `analysis.fit()`.
     For tutorials with an `extract_diffrn` callback, leave a TODO
     comment pointing at Step 8 — do not rewrite the callback into rules
     here; Step 8 owns that migration.

7. Do **not** touch `sequential.py` in this step beyond what is
   necessary for the import path to compile. The callback parameter
   still exists on the callee.

**Suggested commit**

```
Replace fit category with Analysis.fit() method
```

### Step 8: Migrate sequential execution to persisted settings

**Scope of this step.** Step 8 rewrites the body of
`src/easydiffraction/analysis/sequential.py` so that all per-file
metadata extraction comes from `analysis.sequential_fit_extract` instead
of the Python `extract_diffrn` callback. After this step,
`_run_sequential` (from Step 7) no longer passes `extract_diffrn=None`,
and the callee no longer accepts that parameter.

**Files**

- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/sequential.py`
- any tutorial left with a `TODO: Step 8` marker from Step 7

**Tasks**

1. Remove the `extract_diffrn` parameter from the public entry point in
   `sequential.py` (the function previously called `_fit_seq` or
   similar). Adjust `_run_sequential` in `analysis.py` accordingly.
2. Just before launching the worker pool, validate every
   `sequential_fit_extract` row's `target` against the template
   experiment's `diffrn` category: the second segment must be an
   existing numeric descriptor attribute on `experiment.diffrn`. Raise a
   clear error if any rule references an unknown attribute. This is the
   second half of the validation deferred from Step 6.
3. In the worker function (the one currently consuming `extract_diffrn`
   near `sequential.py` line ~853), for each data file:
   - read the file line by line
   - for each `sequential_fit_extract` row, apply
     `re.search(pattern, line)` to each line in order; stop at the first
     match for that rule
   - if matched, convert the captured group to `float`; assign it to
     `experiment.diffrn.<second-segment>` on the worker experiment, and
     record the value in the result row under the column name
     `diffrn.<second-segment>` (dots preserved)
   - if not matched and the rule has `required=True`, mark the file's
     result as failed with a clear error message and continue with the
     next file. Do **not** abort the whole run. (Whole-run abort and
     max-failure threshold are open questions.)
   - if not matched and `required=False`, leave the column empty for
     that file.
4. Resolve `max_workers` at runtime:
   - `'auto'` → `os.cpu_count() or 1`
   - any other valid string → `int(value)`
   - The token on disk is unchanged regardless of runtime resolution.
5. Resolve `chunk_size` at runtime: if stored as a nullable numeric,
   `None` means "let the executor decide". If stored as a string per the
   Step 5 fallback, treat `'.'` as `None` and any other value as
   `int(value)`.
6. Apply `reverse` by reversing the sorted file list before chunking.
7. Dataset replay (loading `analysis/results.csv` back onto the template
   experiment for `display.fit.series(...)`) keeps its existing logic
   but now reads `diffrn.*` columns produced by the extract rules.
8. Rewrite tutorial `TODO: Step 8` markers from Step 7: convert each
   `extract_diffrn` callback into one or more
   `analysis.sequential_fit_extract.create(...)` calls before the
   `analysis.fit()` call.

**Out of scope (open questions, do not implement):**

- Resume after a mid-run failure.
- Extraction caching.
- CLI overrides of extraction rules.

**Suggested commit**

```
Drive sequential fitting from sequential_fit settings
```

### Step 9: `joint_fit` auto-population and validation

**Files**

- `src/easydiffraction/analysis/analysis.py`

**Tasks**

1. In the `joint` branch of `Analysis.fit()`, before delegating to
   `_run_joint`, run a deterministic prepare step:
   - For every experiment in the project that does not already have a
     row in `analysis.joint_fit`, add a row with `experiment_id=<id>`
     and `weight=1.0`.
   - For every existing row whose `experiment_id` does not match a
     project experiment, **raise** with a clear message naming the
     offending id. Do not silently prune.
2. Switching `fitting_mode_type` to `joint` must **not** mutate
   `joint_fit`. Auto-population happens only at execution time.
3. Add execution checks (raise before delegating to the joint runner):
   - project has at least two experiments,
   - every participating experiment has exactly one row after
     auto-population.
4. Do not modify the joint runner itself; this step only adds the
   preparation/validation wrapper.

**Suggested commit**

```
Auto-populate joint_fit rows and validate before fitting
```

### Step 10: Help-filter hook on `GuardedBase`

**Files**

- `src/easydiffraction/core/guard.py`
- `src/easydiffraction/analysis/analysis.py`

**Hook signature (locked).**

```python
def _help_filter(
    self,
    properties: list[str],
    methods: list[str],
) -> tuple[list[str], list[str]]:
    ...
```

Both lists contain attribute names as strings. The hook returns a
`(properties, methods)` tuple. Order in the returned lists is irrelevant
— `GuardedBase.help()` re-sorts before rendering.

**Tasks**

1. In `GuardedBase.help()`, after class-MRO discovery produces the
   property-name list and method-name list, look up `_help_filter` on
   the instance via `getattr(self, '_help_filter', None)`. If callable,
   invoke it with the two lists. Default behaviour (no hook):
   pass-through.
2. The hook may only **hide** members; it must not append. After
   invoking the hook, assert that
   `set(returned_properties) <= set(input_properties)` and the same for
   methods. On violation, raise `RuntimeError` with a clear message
   naming the offending subclass.
3. Implement `Analysis._help_filter(properties, methods)`:
   - Always keep: `fitting`, `display`, `aliases`, `constraints`,
     `joint_fit`, `sequential_fit`, `sequential_fit_extract`, plus other
     existing analysis properties.
   - When `fitting_mode_type == 'single'`: hide `joint_fit`,
     `sequential_fit`, `sequential_fit_extract`.
   - When `fitting_mode_type == 'joint'`: hide `sequential_fit`,
     `sequential_fit_extract`.
   - When `fitting_mode_type == 'sequential'`: hide `joint_fit`.
4. Do **not** modify `CategoryItem.help()` in this step (open question).
   Do **not** modify `dir()` (open question).
5. Direct attribute access to a hidden category remains allowed (lenient
   access per ADR \u00a77). No `ModeError` is raised.

**Suggested commit**

```
Add instance-aware help filter and hide inactive mode categories
```

### Step 11: Update CIF serialization

**Files**

- `src/easydiffraction/io/cif/serialize.py`

**Tasks**

1. In `analysis_to_cif(analysis)`, emit sections in this fixed order.
   Concrete example for `sequential` mode with
   `minimizer_type='lmfit (leastsq)'`:

   ```cif
   _fitting.mode_type sequential
   _fitting.minimizer_type "lmfit (leastsq)"
   ```

   Construct the `_fitting.mode_type` line inline in `analysis_to_cif`
   (single `f'_fitting.mode_type {value}\n'` string); do not add it to
   `Fitting.as_cif`. Quote the value only if it contains whitespace (it
   doesn't for the three enum members, but apply the same quoting rule
   the rest of the serializer uses).

   Section order:
   1. `_fitting.mode_type <value>` — synthesized from
      `analysis.fitting_mode_type`. Do **not** consult any runtime
      descriptor on `fitting`.
   2. `analysis.fitting.as_cif` — currently just
      `_fitting.minimizer_type`.
   3. Aliases loop.
   4. Constraints loop.
   5. The **active** mode-specific section only:
      - `joint` → `analysis.joint_fit.as_cif` (loop)
      - `sequential` → `analysis.sequential_fit.as_cif` (key-value),
        then if any extract rows exist
        `analysis.sequential_fit_extract.as_cif` (loop)
      - `single` → no extra section

2. Inactive mode-specific categories are not emitted, even if they
   contain user-mutated state. This is intentional (ADR \u00a78).
3. Preserve `max_workers` token verbatim. Do not normalize `auto` →
   integer on save.
4. `chunk_size` unset serializes as the CIF null token `.`.
5. `reverse` serializes as `true`/`false` (Step 1).

**Suggested commit**

```
Serialize only active mode-specific analysis categories
```

### Step 12: Update CIF deserialization and add migration error

**Files**

- `src/easydiffraction/io/cif/serialize.py`

**Tasks**

1. In `analysis_from_cif(analysis, cif_text)`, follow this strict order:
   1. Detect legacy markers using `gemmi` block lookups, not raw text
      search. For each legacy CIF name, call `block.find_value(<name>)`
      (for key-value pairs) or `block.find_loop(<name>)` (for loops). If
      any of the following return a non-`None` / non-empty result,
      raise:
      - `_fit.minimizer_type` (key)
      - `_fit.mode` (key)
      - `_joint_fit_experiment.id` (loop column)
      - `_joint_fit_experiment.weight` (loop column)

      Raise once with a single error message listing the new names:
      `_fitting.minimizer_type`, `_fitting.mode_type`,
      `_joint_fit.experiment_id`, `_joint_fit.weight`. Use the same
      exception type the rest of `serialize.py` uses for malformed input
      (grep for existing raises in the file). The project loader
      (`project.py`) already calls `analysis_from_cif` during analysis
      load, which satisfies the ADR's "first access of analysis"
      requirement.

   2. Read `_fitting.mode_type` and call
      `analysis._set_fitting_mode_type(mode_value)`.
   3. Call `analysis.fitting.from_cif(block)` to restore
      `minimizer_type`.
   4. Restore the active mode-specific category, if its CIF rows are
      present:
      - `joint` → `analysis.joint_fit.from_cif(block)`
      - `sequential` → `analysis.sequential_fit.from_cif(block)`, then
        `analysis.sequential_fit_extract.from_cif(block)`
   5. Restore aliases.
   6. Restore constraints (and `analysis.constraints.enable()` if
      non-empty, as today).

2. If `_fitting.mode_type` is absent, default to
   `FitModeEnum.default()`.
3. If the active mode is `single` but joint or sequential rows are
   present, log a warning and skip them; do not error. Inactive sections
   may be present from a manually edited file but they are not
   authoritative.

**Suggested commit**

```
Restore mode before mode-specific analysis sections
```

### Step 13: Tutorials, docs, exports, package-structure regen

**Files**

- every notebook source under `docs/docs/tutorials/*.py` that references
  the old API
- `docs/dev/architecture.md` — update the switchable-category section to
  mention the new **active-sibling selector** pattern with a short
  paragraph and a link to the ADR
- `docs/dev/issues_open.md` — add the open questions from the ADR as
  issue rows (one per question)
- `src/easydiffraction/analysis/__init__.py` and any package
  `__init__.py` that exports renamed symbols
- run `pixi run notebook-prepare` after editing notebook sources (do not
  edit `.ipynb` directly)
- run `pixi run fix` to regenerate `docs/dev/package-structure-*.md` —
  never hand-edit those files

**Tasks**

1. Grep for old API surfaces:

   ```bash
   grep -rIn 'fit_sequential\|joint_fit_experiments\|analysis\.fit\.\|extract_diffrn' \
       docs/ tutorials/ src/easydiffraction/__init__.py
   ```

   Replace each with the new API.

2. Architecture note (~10 lines): the active-sibling selector is a
   distinct pattern from the existing peak-profile-style switchable
   category; the owner gates which sibling category is active and
   visible; persisted mode lives only on the owner.
3. Ensure `__init__.py` files explicitly import every new concrete class
   (per project rule against pkgutil/importlib auto-discovery):
   `Fitting`, `SequentialFit`, `SequentialFitExtractItem`,
   `SequentialFitExtractCollection`, `BoolDescriptor`, renamed
   `JointFitItem` / `JointFitCollection`.
4. Run `pixi run fix`. Accept the regenerated package-structure docs
   without manual review (per project rule).

**Suggested commit**

```
Update tutorials, docs, and exports for new fitting API
```

### Phase 1 review gate

Stop. Summarize the implementation for the user. Wait for explicit
approval before starting Phase 2.

---

## Phase 2 — Verification

### Step 14: Tests and project-wide checks

**Tasks**

1. Add or update unit tests, mirroring source layout:
   - `tests/unit/easydiffraction/core/test_variable.py` — extend to
     cover `BoolDescriptor` (round-trip, null parsing, invalid tokens).
   - `tests/unit/easydiffraction/analysis/categories/test_fitting.py` —
     replaces `test_fit.py`; covers `minimizer_type` and that the class
     is not callable.
   - `tests/unit/easydiffraction/analysis/categories/test_joint_fit.py`
     — replaces `test_joint_fit_experiments.py`; covers renamed fields
     and CIF round-trip with new names.
   - `tests/unit/easydiffraction/analysis/categories/test_sequential_fit.py`
     — covers defaults, validators, CIF round-trip including
     `chunk_size = .` and `max_workers = auto` preservation.
   - `tests/unit/easydiffraction/analysis/categories/test_sequential_fit_extract.py`
     — covers `create()` validation: bad target, bad regex, multiple
     capture groups, backreferences, valid round-trip.
   - `tests/unit/easydiffraction/analysis/test_analysis.py` — extend to
     cover `fitting_mode_type` getter/setter,
     `show_fitting_mode_types()`, `_set_fitting_mode_type()`, `fit()`
     dispatch (with the runners patched), and the help-filter behaviour
     for each mode.
   - `tests/unit/easydiffraction/core/test_guard.py` (or wherever
     `GuardedBase` is tested) — cover the new `_help_filter` hook with a
     minimal subclass; assert the subset-only contract.
2. Update or add integration tests under `tests/integration/fitting/`:
   - rename `test_powder-diffraction_joint-fit.py` usages to the new
     API,
   - replace `test_sequential.py`'s Python-callback usage with
     `sequential_fit_extract` rules,
   - add a test that loading a CIF containing `_fit.mode` raises the
     migration error,
   - add a test confirming inactive mode-specific sections are not
     written to CIF.
3. For any test expecting `log.error(...)` to raise, set Logger to RAISE
   mode via `monkeypatch` (per project rule).
4. Verify test layout matches source layout:

   ```bash
   pixi run test-structure-check
   ```

5. Run the full verification sequence:

   ```bash
   pixi run fix
   pixi run check
   pixi run unit-tests
   pixi run integration-tests
   pixi run script-tests
   ```

6. Each command must pass before considering the plan complete. If
   `pixi run fix` regenerates `docs/dev/package-structure-*.md`, stage
   and commit those without manual edits.

**Suggested commit (after tests pass)**

```
Add tests for fit-mode categories and active-sibling help filter
```

---

## Verification commands (Phase 2)

```bash
pixi run fix
pixi run check
pixi run test-structure-check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

## Files most likely to change

- `src/easydiffraction/core/variable.py`
- `src/easydiffraction/core/guard.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/sequential.py`
- `src/easydiffraction/analysis/categories/fitting/` (new)
- `src/easydiffraction/analysis/categories/sequential_fit/` (new)
- `src/easydiffraction/analysis/categories/sequential_fit_extract/`
  (new)
- `src/easydiffraction/analysis/categories/joint_fit/` (renamed)
- `src/easydiffraction/analysis/categories/fit/` (removed)
- `src/easydiffraction/io/cif/serialize.py`
- tests under `tests/unit/easydiffraction/analysis/` and
  `tests/integration/fitting/`
- tutorial sources under `docs/docs/tutorials/*.py`
- `docs/dev/architecture.md`, `docs/dev/issues_open.md`
- package-structure docs regenerated by `pixi run fix`

## Open items recorded on this branch

These remain open per the ADR and are deliberately not implemented:

- Help-filter hook on `CategoryItem` and `dir()` consistency.
- `single_fit` category.
- Nested-descriptor extract targets, multi-rule conflicts on the same
  target, extraction caching, max-failure thresholds.
- Resume-after-failure for sequential runs.
- CLI override of extract rules.
- Whether CLI-resolved `max_workers` is ever written back to disk
  (current plan: never).

Each should be tracked in `docs/dev/issues_open.md` as part of Step 13.

## Suggested Pull Request

**Title**

```
Reshape fitting API with mode-aware analysis categories
```

**Description (end-user-oriented)**

This change cleans up how fitting is configured and run in
EasyDiffraction.

- Common fitting settings now live in a dedicated `fitting` section
  (`project.analysis.fitting.minimizer_type`). The previous `fit` object
  that mixed configuration and execution has been split.
- The fit mode (`single`, `joint`, or `sequential`) is now selected in
  one place: `project.analysis.fitting_mode_type`. Switching modes
  immediately changes which configuration sections are visible in
  `help()` output and which are saved to the project file.
- Sequential fitting becomes a first-class workflow. Settings such as
  the data directory, file pattern, worker count, chunk size, and
  reverse order are persisted in `project.analysis.sequential_fit`. The
  previous Python-callback for extracting per-file metadata
  (temperature, pressure, etc.) is replaced by
  `project.analysis.sequential_fit_extract` rules that are saved as
  regular project data and work from the CLI as well as from notebooks.
- Joint fitting weights now live in `project.analysis.joint_fit`, keyed
  by experiment id. Missing entries are filled in automatically with a
  neutral weight when you start the fit.
- Help output adapts to the active mode and hides sections that do not
  apply, so users see only the configuration relevant to what they are
  doing.

Old project files that still use the previous category names (`_fit.*`,
`_joint_fit_experiment.*`) will refuse to load with a clear message
pointing at the new names. Since the project is in beta this is
intentional — there is no silent migration.
