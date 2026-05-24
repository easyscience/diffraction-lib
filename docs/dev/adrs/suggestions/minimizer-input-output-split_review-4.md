# Review 4: Minimizer Input/Output Split

Context: this review follows
`minimizer-input-output-split_reply-1.md`. The reply addresses review 1,
but the current ADR still has the issues below.

## Findings

1. **High — Writable arbitrary credible interval levels still make the persisted `_fit_parameter` columns misleading.** The ADR promotes `credible_interval_inner` and `credible_interval_outer` to user-writable settings, then keeps the fixed `posterior_interval_68_*` / `posterior_interval_95_*` column names even when users choose different levels (`minimizer-input-output-split.md:138-153`). The deferred-work section explicitly postpones the column-name generalization (`:369-375`). This would allow saving, for example, a 50% interval in a column named `posterior_interval_68_low`. A fit-time warning does not make the persisted schema truthful. Please either constrain these settings to the fixed 0.68 / 0.95 values until generalized columns are accepted, or make the generalized persistence shape part of this ADR.

2. **Medium — The context and decision disagree on whether credible interval levels are currently writable.** The context still lists `credible_interval_inner` and `credible_interval_outer` under the current live "Writable inputs" (`minimizer-input-output-split.md:26-32`), but the decision says they are "promoted from output-only to writable input" and today have only internal `_set_*` methods (`:138-142`). The latter matches the live code. Please update the context list so it does not describe the current API as already writable.

3. **Medium — The context still presents `objective_value` and `reduced_chi_square` as a duplicate pair after the decision says they are distinct.** The context still says three output fields overlap and lists the χ² row as `minimizer.objective_value` vs `fit_result.reduced_chi_square` (`minimizer-input-output-split.md:40-46`). The decision and consequences now say raw `objective_value` and reduced χ² are not duplicates and both stay (`:175-183`, `:294-298`). Please revise the context so it separates the two real duplications from the raw-objective-vs-reduced-χ² distinction.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
