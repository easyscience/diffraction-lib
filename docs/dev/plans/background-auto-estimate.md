# Plan: Automatic Line-Segment Background Estimation

This plan follows [`AGENTS.md`](../../../AGENTS.md) and implements the
[`background-auto-estimate`](../adrs/suggestions/background-auto-estimate.md)
ADR (drafted via `/draft-adr`, review cycle closed at the sentinel).

**Dependency authorization (for `/draft-impl-1`):** this plan **names
the new runtime dependency `pybaselines`** explicitly (P1.1,
_Decisions_, _Concrete files_). Per [`AGENTS.md`](../../../AGENTS.md) →
**Architecture**, that naming — combined with the user invoking
`/draft-impl-1` / `/draft-impl-2` — is the pre-approval that lets those
shortcuts edit `pyproject.toml`, `pixi.toml`, and `pixi.lock`
autonomously. No other deliberate exception to `AGENTS.md` is taken.

## ADR

This plan owns the ADR
[`docs/dev/adrs/suggestions/background-auto-estimate.md`](../adrs/suggestions/background-auto-estimate.md).
The ADR stays a **suggestion** (Status: Proposed) for this PR; promotion
to `accepted/` is intentionally **out of scope** here and can follow
when the team formally accepts it. (`/review-plan` may request promotion
as a P1 step; if so, it becomes a one-line docs step that `git mv`s the
file, flips the Status line, and updates the index row.)
`/draft-impl-1`'s Phase A commits the ADR from its current
`suggestions/` location and removes the design-phase `_review-*` /
`_reply-*` siblings.

## Branch and PR

- Branch: **`background-auto-estimate`** (flat slug off `develop`, no
  `feature/` prefix). Do not push unless asked.
- PR targets **`develop`**.

## Decisions (settled in the ADR)

- **Public API.** A user-invoked
  `LineSegmentBackground.auto_estimate(*, method='auto', width=None, smoothness=None, n_points=None, use_model=True)`
  — zero-arg must work, no `free` argument, no `**kwargs`. Returns
  `None`, logs a one-line summary (method, width, point count).
  **Never** runs inside `_update()` / at calculation time.
- **Two-stage algorithm.** Stage 1 estimates a peak-insensitive
  background curve `B(x)`; Stage 2 thins it to sparse `(x, intensity)`
  anchors with Ramer–Douglas–Peucker simplification (endpoints always
  kept, optional `n_points` cap). Anchor heights come from `B(x)`,
  clipped to `0 ≤ intensity ≤ intensity_meas` (always the original
  measured intensities). Dense overlap is handled by **abstention** (no
  forced anchor).
- **Auto-parameterization, per dataset.** Peak width `W` (points) is
  measured from the data (`scipy.signal.find_peaks` → `peak_widths`,
  robust **~75th percentile** upper estimate to clear CWL angular
  broadening); noise σ via the MAD of the second difference. The
  peak/resolution model is **not** used for width by default.
  Deterministic; one `log.warning` on degenerate input.
- **One method to start.** A single penalised-least-squares default,
  **`arpls`**, for every experiment; all per-dataset adaptation via the
  derived width/noise/tolerance. `method` is a per-call keyword argument
  validated against a closed `BackgroundEstimatorMethodEnum` with
  exactly `{auto, snip, arpls, fabc}`; `auto` resolves to `arpls`; it is
  **not** a persisted descriptor. A `beam_mode`/`radiation_probe` policy
  is deferred to corpus benchmarking.
- **Backend.** `pybaselines` (approved; BSD-3, runtime deps NumPy+SciPy,
  both already required) supplies Stage-1 `B(x)` (and the classification
  mask). The in-house layer owns the parameterization, Stage-2 thinning,
  clipping, model-guided re-run, and the point lifecycle.
- **Model-guided re-run.** When a calculation has run, the helper input
  is the **peak-subtracted measured intensities**
  `y = intensity_meas − (intensity_calc − intensity_bkg)` (not the fit
  residual), so `B(x)` is the **absolute** background — emitted points
  are absolute heights, no add-back. Peak positions are detected from
  the peak-only model array `intensity_calc − intensity_bkg`. Everything
  comes from the backend-independent `data.*` arrays; **no
  `experiment.refln`** dependency (identical for Cryspy and CrysFML).
  Data-only path (no calculation yet, or `use_model=False`) passes
  `y = intensity_meas`.
- **Lifecycle.** Every call **overwrites and re-fixes**: clears the
  collection and rebuilds it with **fixed** points
  (`intensity.free = False`) regardless of prior free state; no append
  mode. When the collection is non-empty it logs a one-line notice that
  it is replacing the existing points (first call is silent). Sequential
  string ids (`'1', '2', …`). Excluded regions are honoured for free
  (`data.x` / `data.intensity_meas` iterate active points only).

## Open questions

- **Empirical calibration (resolved during Phase 2, not blocking).** The
  Stage-2 tolerance multiplier (`c · σ`, proposed `c ≈ 2`), the width
  percentile (proposed ~75th), and confirmation that the single `arpls`
  default holds across the tutorial corpus (CWL/TOF, neutron/X-ray).
  Record anything surprising in the ADR.
- **ADR promotion** to `accepted/` is out of scope here (see _ADR_);
  flagged for `/review-plan` to confirm or request.

## Concrete files likely to change

- `pyproject.toml` — add `'pybaselines>=1.1'` to `dependencies` (the
  version that ships the classification `mask` + `min_length` and
  `fabc`).
- `pixi.lock` — regenerated via `pixi lock` after the `pyproject.toml`
  edit. `pixi.toml` likely needs **no** edit (the package is installed
  editable, so the new runtime dep flows from `pyproject.toml`); add a
  pin there only if `pixi lock` cannot resolve it.
- `src/easydiffraction/datablocks/experiment/categories/background/enums.py`
  — add `BackgroundEstimatorMethodEnum` (`auto`, `snip`, `arpls`,
  `fabc`) with `default()` / `description()`, matching
  `BackgroundTypeEnum`.
- `src/easydiffraction/datablocks/experiment/categories/background/estimate.py`
  — **new** pure-function estimator module (parameterization + Stage-1
  via `pybaselines` + Stage-2 thinning).
- `src/easydiffraction/core/collection.py` — reusable `clear()` on
  `CollectionBase` via `_adopt_items([])` (unlink children, empty
  `_items`, rebuild `_index`). Used by the overwrite contract.
- `src/easydiffraction/core/category.py` — `CategoryCollection.clear()`
  override (calls `super().clear()` then `_mark_parent_dirty()`), since
  `CategoryCollection` is defined here, not in `collection.py`.
- `src/easydiffraction/datablocks/experiment/categories/background/line_segment.py`
  — add `LineSegmentBackground.auto_estimate()` (the thin adapter).
- `docs/dev/adrs/suggestions/background-auto-estimate.md` and
  `docs/dev/adrs/index.md` — already written; committed by
  `/draft-impl-1` Phase A (not edited again here).
- Phase 2 (tests):
  `tests/unit/easydiffraction/datablocks/experiment/categories/background/test_estimate.py`
  (**new**), `…/test_line_segment.py` (update for `auto_estimate`), unit
  coverage for `CollectionBase.clear()`, and a
  `tests/functional/…/background/` tutorial-corpus comparison test (run
  by `pixi run functional-tests`).

## Implementation steps (Phase 1)

Each `- [ ]` step is one atomic commit. Per §Commits, stage only the
files the step names, with explicit paths, and commit locally with the
step's `Commit:` message **before** moving to the next step or the Phase
1 review gate. Mark `[x]` in this file as part of the same commit. Phase
1 is **code + docs only — no tests** (those are Phase 2).

- [ ] **P1.1 — Add `pybaselines` dependency.** Add `'pybaselines>=1.1'`
      to the `dependencies` list in `pyproject.toml` (it is the new
      runtime backend, §4 of the ADR). Run `pixi lock` to regenerate
      `pixi.lock`. Stage `pyproject.toml` and `pixi.lock` (and
      `pixi.toml` only if a direct pin was required). Commit:
      `Add pybaselines dependency`

- [ ] **P1.2 — Add `BackgroundEstimatorMethodEnum`.** In `enums.py`, add
      a `StrEnum` with members `AUTO='auto'`, `SNIP='snip'`,
      `ARPLS='arpls'`, `FABC='fabc'`, plus `default()` (returns `AUTO`)
      and `description()`, following the existing `BackgroundTypeEnum`.
      No `__init__.py` change (the enum is imported directly, like
      `BackgroundTypeEnum`). Commit: `Add BackgroundEstimatorMethodEnum`

- [ ] **P1.3 — Add the background curve estimator helper.** Create the
      new module `estimate.py` with a pure
      `estimate_background_curve(x, y, *, method='arpls', beam_mode, peaks=None, width=None, smoothness=None, n_points=None) -> (curve, anchors)`.
      `method` is the **resolved** Stage-1 algorithm (`snip` / `arpls` /
      `fabc` — never `auto`) and selects the `pybaselines` routine, so
      **all backend dispatch lives in the helper**, not the adapter.
      Derive `W` (find_peaks → peak_widths, ~75th percentile) and noise
      σ (MAD of the second difference) when not supplied; compute the
      Stage-1 `B(x)` via the selected `pybaselines` routine; thin `B(x)`
      to anchors by RDP with tolerance `c · σ` (endpoints kept, optional
      `n_points` cap). Array-in/array-out, no model state, no domain
      imports. Extract helpers to stay under the lint complexity
      thresholds. Commit: `Add background curve estimator helper`

- [ ] **P1.4 — Add `CollectionBase.clear()`.** Add a bulk reset to
      `CollectionBase` (`core/collection.py`). It must **not** be a bare
      `self._items = []`: that would strand the name `_index` and leave
      removed children with a stale `_parent`. Implement it by
      delegating to the existing teardown primitive
      `self._adopt_items([])`, which unlinks every child
      (`_parent = None`), empties `_items`, and rebuilds `_index` — the
      same invariants `__delitem__` already maintains. Because
      `_adopt_items()` does not notify a dirty-tracking owner, override
      `clear()` on `CategoryCollection` (in `core/category.py`) to call
      `super().clear()` then `self._mark_parent_dirty()`, mirroring how
      `CategoryCollection.add()` layers dirty-marking on the base
      mutator. Stage **both** `src/easydiffraction/core/collection.py`
      and `src/easydiffraction/core/category.py`. (Unit coverage for
      these invariants is added in Phase 2.) Commit:
      `Add clear method to CollectionBase`

- [ ] **P1.5 — Add `LineSegmentBackground.auto_estimate()`.** In
      `line_segment.py`, add the public method (signature in
      _Decisions_). It: reads `self._parent.data`; chooses the helper
      input `y` — data-only `intensity_meas`, or, when `use_model` and
      `np.any(intensity_calc)`, the peak-subtracted
      `intensity_meas − (intensity_calc − intensity_bkg)` and `peaks`
      detected from the peak-only model array; resolves `method='auto'`
      to `arpls` and passes the resolved method into the helper (which
      owns Stage-1 dispatch); clips heights to `[0, intensity_meas]`;
      `clear()`s the collection (logging the replace notice when it was
      non-empty) and `create()`s fixed points with sequential ids; logs
      the one-line summary. Validate `method` against
      `BackgroundEstimatorMethodEnum` centrally. Numpy-style docstring;
      no `**kwargs`. Commit:
      `Add auto_estimate to LineSegmentBackground`

- [ ] **P1.6 — Phase 1 review gate.** No code. Mark this `[x]`, commit
      the checklist update alone, and hand off to `/review-impl-1`.
      Commit: `Reach Phase 1 review gate`

## Phase 2 — Verification

Add/update tests, then run the checks below. **Stop after Phase 1 for
review before starting Phase 2.**

Tests to add/update (unit tests mirror the source tree per
[`test-strategy.md`](../adrs/accepted/test-strategy.md)):

- **`test_estimate.py` (new)** on the pure helper: synthetic patterns
  with a known analytic background (flat, linear, smooth curve, TOF-like
  decay) plus planted Gaussians including a deliberately overlapped
  multiplet — assert the recovered points reproduce the true background
  within tolerance, **no anchor lands on a planted peak**, and none
  exceeds the local data; **CWL angular broadening** (FWHM grows with x)
  keeps the background off the broad peaks; **model-guided re-run** with
  a supplied peak-only model places better anchors **and** yields
  **absolute** background heights (not residual corrections);
  **determinism** (same input → same points); **graceful degradation**
  (peakless input → single warning, not a crash).
- **`test_line_segment.py` (update)** for `auto_estimate` lifecycle:
  overwrite-and-re-fix (fixed points even when prior ones were freed),
  the replace notice on a non-empty collection, sequential ids, and
  data-only vs model-guided dispatch. Also assert each
  `BackgroundEstimatorMethodEnum` value is accepted and reaches Stage-1
  dispatch (`auto`→`arpls`, plus `snip` / `arpls` / `fabc`), and that an
  invalid method is rejected.
- **`CollectionBase.clear()` invariants (new unit coverage)**: after
  `clear()` the collection is empty, name lookups fail (`_index`
  cleared), every prior child has `_parent is None`, and a
  `CategoryCollection` marks its parent dirty — tested directly, not
  only via `auto_estimate()`.
- **Functional tutorial-corpus comparison** in `tests/functional/`
  (data-only, no engine; run by `pixi run functional-tests`): load
  representative tutorial experiments — CWL
  [`ed-2.py`](../../docs/tutorials/ed-2.py),
  [`ed-17.py`](../../docs/tutorials/ed-17.py); TOF
  [`ed-13.py`](../../docs/tutorials/ed-13.py),
  [`ed-16.py`](../../docs/tutorials/ed-16.py) — strip their hand-placed
  points, run `auto_estimate()`, and assert the recovered curve matches
  the original within tolerance. Use this to calibrate `c` and the width
  percentile and confirm the single `arpls` default.
- Verify the test-structure mirror with `pixi run test-structure-check`.

Verification commands (zsh-safe log capture where output is needed):

```bash
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run test-structure-check > /tmp/easydiffraction-structure.log 2>&1; structure_exit_code=$?; tail -n 100 /tmp/easydiffraction-structure.log; exit $structure_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run functional-tests > /tmp/easydiffraction-functional.log 2>&1; functional_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-functional.log; exit $functional_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

If implementation uncovers a serious requirement, risk, design issue, or
a scope change not covered by this plan — for example a public-API
change beyond what the ADR approved, or a dependency the plan does not
name — **stop and ask** before proceeding, per `AGENTS.md` → §Planning.

## Suggested Pull Request

**Title:** Add one-call automatic background estimation for powder
patterns

**Description:** Setting up a line-segment background used to mean
placing every anchor point by hand — tedious, and easy to get wrong
where peaks overlap and the pattern never returns to baseline. This
change adds `experiment.background.auto_estimate()`: call it with no
arguments and it detects a sensible set of background points directly
from your measured pattern, placing them between peaks and reading their
heights from a peak-insensitive background curve so they don't eat into
peak intensities. The points are ordinary, editable control points —
review them, keep them fixed, or free any of them for refinement. Run it
again after an initial fit and it uses the fitted model to place even
better points, especially across crowded regions. It works for both
constant-wavelength and time-of-flight data, neutron and X-ray.
