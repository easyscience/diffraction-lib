# Progress Activity Indicator Implementation Plan

**Status:** Proposed  
**Date:** 2026-05-14

## Goal

Add a small activity indicator for fitting and other long-running
calculations. The indicator should read as the same feature in terminal
and Jupyter, while using environment-appropriate rendering underneath.

This is an activity indicator, not a numeric progress bar. Most
deterministic minimizers do not expose a reliable total work estimate,
and the existing fit progress table updates only when meaningful fit
state changes. A spinner-style indicator communicates that work is
continuing without implying a percentage that may be unavailable.

## User-Facing Behavior

### Visibility

The indicator is controlled by existing verbosity:

| Verbosity | Behavior                                                                                             |
| --------- | ---------------------------------------------------------------------------------------------------- |
| `silent`  | Show nothing. No table, no activity indicator, no status line.                                       |
| `short`   | Show the activity indicator, but not the detailed fit progress table. Keep existing short summaries. |
| `full`    | Show the detailed progress table and the activity indicator below it.                                |

This changes the current fit tracker behavior where `short` returns
before creating any live progress output.

### Labels

Use the following labels:

| Work type                         | Label        |
| --------------------------------- | ------------ |
| Deterministic single fit          | `fitting`    |
| Sequential fit                    | `fitting`    |
| Bayesian DREAM burn phase         | `burn-in`    |
| Bayesian DREAM sampling phase     | `sampling`   |
| Posterior predictive plots/checks | `processing` |
| Posterior pair plots              | `processing` |
| Other long calculations           | `processing` |

The label must be updateable while work is running. DREAM should switch
from `burn-in` to `sampling` when sampler progress reports the phase
change.

### Visual Style

Use compact Unicode spinner frames:

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Examples:

```text
⠋ fitting
⠴ burn-in
⠇ sampling
⠙ processing
```

The indicator should be a single line. In `full` mode it appears below
the progress table. In `short` mode it appears as the only live progress
element.

## Current Code Paths

### Fit Progress

The single-fit and sampler progress lifecycle is owned by
`src/easydiffraction/analysis/fit_helpers/tracking.py`.

Important methods:

- `FitProgressTracker.start_tracking(...)`
- `FitProgressTracker.add_tracking_info(...)`
- `FitProgressTracker.track_sampler_progress(...)`
- `FitProgressTracker.finish_tracking(...)`
- `_make_display_handle()`
- `_TerminalLiveHandle`

The existing table update path uses `render_table(...)`, which delegates
to `TableRenderer` and then to either:

- `PandasTableBackend` in Jupyter
- `RichTableBackend` in terminal

### Sequential Fit

Sequential fitting currently has separate progress output in
`src/easydiffraction/analysis/sequential.py`.

Important functions:

- `fit_sequential(...)`
- `_run_fit_loop(...)`
- `_report_chunk_progress(...)`

Sequential fit should reuse the same activity indicator abstraction
rather than adding a separate spinner implementation.

### Posterior And Other Long Calculations

Posterior display work is routed through:

- `src/easydiffraction/project/display.py`
- `src/easydiffraction/display/plotting.py`

Important entry points include:

- `PosteriorDisplay.pairs(...)`
- `PosteriorDisplay.predictive(...)`
- `Plotter.plot_posterior_pairs(...)`
- `Plotter.plot_posterior_predictive(...)`

These should use the generic `processing` label if an activity indicator
is added to those paths.

## Architecture

### Add A Shared Activity Indicator

Add a small shared display helper, preferably:

```text
src/easydiffraction/display/progress.py
```

Recommended public/internal shape:

```python
class ActivityIndicator:
    def __init__(self, label: str = "processing", *, verbosity: VerbosityEnum) -> None: ...
    def start(self) -> None: ...
    def update(self, *, label: str | None = None, content: object | None = None) -> None: ...
    def stop(self, *, final_label: str | None = None) -> None: ...
```

The exact class name can change during implementation, but it should
provide these capabilities:

- no output in `silent`
- live output in `short` and `full`
- label updates while running
- optional table/content rendering above the indicator in `full`
- terminal and Jupyter implementations behind one API
- safe cleanup on exceptions

### Terminal Rendering

Use Rich for terminal rendering.

Preferred implementation:

- keep using `rich.live.Live`
- render a `rich.console.Group`
- group content should be:
  - the progress table renderable, when present
  - the activity indicator line

The indicator line can be either:

- Rich's built-in `Spinner`, if it works cleanly inside the existing
  `Live` setup, or
- a local unicode-frame renderable driven by the same frame list.

Do not create a second independent `Live` instance for the same output
area. The table and spinner should be refreshed together through one
live handle.

### Jupyter Rendering

Use an IPython `DisplayHandle` and HTML.

The Jupyter spinner should be browser-driven CSS animation, not a
Python-loop animation. This matters because Python may not regain
control during expensive calculations, but CSS keeps animating once the
HTML has been displayed.

Recommended HTML structure:

```html
<div class="ed-activity">
  <span class="ed-activity-spinner"></span>
  <span class="ed-activity-label">fitting</span>
</div>
```

The table HTML and spinner HTML can be updated together in the same
display handle, or the spinner can have its own display handle below the
table. Prefer a single display handle if it keeps table-and-spinner
replacement simpler and avoids duplicated output cells.

### Table Rendering Refactor

The existing table backends mostly print/update directly. For a clean
combined table-plus-spinner render, add a way to build table renderables
without immediately displaying them.

Possible approach:

1. Keep `render_table(...)` working for existing callers.
2. Add a backend method that returns a renderable representation:
   - Rich: return `rich.table.Table`
   - Pandas: return HTML from `Styler.to_html()`
3. Let the activity indicator compose that renderable with the spinner.

This avoids hard-coding table internals in the tracker and keeps normal
table rendering backwards compatible.

## Fit Tracker Integration

### State

Add fields to `FitProgressTracker`:

- `_activity_indicator`
- `_activity_label`

The label is derived from tracking mode:

- fit mode -> `fitting`
- sampler mode -> initial label from sampler phase if known, otherwise
  `sampling`

### `start_tracking(...)`

Update behavior:

1. Set tracking mode.
2. Return immediately only for `silent`.
3. Print the existing start/header messages only where appropriate:
   - keep current full messages
   - keep short mode concise
4. Create the activity indicator for `short` and `full`.
5. In `full`, render the initial empty progress table plus the
   indicator.
6. In `short`, render only the indicator.

### `add_tracking_info(...)`

Update behavior:

1. Always store row state for `full` mode.
2. In `full`, refresh the table plus the indicator.
3. In `short`, do not render the table; keep the indicator running.

### `track_sampler_progress(...)`

Update the activity label from `SamplerProgressUpdate.phase`:

- phase `burn-in` -> label `burn-in`
- phase `sampling` -> label `sampling`
- any other phase -> normalized phase string if user-facing, otherwise
  `processing`

The existing sampler table's `phase` column remains unchanged.

### `finish_tracking(...)`

Update behavior:

1. Finalize the last table row as today.
2. Stop the activity indicator for `short` and `full`.
3. In `full`, print the current completion summary.
4. In `short`, keep or add only a concise completion line if the current
   short behavior expects one.
5. In `silent`, print nothing.

Use `try/finally` in minimizer execution paths so the indicator is
stopped when a solver raises.

## Sequential Fit Integration

Sequential fit should use the same `ActivityIndicator`.

Recommended behavior:

- `silent`: no output.
- `short`: show one activity indicator labelled `fitting`; keep concise
  chunk summaries when chunks finish.
- `full`: show one activity indicator labelled `fitting`; keep detailed
  chunk summaries.

Implementation points:

1. Create the indicator in `fit_sequential(...)` after preflight checks
   and before `_run_fit_loop(...)`.
2. Pass it into `_run_fit_loop(...)`, or wrap `_run_fit_loop(...)` in a
   context manager.
3. Update the indicator content after each chunk if the implementation
   supports content text, for example:

   ```text
   ⠼ fitting  chunk 3/20
   ```

4. Stop the indicator in a `finally` block before printing final
   completion output.

Do not duplicate spinner frame logic in `sequential.py`.

## Posterior And Generic Processing Integration

The first implementation can focus on fitting and sequential fitting.
After that, add a small context helper for generic long calculations:

```python
with activity_indicator("processing", verbosity=VerbosityEnum(project.verbosity)):
    ...
```

Use this for:

- posterior predictive summary generation
- posterior pair plot construction when sample thinning, density grids,
  or figure construction take noticeable time
- any future calculation where total progress is unknown

The generic helper should default to `processing`.

## Testing Plan

### Unit Tests

Add tests for the shared progress helper:

- `silent` does not create display handles or print output.
- `short` starts the indicator.
- `full` can compose content plus indicator.
- label updates replace the visible label.
- `stop()` suppresses cleanup errors.

Extend tracker tests:

- `FitProgressTracker.start_tracking(...)` starts the indicator in
  `short`.
- `silent` still shows nothing.
- full fit mode uses label `fitting`.
- sampler updates switch labels from `burn-in` to `sampling`.
- finalization stops the indicator on success.
- finalization stops the indicator when solver preparation or solver
  execution raises.

Extend sequential tests:

- `fit_sequential(..., verbosity="short")` starts and stops the shared
  indicator.
- `fit_sequential(..., verbosity="silent")` does not start it.
- chunk progress does not create a separate spinner.

### Rendering Tests

Terminal:

- fake or monkeypatch `Live` and assert one live handle receives grouped
  table-plus-indicator content.

Jupyter:

- fake `DisplayHandle` and assert generated HTML contains the activity
  container and the selected label.
- assert CSS animation is included once, not duplicated on every table
  update if avoidable.

### Regression Tests

Keep existing tests passing:

- `tests/unit/easydiffraction/analysis/fit_helpers/test_tracking.py`
- `tests/integration/fitting/test_bayesian_tracker_and_base.py`
- sequential tests under `tests/integration/fitting/test_sequential.py`

## Implementation Sequence

1. Add `display/progress.py` with a minimal `ActivityIndicator`.
2. Add tests for verbosity behavior and label updates.
3. Refactor table rendering just enough to allow Rich renderable and
   Jupyter HTML composition.
4. Wire `FitProgressTracker` to the activity indicator.
5. Update tracker tests for `short`, `full`, `silent`, and sampler phase
   labels.
6. Wire sequential fitting to the shared activity indicator.
7. Update sequential tests.
8. Add generic `processing` context helper.
9. Add the helper to posterior predictive and posterior pairs if
   profiling or user feedback shows those operations need visible
   activity feedback.
10. Run focused unit tests, then the relevant integration tests.

## Open Design Checks

- Whether `short` mode should print the existing start line before the
  spinner or show only the spinner until completion.
- Whether terminal output should use Rich's built-in `Spinner` or the
  explicit EasyDiffraction frame list. Prefer the explicit list if
  consistency with Jupyter matters more than Rich defaults.
- Whether the table and spinner should share one Jupyter display handle.
  Prefer one handle unless it complicates the existing pandas backend.
- Whether generic display/plot operations need a public verbosity
  argument, or should only read `project.verbosity`.
