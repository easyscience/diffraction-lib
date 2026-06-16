# Plan: Validate Joint-Fit Weights Before Residual Normalisation

Governed by [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions
to those instructions are taken in this plan.

Closes issue **15 — Validate Joint-Fit Weights Before Residual
Normalisation**
([`docs/dev/issues/open/highest_validate-joint-fit-weights-before-residual-normalisation.md`](../issues/open/highest_validate-joint-fit-weights-before-residual-normalisation.md)).

## ADR

No new ADR is required. This is a localised correctness fix that adds
boundary-input validation (per §Project Context: "external-library
boundaries (calculator backends, samplers)" and user-producible state)
without changing any documented architecture or public contract. It
touches the fitting-execution path covered by the accepted
[`fit-mode-categories`](../adrs/accepted/fit-mode-categories.md) ADR and
is verified under the
[`test-suite-and-validation`](../adrs/accepted/test-suite-and-validation.md)
strategy, but introduces no new category, factory, or persisted state.

## Problem

Joint-fit weights are read from `analysis.joint_fit[<id>].weight.value`
and passed as a NumPy array into `Fitter.fit(...)`, which forwards them
to `Fitter._residual_function`
(`src/easydiffraction/analysis/fitting.py`). There the array is
normalised and applied per experiment:

```python
norm_weights *= num_expts / np.sum(norm_weights)   # line ~440
...
diff *= np.sqrt(weight)                              # line ~457
```

The `weight` descriptor in
`src/easydiffraction/analysis/categories/joint_fit/default.py` uses a
bare `RangeValidator()` (no bounds), so a user can set negative, zero,
or non-finite weights via the public API. Two failure modes reach the
minimiser as corrupted residuals:

- **All-zero (or empty-sum) set** → `np.sum(norm_weights) == 0` →
  division by zero → `inf`/`nan` weights.
- **Negative weight** → `np.sqrt(weight)` of a negative number → `nan`
  residuals.
- **Non-finite weight** (`nan`/`inf`) → propagates straight through.

These slip silently into the optimiser instead of failing with a clear,
user-facing error.

## Decisions

1. **Validate once, at the `Fitter.fit()` chokepoint** — not inside
   `_residual_function` (which the minimiser calls every iteration; the
   weights are static across a fit) and not only at the descriptor
   setter (a per-element setter cannot catch the _aggregate_ all-zero
   case). `Fitter.fit()` is the single point every joint fit passes
   through (both `Analysis._fit_joint` and any direct `Fitter.fit`
   caller), so one up-front check covers all paths and runs once.

2. **Mirror the existing `_require_measured_data` idiom.** Add a static
   `Fitter._require_valid_weights(weights, experiments)` next to
   `_require_measured_data` and call it from `fit()` immediately after
   the measured-data guard. It raises a plain `ValueError` with a clear,
   user-facing message — consistent with `_require_measured_data` and
   with the existing `raise ValueError(msg)` in `Analysis._fit_joint`.

3. **Validation rule = correct shape + non-negative + finite elements +
   finite positive total** (the issue's "at minimum" option, hardened),
   applied only when `weights is not None`:
   - reject any non-finite value (`nan`/`inf`) — `nan` would otherwise
     pass a `>= 0` test silently;
   - reject any value `< 0`;
   - compute the total **once** as `total = arr.sum(dtype=np.float64)`
     and reject `not np.isfinite(total) or total <= 0`. The
     `np.isfinite(total)` guard is essential and not implied by
     per-element finiteness: a finite, non-negative public input such as
     `[1e308, 1e308]` overflows to `inf` on summation, and `inf <= 0` is
     false, so a `<= 0`-only check would let it through and corrupt the
     `num_expts / np.sum(...)` normalisation. This catches both the
     all-zero set (per-element checks miss it) and the overflow case.
     When `weights is None` (single/sequential fits, or joint with equal
     weights) the array is implicitly all-ones — always valid — and the
     check is skipped.

4. **Do not adopt strictly-positive-per-element here.** Requiring every
   weight `> 0` would preempt issue **122 — Define `joint_fit.weight`
   Bounds**, which owns the question of whether `0` means "exclude this
   experiment" and whether an upper bound exists. Non-negative + total
   `> 0` leaves a single `0` weight valid (that experiment contributes
   zero residuals — effective exclusion), keeping issue 122's design
   space open. Note this in the issue closure.

5. **Leave `RangeValidator()` in `joint_fit/default.py` unchanged.**
   Descriptor-level bounds are issue 122's territory; changing them here
   would widen scope and overlap that issue. The fit-time guard fully
   satisfies issue 15's "before residual normalisation" framing.

6. **Validate the documented shape/length contract at the same gate.**
   `Fitter.fit()` documents `weights` as a 1-D array whose length must
   match `experiments`, and Decision 1 makes this helper the single
   up-front validation chokepoint. Relying on the downstream
   `zip(..., strict=True)` in `_residual_function` would surface a late,
   generic NumPy/Python error only after the minimiser has entered the
   objective callback, and only for some malformed shapes — not the
   clear, user-facing joint-fit error this issue targets. So
   `_require_valid_weights` also rejects `arr.ndim != 1` (scalar or 2-D
   input) and `arr.size != len(experiments)` (short/long arrays) with
   `ValueError` messages naming the joint-fit weights. This also keeps
   the `experiments` parameter meaningfully used, avoiding a Ruff `ARG`
   unused-argument lint breach.

## Open questions

None outstanding. The strictly-positive-vs-non-negative choice is
resolved in Decision 4 (defer per-element bounds to issue 122).

## Concrete files likely to change

Phase 1 (implementation):

- `src/easydiffraction/analysis/fitting.py` — add
  `Fitter._require_valid_weights`, call it in `Fitter.fit()`, extend the
  `fit()` `Raises` docstring.
- `docs/dev/issues/open/highest_validate-joint-fit-weights-before-residual-normalisation.md`
  →
  `docs/dev/issues/closed/validate-joint-fit-weights-before-residual-normalisation.md`
  (`git mv`, drop `highest_` prefix, rewrite body to describe the fix).
- `docs/dev/issues/index.md` — move the issue row from the open table to
  the closed table.

Phase 2 (verification — tests):

- `tests/unit/easydiffraction/analysis/test_fitting.py` — unit tests for
  `Fitter._require_valid_weights` (pure static helper; no engine).
- `tests/integration/fitting/test_powder-diffraction_joint-fit.py` — one
  end-to-end test asserting the clear `ValueError` for an all-zero
  weight set via the public joint-fit path.

## Branch and PR notes

- Branch: `validate-joint-fit-weights` (flat slug off `develop`),
  created and checked out by `/draft-impl-1`'s setup.
- PR targets `develop`. Do not push unless asked.

## Implementation steps (Phase 1)

Per §Planning and §Commits: when an AI agent follows this plan, every
completed Phase 1 step must be staged with **explicit paths** and
committed locally (atomic, single-purpose) before moving to the next
step or the review gate. Mark each `- [ ]` as `- [x]` in the same commit
that completes it.

- [x] **P1.1 — Add weight validation to `Fitter.fit()`.** In
      `src/easydiffraction/analysis/fitting.py`:
  - Add a
    `@staticmethod _require_valid_weights(weights: np.ndarray | None, experiments: list[ExperimentBase]) -> None`
    immediately after `_require_measured_data`, with a numpy-style
    docstring (Parameters / Raises). When `weights is None`, return
    immediately. Otherwise coerce to
    `arr = np.asarray(weights, dtype=np.float64)` and raise `ValueError`
    with a clear, user-facing message (mirroring the tone of
    `_require_measured_data`, naming the joint-fit weights and the
    offending condition) if any of:
    - `arr.ndim != 1` — weights must be a 1-D array (rejects
      scalar/2-D);
    - `arr.size != len(experiments)` — one weight per experiment
      (rejects short/long arrays);
    - `not np.isfinite(arr).all()` — any element is `nan`/`inf`;
    - `(arr < 0).any()` — any element is negative;
    - computing the total **once** as
      `total = arr.sum(dtype=np.float64)` and then
      `not np.isfinite(total) or total <= 0` — the total must be finite
      and strictly positive (rejects the all-zero set and the
      finite-elements-overflow-to-`inf` case from review F1).
  - Call `self._require_valid_weights(weights, experiments)` in `fit()`
    right after the `self._require_measured_data(experiments)` line.
  - Extend the `fit()` `Raises` section to document that a `ValueError`
    is raised for invalid joint-fit weights.
  - Stage:
    `git add src/easydiffraction/analysis/fitting.py docs/dev/plans/validate-joint-fit-weights.md`
  - Commit: `Validate joint-fit weights before residual normalisation`

- [x] **P1.2 — Close issue 15.**
  - `git mv docs/dev/issues/open/highest_validate-joint-fit-weights-before-residual-normalisation.md docs/dev/issues/closed/validate-joint-fit-weights-before-residual-normalisation.md`
  - Rewrite the closed file body to describe what closed it (fit-time
    `_require_valid_weights` guard; non-negative + finite + positive
    total; per-element bounds deferred to issue 122). Keep the `# 15. …`
    H1.
  - Update `docs/dev/issues/index.md`: remove the issue 15 row from the
    open table and add it to the closed table, linking the new
    `closed/...` path.
  - Stage:
    `git add docs/dev/issues/index.md docs/dev/issues/closed/validate-joint-fit-weights-before-residual-normalisation.md docs/dev/plans/validate-joint-fit-weights.md`
    (the `git mv` already stages the deletion of the open file).
  - Commit: `Close joint-fit weight validation issue`

- [x] **P1.3 — Phase 1 review gate.** No-code step. Mark this item
      `[x]`, commit the checklist update alone with message
      `Reach Phase 1 review gate`, then stop for Phase 1 review.

## Verification (Phase 2)

Added/updated tests first, then run the full verification suite. Use the
zsh-safe log-capture pattern from §Workflow whenever output must be
saved for analysis.

Tests to add:

- `tests/unit/easydiffraction/analysis/test_fitting.py` — call
  `Fitter._require_valid_weights` directly (it is a pure static helper,
  no engine, satisfying §Testing's "no real calculation engines"):
  - accepts `None`;
  - accepts a valid positive array (e.g. `[0.3, 0.7]`);
  - accepts an array containing a single `0` with positive total (e.g.
    `[0.0, 1.0]`) — confirms 0-as-exclusion stays valid;
  - raises `ValueError` for a negative element (`[-1.0, 1.0]`);
  - raises `ValueError` for an all-zero set (`[0.0, 0.0]`);
  - raises `ValueError` for `nan` and for `inf`;
  - raises `ValueError` for a finite array whose sum overflows to `inf`
    (e.g. `[1e308, 1e308]`) — review F1;
  - raises `ValueError` for a scalar and for a 2-D array — review F2;
  - raises `ValueError` for a length mismatch vs `experiments` (both
    short and long) — review F2. Pass a lightweight stub `experiments`
    sequence of the expected length (the helper only reads
    `len(experiments)`), keeping the test engine-free.
- `tests/integration/fitting/test_powder-diffraction_joint-fit.py` — add
  a test that builds a joint fit with all-zero weights through the
  public API and asserts a `ValueError` (reusing the file's existing
  fixtures).

Run, in order:

```bash
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

Also confirm the test layout is accepted:

```bash
pixi run test-structure-check
```

Notes:

- `pixi run fix` regenerates `docs/dev/package-structure/full.md` and
  `short.md` — include them only if that command changes them; never
  edit by hand.
- Leave generated benchmark CSVs under `docs/dev/benchmarking/` and any
  tutorial project artifacts untracked unless explicitly asked to update
  them.
- For sandbox-only multiprocessing/process-pool failures, rerun with the
  approved escalated permission path before treating as a code defect.

## Status checklist

- [x] P1.1 — Add weight validation to `Fitter.fit()`
- [x] P1.2 — Close issue 15
- [x] P1.3 — Phase 1 review gate
- [ ] Phase 2 — tests added and full verification suite green

## Suggested Pull Request

**Title:** Clear error for invalid joint-fit weights

**Description:** When fitting several experiments together, each
experiment is given a weight. Previously, entering an invalid set of
weights — for example a negative value, or all weights set to zero —
could silently corrupt the fit, producing meaningless (`nan`) results
without any warning. EasyDiffraction now checks the weights before
fitting starts and stops with a clear, explanatory message if the
weights are negative, not-a-number, or all zero, so you can correct them
straight away instead of chasing a confusing failed fit.
