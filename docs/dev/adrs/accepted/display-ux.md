# ADR: Display UX Facade

## Status

Accepted and implemented.

## Context

The previous user-facing display API mixed presentation actions,
analysis reports, and renderer configuration:

```python
project.display.plotter.plot_meas(expt_name='hrpt')
project.display.plotter.plot_calc(expt_name='hrpt')
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')
project.display.plotter.plot_param_correlations()
project.display.plotter.plot_posterior_pairs()
project.display.plotter.plot_param_distribution(param)
project.display.plotter.plot_posterior_predictive(expt_name='hrpt')

project.analysis.display.free_params()
project.analysis.display.fit_results()
```

This has several UX problems:

- `plot_` is redundant below any display or chart object.
- `plotter` and `tabler` expose backend implementation language to
  scientists using notebooks.
- `project.display` and `project.analysis.display` overlap without a
  clear user-facing rule.
- `plot_meas`, `plot_calc`, and `plot_meas_vs_calc` force users to
  choose a plot state that the project can often infer.
- Bayesian and deterministic chart names are not systematic.
- The previous `project.display` category was serialized to CIF, so it
  should not also become a broad transient display facade.

EasyDiffraction is aimed at scientists, often non-programmers, so the
display API should prioritize discoverability, clear names, and safe
defaults.

## Decision

Use `project.display` as the user-facing facade for display actions.
Move serialized renderer settings out of that facade and into separate
project categories named `project.chart` and `project.table`.

Renderer settings:

```python
project.chart.type = 'plotly'
project.table.type = 'pandas'
project.chart.show_supported()
project.table.show_supported()
```

CIF names:

- `_chart.type`
- `_table.type`

No legacy loader is required for `_display.plotter_type` or
`_display.tabler_type`. The project is in beta, so this cleanup may
break old project files rather than carrying compatibility code.

The selected display API is grouped:

```python
project.display.pattern(expt_name='hrpt')

project.display.parameters.free()
project.display.parameters.fittable()
project.display.parameters.all()
project.display.parameters.access()
project.display.parameters.cif_uids()

project.display.fit.results()
project.display.fit.correlations()
project.display.fit.series(param, versus='diffrn.ambient_temperature')

project.display.posterior.pairs()
project.display.posterior.distribution(param)
project.display.posterior.predictive(expt_name='hrpt')

project.display.show_pattern_options(expt_name='hrpt')
```

`project.analysis.display` is removed from the primary public API. Its
current responsibilities move to clearer homes, while the implementation
may keep the existing helpers as internal delegation targets:

| Current method               | New home                                                       |
| ---------------------------- | -------------------------------------------------------------- |
| `all_params()`               | `project.display.parameters.all()`                             |
| `fittable_params()`          | `project.display.parameters.fittable()`                        |
| `free_params()`              | `project.display.parameters.free()`                            |
| `how_to_access_parameters()` | `project.display.parameters.access()`                          |
| `parameter_cif_uids()`       | `project.display.parameters.cif_uids()`                        |
| `fit_results()`              | `project.display.fit.results()`                                |
| `constraints()`              | `project.analysis.constraints.show()`                          |
| `as_cif()`                   | `project.analysis.as_cif` and `project.analysis.show_as_cif()` |

`project.analysis` and `project.info` follow the same CIF display
pattern as structures and experiments:

- `as_cif` is a read-only property returning CIF text as a string.
- `show_as_cif()` pretty-prints the CIF text with a header.

## Pattern Display

Use `pattern()` as the main experiment chart:

```python
project.display.pattern(expt_name='hrpt')
project.display.pattern(expt_name='hrpt', x_min=40, x_max=55)
```

By default, `pattern()` uses `include='auto'` and displays as much
useful information as the project state supports:

- measured data if present
- calculated data if linked structure state and calculated intensities
  are available
- background if powder Bragg measured and calculated data plus defined
  background points are available
- Bragg ticks if powder Bragg measured and calculated data plus
  reflection rows are available
- residual if both measured and calculated data are available and the
  experiment type supports a residual panel
- excluded regions if available on the experiment
- uncertainty bands where posterior predictive data exists and the chart
  engine supports them

Specific subsets are selected with `include`:

```python
project.display.pattern(expt_name='hrpt', include='auto')
project.display.pattern(expt_name='hrpt', include='measured')
project.display.pattern(expt_name='hrpt', include='calculated')
project.display.pattern(
    expt_name='hrpt',
    include=('measured', 'calculated', 'background', 'residual', 'bragg'),
)
```

`include` was chosen over alternatives:

| Name          | Reason not selected                             |
| ------------- | ----------------------------------------------- |
| `layers`      | Sounds graphical rather than user intent.       |
| `components`  | Precise, but longer.                            |
| `content`     | Too broad.                                      |
| `view`        | Better for presets than arbitrary combinations. |
| `series`      | Does not fit residual rows or Bragg ticks well. |
| boolean flags | Explicit, but scales poorly.                    |

Add discovery for supported pattern content:

```python
project.display.show_pattern_options(expt_name='hrpt')
```

The table shows option name, description, availability for the
experiment, whether `include='auto'` includes it, and the reason an
option is unavailable.

Pattern option names:

- `auto`
- `measured`
- `calculated`
- `background`
- `residual`
- `bragg`
- `excluded`
- `uncertainty`

`uncertainty` is available where posterior predictive data exists for a
supported experiment and the active chart engine can render bands. It is
unavailable, with a clear reason, when no posterior predictive data is
present.

Explicit combinations are validated against the same project state used
by `include='auto'`. `background`, `bragg`, and `residual` require both
measured and calculated data in the same view. `excluded` requires
measured, calculated, or uncertainty content in the same view, and
excluded-region overlays currently require the experiment's default
x-axis.

## Deterministic And Bayesian Consistency

Use these naming rules:

- `pattern()` shows the current point-estimate experiment view.
- `fit.results()` reports the latest fit result.
- `fit.correlations()` shows parameter relationships from the latest
  fit.
- `fit.series(param, versus=...)` shows fitted parameter values across a
  sequence of fit results or experiments, using a persisted `diffrn.*`
  path for `versus`.
- `posterior.*` names are used only when posterior samples are required.

`project.display.fit.results()` also prints a "Settings used" block
above the result tables. The block is sourced from
`analysis.minimizer.*` so the minimizer inputs and paired
`analysis.fit_result.*` outputs are visible from the accepted display
facade without adding a new `Analysis`-level display method.

## Rejected Alternatives

Flat display facade:

```python
project.display.pattern(expt_name='hrpt')
project.display.parameters(scope='free')
project.display.fit_results()
project.display.correlations()
project.display.parameter_series(param, versus='diffrn.ambient_temperature')
project.display.posterior_pairs()
project.display.posterior_distribution(param)
project.display.posterior_predictive(expt_name='hrpt')
```

This is shorter but would make `project.display` grow into a long flat
list.

Separate `charts` and `tables` namespaces were also rejected because
users should not need to decide the output type before asking for
information. Some outputs may render as a chart or a table depending on
backend and state.

Separate `measured()` and `calculated()` methods were rejected because
they duplicate `pattern(..., include=...)`.

## Consequences

- The main display workflow becomes more discoverable through grouped
  namespaces and tab completion.
- Renderer configuration becomes clearly separate from display actions.
- Existing tutorials and public API docs must be updated to the selected
  API.
- Constraints remain owned by the analysis constraints category.
- There is no legacy CIF compatibility path for `_display.plotter_type`
  or `_display.tabler_type`.
- `project.analysis` and `project.info` CIF access is standardized for
  consistency with structure and experiment objects.
- Pattern option availability is computed from live project state,
  linked structures, calculated intensities, and experiment-specific
  content instead of placeholder arrays alone.
