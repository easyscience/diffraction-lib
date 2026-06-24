# 104. Tighten `FitParameterItem.posterior_summary` NaN Behaviour

**Priority:** `[priority] low`

**Type:** Robustness / partial-data edge case **Source:** Review 8
finding F9.

`FitParameterItem.has_posterior_summary` returns `True` if any posterior
field is set, and `posterior_summary` then builds a
`PosteriorParameterSummary` whose missing floats become `NaN`. A
hand-edited or partially-written CIF row with only
`posterior_gelman_rubin = 1.02` and the rest unset produces a summary
whose `median`, `standard_deviation`, and both interval bounds are
`NaN`. Downstream plotting and the `display.fit_results` table render
NaN intervals — harder to debug than a clean "no posterior" outcome.

The deterministic-fit case is fine: deterministic fits set all required
fields to `None`, so `has_posterior_summary()` returns `False`.

**Fix:** tighten `has_posterior_summary` to require the core stats (at
least `posterior_median` and one interval bound) before emitting a
summary, or split the dataclass into required-statistics and
optional-diagnostics components.

**Depends on:** nothing.
