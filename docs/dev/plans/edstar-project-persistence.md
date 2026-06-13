# EdSTAR Project Persistence Plan

This plan follows `AGENTS.md`. There are no deliberate exceptions.

## Status

- [x] Draft implementation plan from the accepted local instructions and
      current repository context.
- [x] Review and accept this plan.
- [x] Phase 1 - implementation commits complete.
- [x] Phase 1 review complete.
- [x] Phase 2 - tests and verification complete.
- [ ] Phase 2 review complete.

When an AI agent follows this plan, every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or the Phase 1
review gate. Commits must be atomic, single-purpose, and use the commit
message rules from `AGENTS.md`.

Phase 1 must not add or run tests. Phase 2 adds and updates tests, then
runs the verification commands listed below.

## Related ADR

- ADR: `docs/dev/adrs/accepted/edstar-project-persistence.md`
- Implementation branch: `edstar-project-persistence`
- Pull request target: `develop`

This change implements one ADR. As required by `AGENTS.md`, Phase 1 must
promote the ADR from `suggestions/` to `accepted/` before opening a pull
request, update `docs/dev/adrs/index.md`, and fix links that still point
to the old suggestions path.

## Decisions

- EdSTAR becomes the project persistence format: `project.edstar`,
  `structures/<structure>.edstar`, `experiments/<experiment>.edstar`,
  and `analysis/analysis.edstar`.
- `analysis/results.csv`, `analysis/results.h5`, and
  `reports/<project>.cif` keep their current locations and purposes.
- Report CIF generation stays strict IUCr/pdCIF export. Regular project
  save/load must not treat report CIF as round-trippable project state.
- Saved EdSTAR files include the schema marker
  `_edstar.schema_name EasyDiffraction` and `_edstar.schema_version 1`.
- Project restore accepts only EdSTAR project files. Legacy beta
  EasyDiffraction CIF project files fail with an explicit migration
  error. Official CIF import names remain supported by explicit CIF
  import paths where supported, and read aliases remain recorded on
  handlers.
- EdSTAR files take precedence over stale CIF siblings. If both exist,
  load EdSTAR and ignore CIF for the same project section.
- Ordinary `save()` writes EdSTAR files. It does not need to delete
  stale CIF files; precedence and clear console output handle stale
  siblings.
- Public Python names move to the ADR's API-oriented names with no
  transitional Python properties: `project.metadata`,
  `experiment.experiment_type`, `linked_structures`, `linked_structure`,
  `structure_id`, atom/alias `id`, `parameter_unique_name`, and the
  other explicit field renames from the ADR.
- `analysis.software` becomes a role-keyed loop with
  `software[role].{name, version, url}` and a closed `(str, Enum)` role
  set. Fit timestamp moves to `project.metadata.timestamp`.
- Runtime descriptors expose a read-only `url` derived from EdSTAR names
  and docs version. Static docs tables use stable relative anchors, not
  runtime `param.url`.
- Parameter docs remain hand-maintained. A generated CifHandler/EdSTAR
  inventory is an audit artifact, not the source used to generate docs
  tables.
- No new dependency is planned.

## Open Questions

- Whether EdSTAR needs an explicit public CLI format flag. This plan
  assumes no new `--format` flag: `.edstar` is the default project
  persistence format, and CLI help/docs name it because users see the
  files.
- Whether future analysis-reference fields should adopt a broader
  `<target>_id` naming convention. This plan keeps the ADR's current
  decision: `parameter_unique_name` remains the persisted analysis
  parameter reference field.

## Repository Context

Current persistence is centered in:

- `src/easydiffraction/project/project.py`
- `src/easydiffraction/io/cif/handler.py`
- `src/easydiffraction/io/cif/serialize.py`
- `src/easydiffraction/io/cif/parse.py`
- `src/easydiffraction/datablocks/structure/collection.py`
- `src/easydiffraction/datablocks/experiment/collection.py`
- `src/easydiffraction/datablocks/experiment/item/factory.py`
- `src/easydiffraction/io/ascii.py`
- `src/easydiffraction/__main__.py`

The main public-name changes cross these areas:

- Structure categories: `atom_sites`, `atom_site_aniso`, and `geom`.
- Experiment categories: `experiment_type`, `linked_phases`,
  `linked_crystal`, `refln`, `pref_orient`, `instrument`, `background`,
  and `data`.
- Analysis categories: `aliases`, `fit_parameters`,
  `fit_parameter_correlations`, and `software`.
- Project metadata: `project.metadata`, `project.project_metadata`, and
  `project/categories/metadata/`.
- User-facing docs and generated notebooks under `docs/docs/`.

The existing docs reference is a two-tab code/CIF table in
`docs/docs/user-guide/parameters.md` with per-category pages under
`docs/docs/user-guide/parameters/`. It must become the ADR's three-tab
code/EdSTAR/CIF reference.

## Concrete Files Likely To Change

- ADRs and plan: `docs/dev/adrs/accepted/edstar-project-persistence.md`,
  `docs/dev/adrs/index.md`, accepted ADRs that explicitly describe the
  superseded CIF project layout.
- Persistence handlers: `src/easydiffraction/io/cif/handler.py`,
  `src/easydiffraction/io/cif/serialize.py`,
  `src/easydiffraction/io/cif/parse.py`,
  `src/easydiffraction/io/cif/iucr_writer.py`,
  `src/easydiffraction/io/cif/iucr_transformers.py`, plus a new
  `src/easydiffraction/io/edstar/` package if the implementation needs a
  format-specific boundary.
- Project facade/config: `src/easydiffraction/project/project.py`,
  `src/easydiffraction/project/project_config.py`,
  `src/easydiffraction/project/project_metadata.py`,
  `src/easydiffraction/project/categories/metadata/`, and matching
  `__init__.py` files.
- Structure model:
  `src/easydiffraction/datablocks/structure/categories/atom_sites/`,
  `src/easydiffraction/datablocks/structure/categories/atom_site_aniso/`,
  `src/easydiffraction/datablocks/structure/categories/geom/`, structure
  factories/collections, and report/data-context callers that read
  atom-site labels.
- Experiment model: `src/easydiffraction/datablocks/experiment/item/`,
  `src/easydiffraction/datablocks/experiment/categories/experiment_type/`,
  `linked_phases/`, `linked_crystal/`, `refln/`, `pref_orient/`,
  `instrument/`, `background/`, `data/`, and package `__init__.py`
  files.
- Analysis model: `src/easydiffraction/analysis/analysis.py`,
  `src/easydiffraction/analysis/categories/aliases/`,
  `src/easydiffraction/analysis/categories/fit_parameters/`,
  `src/easydiffraction/analysis/categories/fit_parameter_correlations/`,
  `src/easydiffraction/analysis/categories/software/`,
  `src/easydiffraction/analysis/sequential.py`, and display/plotting
  code that reads persisted parameter-reference names.
- Documentation and CLI: `docs/docs/user-guide/parameters.md`,
  `docs/docs/user-guide/parameters/`,
  `docs/docs/user-guide/analysis-workflow/`,
  `docs/docs/quick-reference/index.md`, `docs/docs/tutorials/*.py`,
  regenerated `docs/docs/tutorials/*.ipynb`, `docs/mkdocs.yml`,
  `src/easydiffraction/__main__.py`, and
  `src/easydiffraction/io/ascii.py`.
- New or updated tools: an EdSTAR handler inventory/audit tool under
  `tools/`, and a docs anchor verification tool if it is not folded into
  an existing docs check.
- Tests in Phase 2: matching unit test files under
  `tests/unit/easydiffraction/`, project save/load tests, CLI tests,
  integration tests, script tests, and notebook regeneration checks.

## Implementation Steps (Phase 1)

- [x] P1.1 - Promote the ADR and mark superseded layout text.

  Move the ADR into `docs/dev/adrs/accepted/`, set status to Accepted,
  update `docs/dev/adrs/index.md`, and add narrow cross-reference notes
  to older accepted ADRs whose examples still describe CIF as the
  regular project persistence format. Do not rewrite those historical
  ADRs wholesale.

  Commit:

  ```text
  Accept EdSTAR project persistence ADR
  ```

- [x] P1.2 - Make handler names explicit before changing tags.

  Extend `CifHandler` so each descriptor can declare: `project_name` for
  EdSTAR write tags, `import_names` for accepted read aliases,
  `iucr_name` for report export, and enough category metadata for
  inventory/docs URL generation. Preserve current CIF behavior while
  this step lands.

  Update descriptor construction only where needed to keep current CIF
  output unchanged. Add the versioned docs URL resolver and a read-only
  descriptor `url` property, but keep docs content changes for P1.11.

  Commit:

  ```text
  Add explicit persistence names to handlers
  ```

- [x] P1.3 - Add the generated handler inventory audit.

  Add a tool that imports the registered concrete categories and emits a
  deterministic inventory of descriptor paths, EdSTAR names, legacy CIF
  import names, IUCr names, docs anchors, and ownership context.
  Generate the initial inventory before any write-side tag renames so
  later commits have a reviewable baseline.

  Keep this as an audit artifact. Do not use it to generate user docs
  tables in this plan.

  Commit:

  ```text
  Add EdSTAR persistence inventory audit
  ```

- [x] P1.4 - Introduce EdSTAR project file save/load.

  Add EdSTAR serialization and parsing boundaries, including schema
  marker writing/validation and selector/body consistency checks. Update
  `Project.save()` to write:

  ```text
  project.edstar
  structures/<structure>.edstar
  experiments/<experiment>.edstar
  analysis/analysis.edstar
  analysis/results.csv
  analysis/results.h5
  reports/<project>.cif
  ```

  Update `Project.load()` and structure/experiment/analysis loaders so
  EdSTAR wins over same-section CIF files, while legacy-only beta CIF
  project files fail with explicit migration errors. Keep
  `project.report.save_cif()` and the IUCr writer on the CIF path.

  Commit:

  ```text
  Save and load EdSTAR project files
  ```

- [x] P1.5 - Rename project info to project metadata.

  Move the public facade from `project.info` to `project.metadata`,
  rename the project metadata module/category paths as appropriate, and
  move the project timestamp field to `project.metadata.timestamp`. Keep
  runtime saved path state available through the renamed metadata
  surface. Do not add a `project.info` compatibility property.

  Update save/load, CLI dry-run handling, report path helpers, display
  context, and docs snippets that access project info.

  Commit:

  ```text
  Rename project info facade to metadata
  ```

- [x] P1.6 - Convert analysis software to a role loop.

  Replace the wide `_software.framework_name`,
  `_software.calculator_name`, and `_software.minimizer_name` style with
  a role-keyed collection such as `analysis.software['framework'].name`.
  Add a closed role enum for framework, calculator, and minimizer.

  Update fit-time provenance stamping, report data context, IUCr report
  rendering, HTML/TeX templates, and restore logic. Move fit timestamp
  reads/writes to `project.metadata.timestamp`.

  Commit:

  ```text
  Persist software provenance as role rows
  ```

- [x] P1.7 - Rename structure identity fields.

  Rename atom-site and anisotropic ADP public row identity from `label`
  to `id`, and rename alias row identity from `label` to `id` where it
  belongs with analysis aliases. Update collection key declarations,
  constructors, display/report code, symmetry/ADP lookup code, and
  examples. Keep official CIF import aliases for `_atom_site.label` and
  `_atom_site_aniso.label`; write EdSTAR with the new `id` names.

  Commit:

  ```text
  Rename structure row identities to id
  ```

- [x] P1.8 - Rename experiment type and linked-structure surfaces.

  Rename `experiment.type` to `experiment.experiment_type`. Rename
  powder `linked_phases` to `linked_structures`, single-crystal
  `linked_crystal` to `linked_structure`, and linked item `id` to
  `structure_id`.

  Move package/module names where the public category name changes, and
  update factories, owner attachment, supported-filter logic,
  calculators, display/report code, docs snippets, tutorials, and
  imports. Do not add stale Python aliases.

  Commit:

  ```text
  Rename experiment structure link categories
  ```

- [x] P1.9 - Rename experiment data and instrument fields.

  Apply the remaining experiment-side API/EdSTAR renames from the ADR:
  powder `refln.phase_id` to `structure_id`, preferred-orientation
  `phase_id` to `structure_id`, powder data `point_id` to `id`, TOF
  calibration `quad`/`recip` to `quadratic`/`reciprocal`, and
  line-segment background `x`/`y` to `position`/`intensity`.

  Update EdSTAR write names, legacy CIF import aliases, calculators,
  report writers, plotting code, docs, and tutorials. Preserve strict
  report CIF output names through `iucr_name`/transformers.

  Commit:

  ```text
  Rename experiment EdSTAR fields
  ```

- [x] P1.10 - Rename analysis parameter-reference fields.

  Rename `param_unique_name` to `parameter_unique_name` for aliases and
  fit-parameter state, rename fit-parameter correlation pair fields from
  `param_unique_name_i`/`param_unique_name_j` to
  `parameter_unique_name_i`/`parameter_unique_name_j`, and rename
  `fit_bounds_uncertainty_multiplier` to
  `bounds_uncertainty_multiplier`. If the ADR's open question is
  resolved differently before implementation, apply that explicit
  decision consistently to aliases, fit-parameter state, correlations,
  docs, and tests.

  Update analysis restore, undo, sequential fitting, plotting,
  results-sidecar consumers, and display code.

  Commit:

  ```text
  Rename analysis parameter reference fields
  ```

- [x] P1.11 - Rework parameter docs and runtime links.

  Update `docs/docs/user-guide/parameters.md` to use three tabs: "How to
  access in the code", "Keys in EdSTAR", and "Keys in CIF". Rename
  per-category pages under `docs/docs/user-guide/parameters/` to EdSTAR
  category names, give them EdSTAR titles and EasyDiffraction
  descriptions, and keep IUCr icon links for official dictionary tags.

  Add stable anchors that match the runtime `param.url` resolver. Static
  docs tables should use relative links to the same anchors rather than
  embedding runtime `param.url`.

  Update `docs/mkdocs.yml`, quick reference, workflow docs, tutorials,
  ZIP/project docs, and CLI help text from CIF project persistence to
  EdSTAR project persistence. Regenerate notebooks only from edited
  tutorial `.py` files during the implementation step that changes
  tutorials.

  Commit:

  ```text
  Document EdSTAR parameter keys
  ```

- [x] P1.12 - Refresh report CIF boundaries and stale-name errors.

  Ensure report CIF generation still emits strict IUCr/pdCIF and does
  not accidentally use EdSTAR project names. Remove or update regular
  project-save CIF assumptions in display/report helpers while keeping
  `reports/<project>.cif` intact.

  Add clear boundary errors for schema marker mismatches and legacy-only
  beta CIF project directories. Do not add compatibility parameters or
  properties for removed public names.

  Commit:

  ```text
  Keep report CIF separate from EdSTAR persistence
  ```

- [x] P1.13 - Phase 1 review gate.

  Confirm all Phase 1 implementation commits are present, the plan
  checklist is updated, and no tests or verification commands have been
  run as part of Phase 1. Stop for review before Phase 2.

  Phase 1 review gate reached on branch `edstar-project-persistence`.
  All Phase 1 implementation commits are present and no Phase 2
  verification commands were run during Phase 1.

  Commit:

  ```text
  Reach EdSTAR Phase 1 review gate
  ```

- [x] P1.14 - Rename the space-group coordinate-system parameter.

  Record the post-review Phase 1 scope addition requested after the
  original review gate: rename
  `structure.space_group.it_coordinate_system_code` to
  `structure.space_group.coord_system_code` and write EdSTAR with
  `_space_group.coord_system_code`. Keep official CIF import/report
  names as `_space_group.IT_coordinate_system_code`, and do not preserve
  the pre-release lowercase EdSTAR spelling as a legacy alias.

  Update the accepted ADR, live ADR references, handler inventory,
  source call sites, user docs, tutorials, and regenerated notebooks.
  This reopened the Phase 1 review cycle after the original review-3
  sentinel; Phase 1 review is complete only after the follow-up review
  accepts this additional step.

  Commit:

  ```text
  Rename space-group coordinate-system parameter
  ```

## Verification Steps (Phase 2)

- [x] P2.1 - Add and update focused tests.

  Add or update unit tests for:

  - EdSTAR schema marker write/read validation.
  - EdSTAR-over-CIF precedence for project, structures, experiments, and
    analysis.
  - Beta-window CIF import aliases for each renamed field.
  - Public stale-name failures for removed Python names.
  - Role-keyed `analysis.software` persistence and timestamp relocation.
  - Fit-parameter and fit-parameter-correlation reference-field renames.
  - `param.url` generation and docs-anchor validation.
  - Report CIF continuing to use strict IUCr/pdCIF names.
  - ZIP extraction and CLI help accepting EdSTAR project archives.

  Add integration/script coverage for save/load round trips, tutorial
  projects, report export, and sequential/Bayesian sidecars where those
  paths are affected.

  Commit:

  ```text
  Test EdSTAR project persistence
  ```

- [x] P2.2 - Run structure and formatting checks.

  ```bash
  pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; test_structure_check_exit_code=$?; tail -n 200 /tmp/easydiffraction-test-structure-check.log; exit $test_structure_check_exit_code
  pixi run fix > /tmp/easydiffraction-fix.log 2>&1; fix_exit_code=$?; tail -n 200 /tmp/easydiffraction-fix.log; exit $fix_exit_code
  ```

  Include regenerated `docs/dev/package-structure/full.md` and
  `docs/dev/package-structure/short.md` if `pixi run fix` changes them.

  Commit:

  ```text
  Apply EdSTAR verification formatting
  ```

- [x] P2.3 - Run static checks.

  ```bash
  pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
  ```

  Commit fixes only if this command identifies code or docs issues.

- [x] P2.4 - Run unit tests.

  ```bash
  pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; exit $unit_tests_exit_code
  ```

  Commit fixes only if this command identifies unit-level issues.

- [x] P2.5 - Run integration tests.

  ```bash
  pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; exit $integration_tests_exit_code
  ```

  If the failure is a sandbox-only multiprocessing or permission symptom
  rather than a code assertion, rerun the same command with the approved
  escalated permission path before changing code.

  Commit fixes only if this command identifies integration-level issues.

- [x] P2.6 - Run script tests.

  ```bash
  pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; exit $script_tests_exit_code
  ```

  If two tutorials write to the same project directory under
  `tmp/tutorials/projects/`, fix the tutorial source path, run
  `pixi run notebook-prepare`, and commit the source plus regenerated
  notebook. Do not include benchmark CSV files under
  `docs/dev/benchmarking/` unless the user explicitly asks to update
  benchmark history.

  Commit fixes only if this command identifies script-level issues.

## Suggested Pull Request

Title:

```text
Add EdSTAR project persistence
```

Description:

```text
Save EasyDiffraction projects in the new EdSTAR format while keeping
report CIF output strict for publication and exchange. The change makes
saved project files easier to read and edit, clarifies project metadata
and linked-structure names, and gives clear migration errors for older
beta CIF project directories.
```
