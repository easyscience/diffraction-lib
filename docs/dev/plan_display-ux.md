# Plan: Display UX Facade

## Goal

Implement the display UX approach described in
`docs/dev/adr_display-ux.md`.

The end-user API should become:

```python
project.display.pattern(expt_name='hrpt')

project.display.parameters.free()
project.display.parameters.fittable()
project.display.parameters.all()
project.display.parameters.access()
project.display.parameters.cif_uids()

project.display.fit.results()
project.display.fit.correlations()
project.display.fit.series(param, versus=temperature)

project.display.posterior.pairs()
project.display.posterior.distribution(param)
project.display.posterior.predictive(expt_name='hrpt')

project.display.show_pattern_options(expt_name='hrpt')
```

Renderer configuration should move to:

```python
project.rendering.chart_engine = 'plotly'
project.rendering.table_engine = 'pandas'
project.rendering.show_chart_engines()
project.rendering.show_table_engines()
project.rendering.show_config()
```

## Branch

Use implementation branch:

```text
feature/display-ux
```

## Decisions

- Use grouped display namespaces under `project.display`.
- Use `project.display.fit.series(param, versus=...)` for sequential fit
  parameter plots.
- Use `pattern(..., include='auto')` as the default experiment chart.
- Use `include` rather than `layers`, `components`, `content`, `view`,
  `series`, or boolean flags.
- Do not add `project.display.constraints()`.
- Move constraint reporting to `project.analysis.constraints.show()`.
- Rename the serialized project display category to `rendering`.
- Do not add legacy CIF loading for `_display.plotter_type` or
  `_display.tabler_type`.
- Standardize CIF display helpers on `project.analysis` and
  `project.info`: `as_cif` should be a read-only property returning CIF
  text, and `show_as_cif()` should pretty-print CIF text with a header.
- Implement `include='uncertainty'` immediately where posterior
  predictive data exists.
- No compatibility aliases or deprecation warnings are required unless
  release policy separately requires them.

## Likely Files To Change

- `src/easydiffraction/project/project.py`
- `src/easydiffraction/project/project_info.py`
- `src/easydiffraction/project/categories/display/default.py`
- `src/easydiffraction/project/categories/display/factory.py`
- `src/easydiffraction/project/categories/display/__init__.py`
- new `src/easydiffraction/project/categories/rendering/...`
- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/display/tables.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/categories/constraints/default.py`
- `src/easydiffraction/__main__.py`
- `docs/dev/architecture.md`
- `docs/docs/user-guide/**/*.md`
- `docs/docs/tutorials/*.py`
- tests under `tests/unit/easydiffraction/`
- tests under `tests/integration/fitting/`

Do not edit generated tutorial notebooks directly. Update tutorial `.py`
files and regenerate notebooks in Phase 2 if required.

## Resolved Questions

- Legacy CIF `_display.plotter_type` and `_display.tabler_type` do not
  need to load into `project.rendering`. No legacy code is required.
- `project.analysis` and `project.info` need consistency with structure
  and experiment objects: `as_cif` should be a read-only property that
  returns CIF text, and `show_as_cif()` should pretty-print CIF text
  with a header.
- `include='uncertainty'` should be implemented immediately where
  posterior predictive data exists.

## Phase 1 - Implementation

Do not create or run tests in Phase 1 unless explicitly requested. Every
completed Phase 1 implementation step must be staged with explicit paths
and committed locally before moving to the next implementation step or
the Phase 1 review gate. Use atomic commits, inspect the worktree before
each commit, and stage only the files changed for that step.

- [x] Rename the serialized project display category to rendering.
  - Move or recreate the category package as
    `src/easydiffraction/project/categories/rendering/`.
  - Rename user-facing settings from `plotter_type` and `tabler_type` to
    `chart_engine` and `table_engine`.
  - Add `show_chart_engines()`, `show_table_engines()`, and
    `show_config()`.
  - Update CIF names to `_rendering.chart_engine` and
    `_rendering.table_engine`.
  - Do not add legacy loading for `_display.plotter_type` or
    `_display.tabler_type`.

- [x] Add the new `project.display` facade.
  - Add a facade object that is not the serialized rendering category.
  - Add `pattern(...)` and `show_pattern_options(...)`.
  - Add `parameters`, `fit`, and `posterior` namespace objects.

- [ ] Implement `pattern(..., include='auto')`.
  - Replace common user-facing calls to `plot_meas`, `plot_calc`, and
    `plot_meas_vs_calc` with one state-aware method.
  - Support explicit includes for `measured`, `calculated`,
    `background`, `residual`, `bragg`, `excluded`, and `uncertainty`
    where data is available.
  - Implement `uncertainty` immediately for experiments with posterior
    predictive data.
  - Render a clear warning or error when a requested include is not
    available.

- [x] Move parameter table displays under `project.display.parameters`.
  - Implement `all()`, `fittable()`, `free()`, `access()`, and
    `cif_uids()`.
  - Remove the primary public need for `project.analysis.display`.

- [x] Move fit displays under `project.display.fit`.
  - Implement `results()`.
  - Implement `correlations()`.
  - Implement `series(param, versus=...)`.

- [x] Move Bayesian displays under `project.display.posterior`.
  - Implement `pairs()`.
  - Implement `distribution(param)`.
  - Implement `predictive(expt_name=...)`.

- [x] Move constraint reporting to
      `project.analysis.constraints.show()`.
  - Do not add `project.display.constraints()`.

- [x] Standardize CIF display helpers.
  - Convert `project.analysis.as_cif()` to a read-only
    `project.analysis.as_cif` property.
  - Ensure `project.analysis.show_as_cif()` pretty-prints CIF text with
    a header.
  - Convert `project.info.as_cif()` to a read-only `project.info.as_cif`
    property.
  - Ensure `project.info.show_as_cif()` pretty-prints CIF text with a
    header.

- [ ] Update docs, tutorials, and architecture text.
  - Replace old public display examples with the selected API.
  - Update `docs/dev/architecture.md`.
  - Update tutorial `.py` files only; regenerate notebooks in Phase 2 if
    required.

- [ ] Stop at the Phase 1 review gate.
  - Summarize changed files and open questions.
  - Suggest next verification commands.
  - Wait for user approval before Phase 2.

Suggested Phase 1 commit messages:

```text
Rename display settings category to rendering
Add grouped display facade
Implement state-aware pattern display
Move analysis display reports to display facade
Standardize CIF display helpers
Update display UX documentation
```

## Phase 2 - Verification

After Phase 1 is reviewed and approved:

- [ ] Add or update unit tests for the rendering category.
- [ ] Add or update unit tests for the display facade namespaces.
- [ ] Add or update plotting integration tests for `pattern(...)`.
- [ ] Add or update analysis display integration tests for parameter and
      fit report methods.
- [ ] Regenerate tutorial notebooks if tutorial `.py` files changed.
- [ ] Run formatting and checks.
- [ ] Run unit tests.
- [ ] Run integration tests.
- [ ] Run script tests.

Verification commands:

```sh
pixi run notebook-prepare
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

Run `pixi run notebook-prepare` only if tutorial `.py` files changed.
Run `pixi run integration-tests` only after the relevant unit and
focused integration tests are passing.

## Suggested Commit Message

```text
Plan display UX facade implementation
```

## Suggested Pull Request

Title:

```text
Improve chart and table display API
```

Description:

This change makes display commands easier to discover and use in
notebooks. Experiment patterns, parameter tables, fit reports, and
Bayesian plots are grouped under `project.display`, while renderer
settings move to `project.rendering`.
