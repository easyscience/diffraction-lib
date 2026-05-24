# Review 5: Minimizer Input/Output Split Branch (Post-Phase 2)

Reviewed plan:
[`minimizer-input-output-split.md`](minimizer-input-output-split.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)

Prior reviews:
[`_review-1`](minimizer-input-output-split_review-1.md),
[`_review-2`](minimizer-input-output-split_review-2.md),
[`_review-3`](minimizer-input-output-split_review-3.md),
[`_review-4`](minimizer-input-output-split_review-4.md) and matching
replies.

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Per the reviewer rule, **no tests, `pixi run fix`, `pixi run check`, or
any other build/verification command was executed**. This is a static
read of the 34 commits on `minimizer-input-output-split` against the
last merged develop ancestor (`973214a5e`), focused on the post-Phase-2
delta since review 4.

## Scope

Compared to review 4, the branch adds three commits:

- `60788b220` Propose IUCr CIF tag alignment for fit outputs
- `6e24d62c8` Add review 4 of input/output split post-Phase 1
- `9878c9f58` Reply to minimizer input-output review 4
- `a2857d9d6` Complete minimizer input-output Phase 2

The first three are documentation only. The last lands Phase 2 in a
single commit covering P2.1 (test migration), P2.2 (new `fit_result`
unit tests), and the cleanup carry-forward agreed in
[`_reply-4`](minimizer-input-output-split_reply-4.md) §"Phase 2
Carry-Forward" (F1 through F3 from review 4).

## Summary

Phase 2 closes the plan. The reply-4 cleanup items are applied, the
test migration is clean, and the new unit-test files exist under
`tests/unit/easydiffraction/analysis/categories/fit_result/`. Two new
small findings worth deciding (F1 below — orphaned method; F2 below —
lint-driven refactors bundled into Phase 2). Neither blocks merge.

## Verification of reply-4 carry-forward

All three items from
[`_reply-4`](minimizer-input-output-split_reply-4.md) §"Phase 2
Carry-Forward" landed in `a2857d9d6`:

### Review-4 F1 — `FitResultBase` defaults aligned

[`base.py:55-78`](../../../src/easydiffraction/analysis/categories/fit_result/base.py:55)
— `success`, `message`, `iterations`, `fitting_time`, and
`reduced_chi_square` now declare `default=None, allow_none=True`. Only
`result_kind` keeps a default (`FitResultKindEnum.default().value`)
because the enum requires a valid member; that exception is reasonable
but undocumented in the class (see F4 below).

The Bayesian side mirrors the same fix:
[`bayesian.py:51-69`](../../../src/easydiffraction/analysis/categories/fit_result/bayesian.py:51)
— `point_estimate_name` and `sampler_completed` are now
`default=None, allow_none=True`. The two credible-interval levels keep
their fixed `0.68` / `0.95` defaults per ADR §"Decisions already made"
point 6, which is correct.

A new test pins the behaviour:
[`test_base.py:43-51`](../../../tests/unit/easydiffraction/analysis/categories/fit_result/test_base.py:43)
asserts that a pre-fit `FitResultBase` serialises `_fit_result.success`,
`_fit_result.message`, and `_fit_result.iterations` as `?`.

Resolved.

### Review-4 F2 — redundant reset before instance replacement removed

[`analysis.py:1207-1216`](../../../src/easydiffraction/analysis/analysis.py:1207)
— `_clear_persisted_fit_state` now constructs a fresh paired instance
directly:

```python
def _clear_persisted_fit_state(self) -> None:
    self._fit_parameters = FitParameters()
    self._fit_result._parent = None
    self._fit_result = self.minimizer._fit_result_class()
    self._fit_result._parent = self
    ...
```

The pre-replacement `_clear_fit_result_projection()` call is gone.
Paired-class invariant is preserved by going through
`self.minimizer._fit_result_class()`. Resolved.

### Review-4 F3 — unreachable `else` branch removed

[`display.py:112-123`](../../../src/easydiffraction/project/display.py:112)
— `_settings_used_rows` no longer carries the
`isinstance(descriptor, GenericDescriptorBase)` guard or the fallback
branch. Each entry in `_setting_descriptor_names` is trusted to
resolve to a descriptor, matching the project rule "no defensive checks
for unlikely edge cases". Resolved.

## Verification of plan-level Phase 2 steps

- **P2.1 — test migration.** `git grep` on the patterns from P1.15 /
  P2.1 returns empty against `src/`, `docs/docs/tutorials/`, and
  `tests/`. The legacy `_minimizer.*` output tags remain only inside
  [`serialize.py`](../../../src/easydiffraction/io/cif/serialize.py)
  as the `_MINIMIZER_OUTPUT_LEGACY_TAGS` rejection list (lines 609-629)
  — intentional.
- **P2.2 — new `fit_result` unit tests.** Four test files exist under
  `tests/unit/easydiffraction/analysis/categories/fit_result/`:
  [`test_base.py`](../../../tests/unit/easydiffraction/analysis/categories/fit_result/test_base.py)
  (defaults, reset, pre-fit CIF unknowns),
  [`test_lsq.py`](../../../tests/unit/easydiffraction/analysis/categories/fit_result/test_lsq.py)
  (LSQ defaults + CIF round-trip),
  [`test_bayesian.py`](../../../tests/unit/easydiffraction/analysis/categories/fit_result/test_bayesian.py)
  (Bayesian defaults including fixed credible-interval levels + CIF
  round-trip),
  [`test_factory.py`](../../../tests/unit/easydiffraction/analysis/categories/fit_result/test_factory.py)
  (factory family creation + paired-class declarations on both
  minimizer bases). Layout matches the test-structure-check expectation
  (a sibling file per source file).
- **P2.3 / P2.4 / P2.5 / P2.6 — auto-fixes, static checks, three
  test suites.** Marked `[x]` in the plan. Reviewer did not re-run
  them; trust the author's pass and gate on CI.

## Paired-class invariant — spot check

Every `self._fit_result = ...` site in
[`analysis.py`](../../../src/easydiffraction/analysis/analysis.py)
constructs through `_fit_result_class`:

- [`analysis.py:483`](../../../src/easydiffraction/analysis/analysis.py:483)
  — `__init__`
- [`analysis.py:1067`](../../../src/easydiffraction/analysis/analysis.py:1067)
  — `_replace_minimizer`
- [`analysis.py:1211`](../../../src/easydiffraction/analysis/analysis.py:1211)
  — `_clear_persisted_fit_state`

Each call also re-establishes `_parent = self`, and each prior instance
is explicitly detached (`_parent = None`) before being replaced. Matches
the ADR's atomic-swap requirement.

Legacy-tag rejection
([`serialize.py:609-629`](../../../src/easydiffraction/io/cif/serialize.py:609))
enumerates all 19 removed `_minimizer.<output>` tags and raises a
single `ValueError` with the correct migration hint pointing at
`_fit_result.*`. Matches plan §P1.11.

## Findings (this review)

### F1 — `_clear_fit_result_projection` is defined but never called

[`analysis.py:1217-1221`](../../../src/easydiffraction/analysis/analysis.py:1217):

```python
def _clear_fit_result_projection(self) -> None:
    """
    Reset result-only fields on the active fit-result category.
    """
    self.fit_result._reset_result_descriptors()
```

`git grep -nE _clear_fit_result_projection src/ tests/` returns only
the definition line. The single caller used to be
`_clear_persisted_fit_state`, removed by the reply-4 F2 fix. After
that removal, this method is dead code.

It is also no longer reachable from outside the class (single-underscore
private API), and the docstring matches the legacy behaviour from
before the fresh-instance approach won out, so keeping it as a future
hook is not justified.

Suggested follow-up: delete the method. One-line cleanup; deferrable
to a follow-on if not in scope for this PR.

### F2 — Phase 2 commit bundles five lint-driven refactors outside the input/output split

The single Phase 2 commit `a2857d9d6` touches files unrelated to the
fit-result split:

- [`src/easydiffraction/core/singleton.py`](../../../src/easydiffraction/core/singleton.py)
  — extracts `_apply_one_constraint` from a `for` body.
- [`src/easydiffraction/analysis/sequential.py`](../../../src/easydiffraction/analysis/sequential.py)
  — splits `_fit_worker` into `_fit_worker_success` /
  `_fit_worker_error` plus several smaller helpers (~121 lines).
- [`src/easydiffraction/display/plotting.py`](../../../src/easydiffraction/display/plotting.py)
  — extracts `_evaluate_posterior_predictive_draw_values` to flatten
  a try/finally body (~73 lines).
- [`src/easydiffraction/analysis/calculators/crysfml.py`](../../../src/easydiffraction/analysis/calculators/crysfml.py)
  — extracts `_calculate_adjusted_pattern` /
  `_calculate_raw_pattern`.
- [`src/easydiffraction/analysis/calculators/pdffit.py`](../../../src/easydiffraction/analysis/calculators/pdffit.py)
  — analogous extraction.

These read as `pixi run check` complexity-threshold refactors. They are
faithful to the project rule "do not raise lint thresholds — refactor
instead" (plan §P2.3), which is the right call mechanically. But they
also have nothing to do with splitting minimizer settings from fit
outputs, so they expand the PR's blast radius and make `git blame`
noisier for unrelated future debugging.

Two options for the next reviewer / PR author:

1. **Keep bundled, but call them out in the PR description** under a
   short "Incidental cleanup" subsection so a future reader of `git
   log` understands why the input/output split commit touched
   `singleton.py`. Lowest-friction option.
2. **Split into a follow-up "Apply lint-driven refactors in Phase 2"
   commit** on the same branch. Keeps the input/output split commit
   focused; one extra commit on the branch.

Either is acceptable. The cleanup itself is correct.

### F3 (informational) — `essdiffraction` removal commit still bundled

[`_review-4`](minimizer-input-output-split_review-4.md) §F5 flagged
the unrelated `c5da0b0fc Remove essdiffraction dependency` commit, and
[`_reply-4`](minimizer-input-output-split_reply-4.md) decided to keep
it on the branch and call it out in the PR description. No change since
review 4. Confirming the decision; this review does not re-open it.

The plan §"Suggested Pull Request" description does not yet mention the
`essdiffraction` removal or the F2 lint-driven refactors. Suggested
amendment to the PR description before opening:

> Incidental cleanup also bundled in this PR: the `essdiffraction`
> dependency is removed, and a handful of unrelated functions
> (`singleton.ConstraintsHandler.apply_constraints`,
> `analysis.sequential._fit_worker`,
> `display.plotting._posterior_predictive_*`,
> `calculators.{crysfml,pdffit}._calculate_pattern`) are split into
> helpers to satisfy the project's complexity thresholds.

### F4 (informational) — `FitResultBase.result_kind` exception undocumented

[`base.py:44-54`](../../../src/easydiffraction/analysis/categories/fit_result/base.py:44)
— `result_kind` keeps a non-None default because
`FitResultKindEnum` requires a valid member. Every other descriptor on
the same class uses `default=None, allow_none=True` after reply-4 F1.
The asymmetry is intentional but unexplained in code; a one-line
comment would save a future reader from wondering whether it is
another instance of the pattern review-4 F1 flagged. Trivial; defer
to a follow-on if not in scope.

## Documentation

- The five amended ADRs and the new accepted ADR are unchanged since
  review 4. No further amendments needed for Phase 2.
- The plan's status checklist is fully `[x]` through P2.6.
- `docs/dev/package-structure/full.md` and `short.md` were updated by
  `pixi run fix` (per CLAUDE.md §Workflow auto-generation) and should
  not be hand-reviewed.

## Verification commands run for this review

Static reads only:

```text
git rev-parse --abbrev-ref HEAD                     # minimizer-input-output-split
git merge-base HEAD main                            # 8f9a679ed
git log --oneline 973214a5e..HEAD                   # 34 commits since last merged PR
git show --stat a2857d9d6                           # Phase 2 commit file list
git grep -nE 'analysis\.minimizer\.(runtime_seconds|iterations_performed|objective_value|...)' src/ tests/ docs/docs/tutorials/
git grep -nE '_minimizer\.(runtime_seconds|...)' src/ tests/ docs/docs/tutorials/
git grep -nE '_clear_fit_result_projection' src/ tests/
git grep -nE '\bFitResult\b' src/ tests/ docs/dev/adrs/ docs/dev/plans/  # stale-name sweep
```

All four migration-pattern greps return empty against `src/`,
`docs/docs/tutorials/`, and `tests/` (the `_minimizer.*` sweep returns
only the rejection list inside `serialize.py`, which is intentional).
The `_clear_fit_result_projection` grep returns the definition line
only — supporting F1 above. The `\bFitResult\b` sweep with the family
names filtered out returns empty, confirming the P1.1 rename has no
stragglers.

No `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
`pixi run integration-tests`, or `pixi run script-tests` was executed.
Those gates are deferred to CI and to the author's Phase 2 pass.

## Recommended next steps

1. **Decide F1.** Drop the orphaned `_clear_fit_result_projection`
   method, or leave the cleanup for a follow-on.
2. **Decide F2.** Either amend the PR description to call out the
   five lint-driven refactors, or split them into a separate cleanup
   commit on the branch.
3. **Update the PR description** to also mention the `essdiffraction`
   removal (F3 carry-over from review 4) so reviewers are not
   surprised by the `pixi.lock` churn.
4. **Optional F4 comment** on `FitResultBase.result_kind` explaining
   why it keeps a default while the rest do not.
5. **Open the PR.** No blockers found; CI is the next gate.
