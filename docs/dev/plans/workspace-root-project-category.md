# Workspace Root and Project Category Migration Plan

## Status

Branch: `feature/workspace-root-project-category`

ADR suggestion:

```text
docs/dev/adrs/suggestions/workspace-root-project-category.md
```

Two-phase workflow from `.github/copilot-instructions.md`:

- Phase 1 - Implementation. Code and docs updates only. Do not create or
  run tests unless the user explicitly asks.
- Phase 2 - Verification. Add/update tests, then run the verification
  commands listed near the end of this plan.

Stop after Phase 1 and request review before starting Phase 2.

Status checklist. Mark `[x]` only while implementing:

```text
Phase 1 - Implementation
[ ] Phase 0: Confirm breaking-change approval.
[ ] Phase 1: Rename root package and public facade to Workspace.
[ ] Phase 2: Rename project-info access from info to project.
[ ] Phase 3: Align project information fields with _project.* tags.
[ ] Phase 4: Rename project config file to workspace.cif.
[ ] Phase 5: Update root-object references across runtime code.
[ ] Phase 6: Update docs, tutorials, and ADR references.
[ ] Phase 7: Remove old public Project surface unless approved.
[ ] Phase 1 review gate: present diff for approval.

Phase 2 - Verification
[ ] Move/update unit tests to workspace paths.
[ ] Add workspace naming and CIF layout tests.
[ ] pixi run test-structure-check
[ ] pixi run fix
[ ] pixi run check
[ ] pixi run unit-tests
[ ] pixi run integration-tests
[ ] pixi run script-tests
[ ] pixi run notebook-prepare
[ ] pixi run notebook-tests
```

## Commit Discipline

When an AI agent follows this plan, every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or to the Phase 1
review gate.

Follow the **Commits** section of `.github/copilot-instructions.md`.

Rules:

- One commit per phase.
- Keep each commit atomic and single-purpose.
- Stage explicit paths only. Do not use `git add .`.
- Use `git mv` for file and directory moves.
- Do not stage unrelated user changes.
- Do not stage generated artifacts unless the user explicitly asks.
- If a serious uncovered design issue appears, stop and ask before
  continuing.

Suggested commit messages:

```text
Rename Project facade to Workspace
Expose project information as workspace.project
Align project metadata fields with CIF names
Rename project config file to workspace.cif
Update runtime references to Workspace
Update docs for Workspace root API
Remove old Project public API surface
```

## Goal

Split the name "project" into two distinct concepts:

1. `Workspace` - the top-level runtime facade, currently named
   `Project`.
2. `workspace.project` - the category that stores information about the
   scientific project.

Target public API:

```python
import easydiffraction as ed

workspace = ed.Workspace(project_id='lbco_hrpt')
workspace.project.id
workspace.project.title = 'La0.5Ba0.5CoO3 at HRPT@PSI'
workspace.rendering.table_engine = 'rich'
workspace.verbosity = 'short'
workspace.structures
workspace.experiments
workspace.analysis
workspace.display
workspace.summary
workspace.save_as('lbco_hrpt')
```

Target workspace-level config file:

```text
workspace.cif
```

Target CIF tags inside `workspace.cif`:

```cif
_project.id
_project.title
_project.description
_project.created
_project.last_modified

_rendering.chart_engine
_rendering.table_engine

_verbosity.level
```

Do not introduce `_meta.*` tags.

Target saved layout:

```text
<workspace-dir>/
|-- workspace.cif
|-- structures/
|   `-- cosio.cif
|-- experiments/
|   `-- d20.cif
|-- analysis/
|   `-- analysis.cif
`-- summary/
    `-- summary.cif
```

## Decisions Already Made

Use these decisions unless the user explicitly changes the ADR before
implementation:

- The public root class becomes `Workspace`.
- The public root import becomes
  `from easydiffraction import Workspace`.
- The public project-information category becomes `workspace.project`.
- The public rendering category remains `workspace.rendering`.
- The project-information category keeps semantic CIF tags `_project.*`.
- The rendering category keeps semantic CIF tags `_rendering.*`.
- The verbosity preference is serialized as `_verbosity.level`.
- The saved singleton config file becomes `workspace.cif`.
- The saved root is a workspace directory with a user-chosen filesystem
  name; do not use `project` as the conceptual root name in new docs.
- Do not use `project.cif`, `config.cif`, or `meta.cif` as the primary
  singleton config file in the target layout.
- The storage directory path belongs to `Workspace.path`, not
  `workspace.project.path`.
- The old `Project` public API is removed unless the user explicitly
  approves an alias before implementation.
- The category class name `ProjectInfo` is kept; only the public
  attribute name (`info` → `project`) changes.
- `ProjectInfo.path` is removed; the saved directory path lives on
  `Workspace.path` only.
- A first-class `Verbosity` category under `WorkspaceConfig` is required
  (not optional) so that `_verbosity.level` round-trips through
  `workspace.cif` like other singleton categories.
- Source-tree imports may be temporarily inconsistent between phases
  (for example, Phase 1 leaves `project_config_to_cif` imports until
  Phase 4 renames the serializer functions). This is acceptable because
  tests are not run in Phase 1. Each phase must still leave the source
  importable at the end of the phase.

## Current Shape

The current implementation already has a category-owner based project
configuration layer:

```text
src/easydiffraction/project/
|-- project.py             # class Project
|-- project_config.py      # class ProjectConfig
|-- project_info.py        # ProjectInfo export
|-- display.py             # class ProjectDisplay
`-- categories/
    |-- info/              # ProjectInfo category
    `-- rendering/         # Rendering category
```

Current public API:

```python
project = ed.Project(name='my_project')
project.info.title
project.rendering.table_engine
```

Current saved config file:

```text
project.cif
```

## Target Shape

Target implementation:

```text
src/easydiffraction/workspace/
|-- workspace.py           # class Workspace
|-- workspace_config.py    # class WorkspaceConfig
|-- project_info.py        # ProjectInfo export
|-- display.py             # class WorkspaceDisplay
`-- categories/
    |-- project/           # ProjectInfo category
    |-- rendering/         # Rendering category
    `-- verbosity/         # Verbosity category
```

Target public API:

```python
workspace = ed.Workspace(project_id='my_project')
workspace.project.title
workspace.rendering.table_engine
workspace.verbosity = 'short'
```

## Out Of Scope

Do not do these in this migration:

- Do not add `_meta.*` CIF tags.
- Do not use `project.cif`, `config.cif`, or `meta.cif` as the target
  singleton settings file.
- Do not redesign structure or experiment datablocks.
- Do not change analysis fit-mode semantics.
- Do not change calculator behavior.
- Do not edit generated package-structure docs by hand.
- Do not edit generated notebooks directly. Edit tutorial `.py` sources
  and regenerate notebooks during Phase 2.
- Do not keep a `Project = Workspace` compatibility alias unless the
  user explicitly approves it.

## Phase 0: Confirm Breaking-Change Approval

This migration removes or replaces the public `Project` API unless the
user approves a compatibility alias.

Before changing code, ask the user to confirm:

```text
This migration removes ed.Project and replaces it with ed.Workspace.
Should implementation proceed without a Project compatibility alias?
```

If the user asks for a compatibility alias, record that decision in this
plan and in the ADR before implementation.

Do not implement code before this approval gate.

Commit: no commit required for this phase unless the plan or ADR is
updated.

## Phase 1: Rename Root Package And Public Facade

### Objective

Rename the top-level runtime facade and package from `project` to
`workspace`.

### Files Likely To Change

- `src/easydiffraction/project/`
- `src/easydiffraction/__init__.py`
- `src/easydiffraction/__main__.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/sequential.py`
- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/summary/summary.py`
- any source file importing `easydiffraction.project.*`

### Steps

1. Move the source package with `git mv` so history is preserved:

   ```text
   src/easydiffraction/project/
   -> src/easydiffraction/workspace/
   ```

2. Rename files:

   ```text
   workspace/project.py
   -> workspace/workspace.py

   workspace/project_config.py
   -> workspace/workspace_config.py
   ```

3. Rename classes:

   ```text
   Project -> Workspace
   ProjectConfig -> WorkspaceConfig
   ProjectDisplay -> WorkspaceDisplay
   ```

4. Rename class-level state inside the facade:

   ```text
   Project._current_project   -> Workspace._current_workspace
   Project._loading           -> Workspace._loading      # name kept
   Project.current_project_path() -> Workspace.current_workspace_path()
   ```

   Update the `ClassVar` annotation accordingly and update all internal
   references (`type(self)._current_project = self`,
   `cls._current_project`).

5. Update the `varname()` fallback inside `__init__` so the default
   variable name becomes `'workspace'` instead of `'project'`:

   ```python
   self._varname = 'workspace' if type(self)._loading else varname()
   ```

6. Update top-level import:

   ```python
   from easydiffraction.workspace.workspace import Workspace
   ```

7. Remove the old top-level `Project` import unless the user approved an
   alias.

8. Update type-checking imports:

   ```python
   from easydiffraction.workspace.workspace import Workspace
   ```

9. Update docstrings from "Project facade" to "Workspace facade" where
   they describe the root object. Keep wording that talks about the
   scientific project (titles, descriptions, identity) unchanged.

10. Rename `io/ascii.py::extract_project_from_zip` to
    `extract_workspace_from_zip` and update its re-exports in
    `src/easydiffraction/io/__init__.py` and
    `src/easydiffraction/__init__.py`. The function extracts a saved
    workspace directory, not scientific project information.

11. Note: `src/easydiffraction/io/cif/serialize.py` still defines
    `project_config_to_cif`, `project_config_from_cif`, and
    `project_to_cif` at this point. Leave those imports as-is in
    `workspace.py`; they are renamed in Phase 4. The function
    `project_info_to_cif` keeps its name.

12. Run a source-only grep. Do not run tests in Phase 1:

```shell
rg -n "easydiffraction\\.project|\\bProject\\b|ProjectDisplay|ProjectConfig" src
```

For every match, decide whether it refers to:

- the old root object, which should become `Workspace`;
- the project-information category, which should remain project;
- historical text that should be updated in docs later.

### Stop Conditions

Stop and ask if:

- another public class named `Workspace` already exists;
- package moves break imports in a way that would require compatibility
  shims;
- a file has both root-object `project` and category `project` meanings
  that cannot be separated clearly.

### Commit

Stage explicit moved and edited files, then commit:

```text
Rename Project facade to Workspace
```

## Phase 2: Rename Project-Info Access From `info` To `project`

### Objective

Make the project-information category public as `workspace.project`
instead of `workspace.info`.

### Files Likely To Change

- `src/easydiffraction/workspace/workspace_config.py`
- `src/easydiffraction/workspace/workspace.py`
- `src/easydiffraction/workspace/categories/info/`
- `src/easydiffraction/workspace/project_info.py`
- `src/easydiffraction/io/cif/serialize.py`
- all code using `.info` for project information

### Steps

1. Rename category package:

   ```text
   src/easydiffraction/workspace/categories/info/
   -> src/easydiffraction/workspace/categories/project/
   ```

2. Keep the category class name `ProjectInfo` for now. The class name is
   explicit and avoids a confusing `Project` class after the root class
   is renamed to `Workspace`.

3. Rename imports:

   ```python
   from easydiffraction.workspace.categories.project import ProjectInfo
   from easydiffraction.workspace.categories.project import ProjectInfoFactory
   ```

4. In `WorkspaceConfig`, rename:

   ```text
   _info -> _project
   info -> project
   ```

5. In `Workspace`, rename:

   ```text
   _info -> _project
   info -> project
   ```

6. Remove the public `.info` property unless the user approved a
   compatibility alias.

7. Update all runtime references:

   ```text
   workspace.info.title -> workspace.project.title
   workspace.info.description -> workspace.project.description
   workspace.info.update_last_modified() -> workspace.project.update_last_modified()
   ```

8. Run grep:

   ```shell
   rg -n "\\.info\\b|categories/info|categories\\.info" src
   ```

9. For every match, update it if it refers to project information. Leave
   unrelated uses of the word "info" alone.

### Stop Conditions

Stop and ask if:

- `info` appears as a different public concept unrelated to project
  information;
- removing `.info` would break a user-requested compatibility alias.

### Commit

```text
Expose project information as workspace.project
```

## Phase 3: Align Project Information Fields With `_project.*`

### Objective

Expose project identity as `workspace.project.id`, matching CIF
`_project.id`.

Move the saved directory path to `workspace.path`, because it describes
the workspace location and is not serialized project information.

### Files Likely To Change

- `src/easydiffraction/workspace/categories/project/default.py`
- `src/easydiffraction/workspace/workspace.py`
- `src/easydiffraction/io/cif/serialize.py`
- `src/easydiffraction/summary/summary.py`
- `src/easydiffraction/display/plotting.py`
- any code using `.name` for project identity or `.project.path`

### Steps

1. In `ProjectInfo`, rename the public identity property and its setter:

   ```text
   name (getter)  -> id (getter)
   name (setter)  -> id (setter)
   ```

   Do not also rename the internal descriptor attribute
   `self._project_id`; it already matches the new public name.

2. Keep the underlying CIF tag unchanged:

   ```python
   CifHandler(names=['_project.id'])
   ```

3. Update `ProjectInfo.unique_name` to return `self.id`.

4. Keep `ProjectInfo._identity.category_code = 'project'` as-is.

5. Update `project_info_to_cif()` and CIF loading helpers to use
   `info.id`.

6. Rename constructor arguments:

   ```text
   name -> project_id
   ```

   Apply this to:
   - `Workspace.__init__`
   - `WorkspaceConfig.__init__`
   - `ProjectInfo.__init__`
   - `ProjectInfoFactory.create(...)` call sites
   - Default value: `'untitled_project'` (unchanged value, just the
     parameter name changes)

7. Add `Workspace.path` as the runtime storage path. Initialize
   `self._path: pathlib.Path | None = None` in `Workspace.__init__`.

   Suggested shape (match the surrounding `GuardedBase` pattern; do not
   add `@typechecked` here because the setter accepts both `str` and
   `pathlib.Path`):

   ```python
   @property
   def path(self) -> pathlib.Path | None:
       """Saved workspace directory."""
       return self._path

   @path.setter
   def path(self, value: object) -> None:
       self._path = pathlib.Path(value) if value is not None else None
   ```

8. Remove `ProjectInfo.path` (property, setter, and the `self._path`
   attribute inside `ProjectInfo.__init__`) unless explicitly approved
   as a compatibility alias.

9. Update save/load logic across the codebase:

   ```text
   workspace.path
   ```

   should replace:

   ```text
   project.info.path        # old
   workspace.project.path   # never used; do not introduce
   ```

   Concrete call sites include `Workspace.save`, `Workspace.load`,
   `Workspace.current_workspace_path`, and any consumers in `analysis/`,
   `display/`, `summary/`, and `io/`.

10. Update messages and string representations:

```text
Workspace '<project_id>' (...)
Saving workspace '<project_id>' to ...
```

11. Run grep:

```shell
rg -n "\\.name\\b|\\.path\\b|project_id|Project identifier" src/easydiffraction/workspace src/easydiffraction/io src/easydiffraction/display src/easydiffraction/summary
```

Inspect each match manually. Do not blindly replace every `.name`;
structures and experiments still use `.name`.

### Stop Conditions

Stop and ask if:

- a caller depends on `workspace.name` as a root-object property;
- moving `path` out of `ProjectInfo` makes save/load unclear;
- external saved fixtures require an approved compatibility path.

### Commit

```text
Align project metadata fields with CIF names
```

## Phase 4: Rename Project Config File To `workspace.cif`

### Objective

Rename the saved singleton configuration file from `project.cif` to
`workspace.cif`.

### Files Likely To Change

- `src/easydiffraction/workspace/workspace.py`
- `src/easydiffraction/io/cif/serialize.py`
- `src/easydiffraction/workspace/workspace_config.py`
- `src/easydiffraction/workspace/categories/verbosity/`
- CLI entry points in `src/easydiffraction/__main__.py`
- docs that describe saved project directories
- test fixtures in Phase 2

### Steps

1. Rename serializer functions in
   `src/easydiffraction/io/cif/serialize.py` and every call site:

   ```text
   project_config_to_cif   -> workspace_config_to_cif
   project_config_from_cif -> workspace_config_from_cif
   project_to_cif          -> workspace_to_cif
   ```

   Call sites include `workspace.py` (formerly `project.py`),
   `workspace_config.py`, and the serializer itself (the
   `project_to_cif` body calls `project_config_to_cif`). After this step
   the imports that were intentionally left stale in Phase 1 must
   compile cleanly.

   Do not rename `project_info_to_cif`; it serializes the `_project`
   category and that name remains correct.

2. Update `Workspace.save()` to write:

   ```text
   workspace.cif
   ```

3. Update `Workspace.load()` to read:

   ```text
   workspace.cif
   ```

4. Do not add `project.cif`, `config.cif`, or `meta.cif` fallbacks
   unless the user approved a compatibility loader.

5. Add a `Verbosity` category under
   `src/easydiffraction/workspace/categories/verbosity/` following the
   same shape as `rendering/` (a `default.py` with a `Verbosity`
   `CategoryItem`, a `factory.py` with `VerbosityFactory`, and an
   `__init__.py` that imports both to trigger registration).

   The category owns one descriptor:

   ```python
   CifHandler(names=['_verbosity.level'])
   ```

   Bind it in `WorkspaceConfig.__init__` next to `_rendering`, and
   expose it from `Workspace` so that the public access path remains:

   ```python
   workspace.verbosity = 'short'
   workspace.verbosity              # -> 'short'
   ```

   The public `verbosity` getter/setter on `Workspace` reads and writes
   the category's `level` descriptor (validated against `VerbosityEnum`)
   and replaces the current `self._verbosity: VerbosityEnum`
   runtime-only attribute. Remove that attribute.

   Serialize it as:

   ```cif
   _verbosity.level short
   ```

6. Keep the contents semantic:

   ```cif
   _project.id
   _project.title
   _rendering.table_engine
   _verbosity.level
   ```

7. Update logging and console output from `project.cif` to
   `workspace.cif`.

8. Run grep:

   ```shell
   rg -n "project\\.cif|config\\.cif|meta\\.cif|project_config_to_cif|project_config_from_cif|project_to_cif|verbosity" src docs tests
   ```

   Update source and docs only. Test files are handled in Phase 2 unless
   the user explicitly asks otherwise.

9. Saved on-disk fixtures under `data/` and `projects/` still contain
   `project.cif` files (for example `data/lbco_project/project.cif`,
   `projects/cosio/project.cif`). Do **not** edit or regenerate them in
   Phase 1. They are inputs to integration/script tests and will either
   be regenerated in Phase 2 or the relevant tests will be updated to
   write fresh workspace directories. Flag any that block Phase 2 in the
   review gate.

### Stop Conditions

Stop and ask if:

- repository fixtures or tutorials contain saved directories that must
  remain loadable without conversion;
- the user wants a one-release compatibility loader.
- the verbosity setting cannot be represented as a category without
  weakening the public `workspace.verbosity` API.

### Commit

```text
Rename project config file to workspace.cif
```

## Phase 5: Update Root-Object References Across Runtime Code

### Objective

Replace root-object variables and attributes named `project` with
`workspace` where they refer to the top-level facade.

Keep the word `project` where it refers to the project-information
category or the scientific project itself.

### Files Likely To Change

- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/sequential.py`
- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/project/display.py` after it has moved to
  `workspace/display.py`
- `src/easydiffraction/summary/summary.py`
- `src/easydiffraction/__main__.py`
- `src/easydiffraction/io/*`

### Steps

1. Rename root references in `Analysis`:

   ```text
   self.project -> self.workspace
   analysis.project -> analysis.workspace
   ```

   This includes the constructor argument, the stored attribute, and any
   public read-only property exposing the parent workspace.

2. Rename display internals in `WorkspaceDisplay` (formerly
   `ProjectDisplay`) and in any other class that stores a back-
   reference to the root facade:

   ```text
   self._project -> self._workspace
   _set_project(...) -> _set_workspace(...)
   ```

   Only do this when the stored object is the top-level runtime facade.
   Do not touch `self._project_id` inside `ProjectInfo` or `_project.*`
   CIF tags.

3. Rename local variables in runtime code:

   ```text
   project = Workspace(...)
   -> workspace = Workspace(...)
   ```

4. Keep scientific-project wording where appropriate:

   ```text
   workspace.project.title
   project_id
   _project.id
   ```

5. Update user-facing messages carefully. Good examples:

   ```text
   "Workspace directory not found"
   "Saving workspace"
   "Project title"
   ```

6. Run grep:

   ```shell
   rg -n "\\bproject\\b|\\bProject\\b|_project|ProjectDisplay" src/easydiffraction
   ```

7. Inspect each match. Do not replace `_project` CIF tags.

### Stop Conditions

Stop and ask if:

- a name has both root-workspace and project-information meanings in the
  same function and cannot be made clear;
- renaming a method such as `_set_project` would require updating public
  plugin or user code.

### Commit

```text
Update runtime references to Workspace
```

## Phase 6: Update Docs, Tutorials, And ADR References

### Objective

Update user-facing and developer-facing documentation to describe the
new root object and project-information category.

### Files Likely To Change

- `docs/dev/adrs/index.md`
- `docs/dev/issues/open.md`
- `docs/dev/adrs/accepted/*.md`
- `docs/dev/adrs/suggestions/*.md`
- `docs/docs/tutorials/*.py`
- `README.md`
- `CONTRIBUTING.md` only if it contains API examples

Do not edit these by hand:

- `docs/dev/package-structure/full.md`
- `docs/dev/package-structure/short.md`
- generated tutorial notebooks
- generated `docs/site/` files

### Steps

1. Update the relevant accepted ADRs:

   ```text
   Project Facade and Persistence Layout
   -> Workspace Facade and Persistence Layout
   ```

2. Update the affected ADR examples to use:

   ```text
   workspace.project      ProjectInfo
   workspace.rendering    Rendering
   workspace.verbosity    str
   workspace.display      WorkspaceDisplay
   ```

3. Update saved layout examples:

   ```text
   workspace.cif
   structures/
   experiments/
   analysis/
   summary.cif
   ```

4. Update public examples:

   ```python
   workspace = ed.Workspace(project_id='lbco_hrpt')
   workspace.project.title = '...'
   ```

5. Update ADRs that describe current API. Historical reasoning can keep
   old names only if it is clearly historical and not presented as
   current usage.

6. Update tutorial `.py` files, not notebooks. Phase 2 will run
   `pixi run notebook-prepare`.

7. Run grep:

   ```shell
   rg -n "ed\\.Project|from easydiffraction import Project|project\\.info|project\\.rendering|ProjectDisplay|project\\.cif" docs README.md CONTRIBUTING.md
   ```

8. Inspect each match manually.

### Stop Conditions

Stop and ask if:

- a tutorial title uses "Project" as ordinary English rather than API
  naming;
- historical ADRs would become misleading if edited mechanically.

### Commit

```text
Update docs for Workspace root API
```

## Phase 7: Remove Old Public `Project` Surface Unless Approved

### Objective

Finish the breaking rename by removing old public imports and module
paths unless the user approved compatibility.

### Steps Without Compatibility Alias

1. Ensure top-level `easydiffraction.__init__` exports `Workspace`, not
   `Project`.

2. Ensure no source imports from:

   ```text
   easydiffraction.project
   ```

3. Ensure no public source package remains at:

   ```text
   src/easydiffraction/project
   ```

4. Run grep:

   ```shell
   rg -n "from easydiffraction import Project|ed\\.Project|easydiffraction\\.project|\\bProject\\(" src docs tests tools README.md CONTRIBUTING.md
   ```

5. Any remaining match must be:
   - historical text that intentionally names the old API; or
   - a test that will be updated in Phase 2; or
   - a generated artifact that should not be edited manually.

### Steps With Approved Compatibility Alias

Only do this if the user explicitly approved it.

1. Add a temporary alias in `src/easydiffraction/__init__.py`:

   ```python
   Project = Workspace
   ```

2. Keep the alias undocumented unless the user asks for a migration
   note.

3. Add tests in Phase 2 proving both `Workspace` and `Project` construct
   the same root object.

### Commit

Without alias:

```text
Remove old Project public API surface
```

With alias:

```text
Add Project alias for Workspace migration
```

## Phase 1 Review Gate

After Phase 1 commits are complete:

1. Run `git status --short`.
2. Confirm only intended files are changed.
3. Summarize:
   - whether `Project` was removed or aliased;
   - whether `workspace.cif` replaced `project.cif`;
   - any files intentionally left for Phase 2 test updates;
   - any unresolved questions.

4. Stop and ask the user to review before starting Phase 2.

Do not run the full verification suite until the user approves moving to
Phase 2.

## Phase 2: Verification And Tests

Only start this phase after the user approves the Phase 1
implementation.

### Test Updates

Move or update tests to mirror the new source tree:

```text
tests/unit/easydiffraction/project/
-> tests/unit/easydiffraction/workspace/
```

Update imports:

```python
from easydiffraction.workspace.workspace import Workspace
from easydiffraction.workspace.display import WorkspaceDisplay
```

Update functional and integration tests:

```python
from easydiffraction import Workspace
workspace = Workspace(project_id='...')
```

### New Tests To Add

Add focused tests for:

1. `from easydiffraction import Workspace`.
2. `Workspace(project_id='p1').project.id == 'p1'`.
3. `workspace.project.title` round-trips through `workspace.cif`.
4. `workspace.rendering.table_engine` round-trips through
   `workspace.cif`.
5. `workspace.verbosity` round-trips through `workspace.cif`.
6. `Workspace.save()` writes `workspace.cif`.
7. `Workspace.load()` reads `workspace.cif`.
8. `workspace.cif` contains `_project.id`, not `_meta.project_id`.
9. `workspace.cif` contains `_rendering.table_engine`.
10. `workspace.cif` contains `_verbosity.level`.
11. `workspace.path` is set after `save_as()` and `load()`.
12. `workspace.project` has no serialized path field.
13. `project.cif`, `config.cif`, and `meta.cif` are not written unless
    compatibility was approved.
14. `ed.Project` is absent unless compatibility was approved.
15. `Verbosity` category is registered via its factory and reachable
    through `WorkspaceConfig` (parallel to `Rendering`).
16. `ed.extract_workspace_from_zip` is importable and
    `ed.extract_project_from_zip` is not (unless compatibility
    approved).

If compatibility alias was approved, add tests for:

1. `from easydiffraction import Project`.
2. `Project is Workspace` or equivalent behavior.
3. Any approved `project.cif` fallback behavior.

### Verification Commands

Run in this order:

```shell
pixi run test-structure-check
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
pixi run notebook-prepare
pixi run notebook-tests
```

If `pixi run fix` regenerates package-structure docs, accept those
generated changes and do not hand-edit them.

### Phase 2 Commit Suggestions

Use one or more commits, depending on size:

```text
Update workspace unit tests
Update tutorials for Workspace API
Regenerate tutorial notebooks for Workspace API
```

## Grep Checklist

Use this checklist before final review.

Runtime root object should use `Workspace`:

```shell
rg -n "\\bProject\\b|ed\\.Project|from easydiffraction import Project" src tests docs tools README.md CONTRIBUTING.md
```

Project-information category should use `workspace.project`:

```shell
rg -n "\\.info\\b|workspace\\.project|project\\.info" src tests docs tools README.md CONTRIBUTING.md
```

CIF project category should stay `_project`:

```shell
rg -n "_meta\\.|_project\\." src tests docs tools README.md CONTRIBUTING.md
```

Saved config file should be `workspace.cif`:

```shell
rg -n "project\\.cif|config\\.cif|meta\\.cif|workspace\\.cif" src tests docs tools README.md CONTRIBUTING.md
```

Workspace verbosity should serialize as a workspace-level category:

```shell
rg -n "_verbosity|verbosity" src tests docs tools README.md CONTRIBUTING.md
```

Generated docs should not be manually edited:

```shell
git diff -- docs/site docs/dev/package-structure/full.md docs/dev/package-structure/short.md
```

If package-structure docs changed because of `pixi run fix`, that is
expected. If `docs/site` changed, ask before staging.

## Common Mistakes

### Mistake: Renaming `_project.*` To `_workspace.*`

Do not do this. The CIF category describes scientific project
information, not the runtime facade.

Correct:

```cif
_project.id
_project.title
```

Incorrect:

```cif
_workspace.project_id
_workspace.title
```

### Mistake: Introducing `_meta.*`

Do not replace `_project.*` with `_meta.*`.

Correct:

```cif
_project.title
```

Incorrect:

```cif
_meta.project_title
```

### Mistake: Keeping `project.cif` Or Switching To Generic File Names

Do not use `project.cif`, `config.cif`, or `meta.cif` as the target
singleton settings file. The file belongs to the workspace layer.

Correct:

```text
workspace.cif
```

### Mistake: Blindly Replacing Every `project`

Some uses of `project` should remain:

- CIF tags such as `_project.id`
- `workspace.project`
- scientific project wording in prose
- `ProjectInfo` class name, unless a later ADR changes it

Only root-facade uses should become `workspace` or `Workspace`.

### Mistake: Leaving Path On Project Information

The saved directory path belongs to the workspace runtime state. It
should be `workspace.path`, not `workspace.project.path`.

### Mistake: Forgetting Facade Class-Level State

When renaming `Project` to `Workspace`, the `ClassVar`
`_current_project`, the `current_project_path()` classmethod, and the
`varname()` fallback string `'project'` all live on the class itself and
are easy to miss with a single search-and-replace. Rename them to
`_current_workspace`, `current_workspace_path()`, and `'workspace'`
respectively.

### Mistake: Renaming `ProjectInfo._project_id`

The internal descriptor attribute `self._project_id` inside
`ProjectInfo` already matches the new public name `id` and stays as is.
Only the public `name` property/setter becomes `id`.

### Mistake: Editing Generated Notebooks Directly

Tutorial notebooks are generated artifacts. Edit tutorial `.py` files,
then run `pixi run notebook-prepare` in Phase 2.

## Suggested Pull Request

Title:

```text
Rename Project root object to Workspace
```

Description:

```text
This change separates the working EasyDiffraction workspace from the
scientific project information stored inside it. Users now create a
Workspace, while project title and description live under
workspace.project and continue to serialize with clear _project.* CIF
names.
```
