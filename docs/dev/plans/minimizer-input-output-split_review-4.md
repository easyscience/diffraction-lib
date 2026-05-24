# Review 4: Minimizer Input/Output Split Branch (Post-Phase 1)

Reviewed plan:
[`minimizer-input-output-split.md`](minimizer-input-output-split.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Per the reviewer rule, **no tests, `pixi run fix`, `pixi run check`,
or any build/verification command was executed**. This is a static
read of the 31 commits on `minimizer-input-output-split` against
`origin/develop`, plus the new accepted ADR and amended ADRs.

## Scope

The branch carries:

- Phase 1 of the input/output split plan (17 commits, P1.1–P1.17 +
  ADR promotion + an unrelated dependency cleanup).
- The accepted ADR
  [`minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)
  (promoted from suggestions at P1.16).
- A new suggestion ADR
  [`iucr-cif-tag-alignment.md`](../adrs/suggestions/iucr-cif-tag-alignment.md)
  capturing a separate IUCr-alignment proposal for future work.

Phase 2 (P2.1–P2.6: test migration, fix, check, unit/integration/
script tests) has not started yet; this review confirms the gate.

## Summary

Phase 1 implementation matches the plan. Each plan step maps 1:1 to
a commit. The new `fit_result` family classes are in place
([base.py](src/easydiffraction/analysis/categories/fit_result/base.py),
[lsq.py](src/easydiffraction/analysis/categories/fit_result/lsq.py),
[bayesian.py](src/easydiffraction/analysis/categories/fit_result/bayesian.py));
`Analysis._swap_minimizer` wires the paired instance atomically;
`_clear_persisted_fit_state` reinstates the paired class on reset;
the LSQ and Bayesian minimizer bases no longer carry their output
descriptors; CIF serialisation routes outputs to `_fit_result.*` and
rejects the legacy `_minimizer.<output>` tags loudly; the five
affected ADRs are amended; the display facade now prints a "Settings
used" block above the existing fit-result tables; tutorials are
migrated.

All stale-reference greps return clean:

- `analysis.minimizer.<removed_field>` in `src/`, `docs/docs/tutorials/`,
  `tests/` — empty.
- `_minimizer.<removed_field>` in `src/`, `docs/docs/tutorials/`,
  `tests/` — only present inside `serialize.py` as the legacy-tag
  rejection list (intentional).

Five small observations follow. None block Phase 2; F1 and F2 are
worth deciding consciously rather than letting them carry forward.

## Findings

### F1 — `FitResultBase` common-header defaults diverge from the family-class pattern

`FitResultBase`
([base.py:42-71](src/easydiffraction/analysis/categories/fit_result/base.py:42))
keeps the legacy common-class defaults:

- `success` → `default=False`
- `message` → `default=''`
- `iterations` → `default=0`

The new family classes
([lsq.py:80-142](src/easydiffraction/analysis/categories/fit_result/lsq.py:80)
and parts of
[bayesian.py](src/easydiffraction/analysis/categories/fit_result/bayesian.py))
deliberately use `default=None, allow_none=True` for every numeric,
string, and bool result field — with explicit docstrings explaining
why: a CIF written before any fit should emit `?` rather than `0` /
`false` / empty-string, because the scientist audience reads `0`
and `false` as a real fit result.

Pre-fit CIFs under the current layout therefore emit:

```
_fit_result.success     false   # reads as "fit ran and failed"
_fit_result.iterations  0       # reads as "fit ran for 0 iterations"
```

The plan inherited these defaults from the pre-split common class
(see P1.1 — "keep current common fields") so this is not a
regression introduced by this PR. But the divergence is now visible
side-by-side in the same category hierarchy: hovering on
`fit_result.iterations` lands in `FitResultBase` (defaults to `0`),
hovering on `fit_result.n_parameters` lands in `LeastSquaresFitResult`
(defaults to `None`), with no principled reason for the difference.

Bayesian-side mirror: `point_estimate_name` defaults to
`'best_sample'` and `sampler_completed` defaults to `False`
([bayesian.py:51-69](src/easydiffraction/analysis/categories/fit_result/bayesian.py:51)),
while `acceptance_rate_mean` and friends default to `None`. Same
inconsistency.

Suggested follow-up: align `FitResultBase` common fields (and the
Bayesian `point_estimate_name` / `sampler_completed`) with the
`None`/`allow_none=True` convention. Small diff; the existing
`_set_*` callers already pass real values when a fit runs. Defer to
a follow-on if not in scope for this PR.

### F2 — `_clear_persisted_fit_state` resets descriptors then immediately replaces the instance

[analysis.py:1207-1216](src/easydiffraction/analysis/analysis.py:1207):

```python
def _clear_persisted_fit_state(self) -> None:
    self._clear_fit_result_projection()              # resets descriptors
    self._fit_parameters = FitParameters()
    self._fit_result._parent = None
    self._fit_result = self.minimizer._fit_result_class()  # replaces instance
    self._fit_result._parent = self
    self._fit_parameter_correlations = FitParameterCorrelations()
    ...
```

`_clear_fit_result_projection()` walks
`_result_descriptor_names` and resets each to its declared default
on the **old** instance, which is then thrown away on the next
line. A fresh instance has defaults by construction; the reset call
is dead work.

Two clean shapes are possible:

- Drop the `_clear_fit_result_projection()` call and rely on the
  fresh-instance construction. Simpler.
- Drop the instance replacement and rely on
  `_clear_fit_result_projection()`. Then the paired-class invariant
  is preserved only as long as `minimizer.type` does not change
  between fits, which is true today but is the kind of invariant a
  future refactor could quietly break.

The first is the smaller diff. Cosmetic; not a correctness issue
because both paths produce the same end state.

### F3 — `_settings_used_rows` carries an unreachable `else` branch

[display.py:117-129](src/easydiffraction/project/display.py:117):

```python
def _settings_used_rows(self) -> list[list[str]]:
    minimizer = self._project.analysis.minimizer
    rows: list[list[str]] = []
    for name in minimizer._setting_descriptor_names:
        descriptor = getattr(minimizer, name)
        if isinstance(descriptor, GenericDescriptorBase):
            rows.append([...])
        else:
            rows.append([name, str(descriptor), ''])
    return rows
```

Every entry in `_setting_descriptor_names` resolves to a
`GenericDescriptorBase` subclass (verified by reading
[`lsq_base.py`](src/easydiffraction/analysis/categories/minimizer/lsq_base.py)
and
[`bayesian_base.py`](src/easydiffraction/analysis/categories/minimizer/bayesian_base.py)).
The `else` branch is defensive coding against an unreachable state.
Per
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Change Discipline** "No defensive checks for unlikely edge
cases."

Suggested follow-up: drop the `else` branch and the
`isinstance(descriptor, GenericDescriptorBase)` guard. Optional —
this is one screen of code and the fallback is harmless.

### F4 — Phase 2 not started; one test file expected to break

`grep -rlE 'minimizer\.<removed_field>' tests/` returns one hit:

- [`test_lsq_base.py`](tests/unit/easydiffraction/analysis/categories/minimizer/test_lsq_base.py)
  still asserts on `minimizer.objective_name`, `minimizer.objective_value`,
  `minimizer.iterations_performed`, etc. — fields that no longer
  exist on the minimizer hierarchy after P1.9.

This is exactly what P2.1 ("Migrate existing tests off the removed
minimizer output fields") covers, and the plan explicitly defers
test migration to Phase 2. Confirming the gate: Phase 2 must run
before the branch is merge-ready. The migration table in P1.15 /
P2.1 is the right reference for the rewrites.

Informational; the gate matches the plan's Phase 1 → Phase 2 split.

### F5 — Unrelated dependency cleanup landed alongside Phase 1

Commit `c5da0b0fc Remove essdiffraction dependency` touches
[`pixi.lock`](pixi.lock) (-1124 lines), [`pyproject.toml`](pyproject.toml)
(-1 line), and
[`scipp-analysis/dream/test_package_import.py`](tests/integration/scipp-analysis/dream/test_package_import.py)
(-14 lines). It is unrelated to the input/output split work.

Per
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Change Discipline** "Don't add features or refactor unless
asked" and the project's "one focused PR" convention, this would
normally land on its own. Bundling it here makes the PR description
slightly less accurate (the user-facing surface is unchanged by the
essdiffraction removal). If the next reviewer flags it, the cleanest
response is to split it out as a separate PR; otherwise it is small
enough to keep.

Informational only.

## Documentation

- Five accepted ADRs amended as listed in the plan §"ADR":
  `minimizer-category-consolidation.md`, `analysis-cif-fit-state.md`,
  `runtime-fit-results.md`, `switchable-category-owned-selectors.md`,
  `display-ux.md`.
- `docs/dev/adrs/index.md` lists the new ADR under Accepted.
- The plan's `_review-N` / `_reply-N` siblings remain alongside the
  plan (per the project's plan-vs-ADR retention precedent — plans
  keep their deliberation files until the plan itself is deleted on
  merge).
- The IUCr alignment idea is parked as
  [`iucr-cif-tag-alignment.md`](../adrs/suggestions/iucr-cif-tag-alignment.md)
  under suggestions, with a §Status Note explaining it is captured
  for future work, not in scope for the current PR.
- Tutorials regenerated per the P1.15 migration table.

## Verification commands run for this review

No `pixi run`, no lint, no test. Static reads only:

```text
git log --oneline origin/develop..HEAD            # 31 commits
git diff origin/develop...HEAD --stat             # 33 files
git grep -nE 'analysis\.minimizer\.(runtime_seconds|iterations_performed|objective_value|objective_name|n_data_points|n_parameters|n_free_parameters|degrees_of_freedom|covariance_available|correlation_available|exit_reason|point_estimate_name|sampler_completed|credible_interval_inner|credible_interval_outer|acceptance_rate_mean|gelman_rubin_max|effective_sample_size_min|best_log_posterior)' src/ docs/docs/tutorials/ tests/
git grep -nE '_minimizer\.(runtime_seconds|iterations_performed|objective_value|point_estimate_name|sampler_completed|credible_interval_inner|credible_interval_outer|acceptance_rate_mean|gelman_rubin_max|effective_sample_size_min|best_log_posterior)' src/ docs/docs/tutorials/ tests/
grep -rlE 'minimizer\.<removed_field>' tests/
```

The first two return empty against `src/`, `docs/docs/tutorials/`,
and `tests/`. The third returns only `serialize.py` (the
legacy-tag rejection list — intentional). The fourth returns one
file (the Phase 2 migration target).

## Recommended next steps

1. **Decide F1 (`FitResultBase` defaults).** Either align the common
   header with the family-class None-defaults convention, or
   document the divergence as intentional in the accepted ADR and
   move on.
2. **Address F2 (redundant reset) and F3 (unreachable else).** Both
   are one-line cleanups; either bundle into Phase 2 cleanup or
   leave for a follow-on.
3. **Start Phase 2.** P2.1 migrates the one stranded test file;
   P2.2 adds unit tests for the new fit_result classes (none exist
   yet under `tests/unit/easydiffraction/analysis/categories/fit_result/`);
   P2.3–P2.6 run `pixi run fix`, `check`, and the three test
   suites.
4. **Optional: split out `c5da0b0fc` into its own PR** for the
   cleanest history; otherwise note it in the PR description so a
   reviewer is not surprised by the `pixi.lock` churn.
