# 93. Eliminate Flicker in Live Progress Tables

**Priority:** `[priority] medium`

**Type:** UX

The shared `ActivityIndicator` / Rich `Live` region used by single fit,
sequential fit, and DREAM sampling visibly flickers in terminals
whenever the live renderable grows (new rows appended) or is updated at
a moderate rate. The effect is most pronounced in sequential fit because
rows are added more frequently than in single fit.

**Findings from current investigation:**

- Both single fit (`FitProgressTracker._refresh_activity_indicator`) and
  sequential fit (`_report_chunk_progress`) push a fresh
  `build_table_renderable(...)` into
  `ActivityIndicator.update(content=...)` on each progress event. The
  Rich `Table` instance is rebuilt from scratch every time.
- `_TerminalLiveHandle` / `ActivityIndicator` start `rich.live.Live`
  with `auto_refresh=True`,
  `refresh_per_second=1/_SPINNER_FRAME_SECONDS` (≈10 Hz), and
  `vertical_overflow='visible'`. At every refresh tick, Rich re-renders
  the full multi-line region (table + spinner line), which on many
  terminals causes a visible flicker that scales with row count.
- Earlier attempts to mitigate this in sequential fit by switching to a
  single-line spinner-only `Live` and printing rows above it (so Rich's
  print-above-live mechanism handled them) removed flicker entirely, but
  produced a different visual style from single fit and could not show
  the closing border during the run. That approach was reverted for
  consistency with single fit; flicker came back with it.
- `vertical_overflow='visible'` is required so the growing table is not
  clipped, but it also forces Rich to repaint the whole region rather
  than scroll/append.
- The spinner animation itself drives the refresh rate; lowering
  `refresh_per_second` reduces flicker frequency but makes the spinner
  feel sluggish.
- Single fit appears smoother in practice mainly because content changes
  are throttled (`FIT_PROGRESS_UPDATE_SECONDS = 5.0`) and rows grow
  slowly; the underlying mechanism is the same and it still flickers
  when many iterations are appended quickly.

**Possible directions (not yet evaluated):**

- Decouple spinner refresh from content refresh: drive `Live` at a low
  `refresh_per_second` (e.g. 2–4 Hz) and update content explicitly only
  when a new row arrives, while animating the spinner via the label
  string rather than Rich's renderable diff.
- Render the table once as static `console.print(...)` above a
  single-line spinner-only `Live`, and re-print only the _new_ row(s) on
  each update — restore the streaming approach but emit the bottom
  border at the end (accept the trade-off that the closing border is not
  visible during the run, or print it as part of every update with ANSI
  cursor movement).
- Use `rich.live.Live(transient=False, auto_refresh=False)` and call
  `live.refresh()` manually only when content changes; let the spinner
  animate via a separate background timer or label updates.
- Investigate `rich.progress.Progress` with custom columns and a table
  panel — Rich has optimised diff rendering there.
- Evaluate the actual cause on macOS Terminal / iTerm2 / VS Code
  terminal separately — flicker behaviour differs across emulators.

**Depends on:** nothing. Affects single fit, sequential fit, and DREAM
sampler progress displays — any fix should keep their visuals consistent
(issue #93 should be solved for all three at once).
