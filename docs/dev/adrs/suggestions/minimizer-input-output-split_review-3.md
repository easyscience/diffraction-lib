# Review 3: Minimizer Input/Output Split

Context: no `minimizer-input-output-split_reply-2.md` file was present.
This review covers the direct edits made to
`minimizer-input-output-split.md` after review 2.

## Findings

1. **High — Writable arbitrary credible interval levels still make the persisted `_fit_parameter` columns misleading.** The ADR promotes `credible_interval_inner` and `credible_interval_outer` to user-writable settings, then says the existing fixed `posterior_interval_68_*` / `posterior_interval_95_*` column names remain even when the user picks different levels (`minimizer-input-output-split.md:138-153`). The deferred-work section explicitly postpones the column-naming generalization (`:369-375`). That means this ADR would allow saving a 50% interval in a column named `posterior_interval_68_low`, which is a persisted data-integrity problem. A fit-time warning does not fix the saved schema. Please either constrain these settings to the fixed 0.68 / 0.95 values until generalized column names are accepted, or make the generalized persistence shape part of this ADR.

2. **Medium — The context and decision now disagree on whether credible interval levels are currently writable.** The context still lists `credible_interval_inner` and `credible_interval_outer` under the current live "Writable inputs" (`minimizer-input-output-split.md:26-32`), but the new decision text says they are "promoted from output-only to writable input" and today have only internal `_set_*` methods (`:138-142`). The latter matches the live code. Please update the context list so it does not describe the current API as already writable.

3. **Medium — The context still presents `objective_value` and `reduced_chi_square` as a duplicate pair after the decision says they are distinct.** The context still says three output fields overlap and lists the χ² row as `minimizer.objective_value` vs `fit_result.reduced_chi_square` (`minimizer-input-output-split.md:40-46`). The decision and consequences now say raw `objective_value` and reduced χ² are not duplicates and both stay (`:175-183`, `:294-298`). Please revise the context so it separates the two real duplicates from the raw-objective-vs-reduced-χ² distinction.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
