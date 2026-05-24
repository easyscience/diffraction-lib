# Review 5: Minimizer Input/Output Split

Context: no `minimizer-input-output-split_reply-2.md` file was present.
This review covers the direct edits made after review 4.

## Findings

1. **Medium — The context still says credible interval levels are currently writable inputs.** The decision now keeps `credible_interval_inner` and `credible_interval_outer` on the output side as fixed `BayesianFitResult` fields (`minimizer-input-output-split.md:138-149`, `:160-163`), which resolves the persistence risk from review 4. But the context still lists those two fields under the current live "Writable inputs" (`:26-32`). Please move them out of that current-writable list so the context matches the decision and live code.

2. **Medium — The context still presents `objective_value` and `reduced_chi_square` as a duplicate pair after the decision says they are distinct.** The context still says three output fields overlap and lists the χ² row as `minimizer.objective_value` vs `fit_result.reduced_chi_square` (`minimizer-input-output-split.md:40-46`). The decision and consequences now say raw `objective_value` and reduced χ² are not duplicates and both stay (`:172-180`, `:291-298`). Please revise the context so it separates the two real duplications from the raw-objective-vs-reduced-χ² distinction.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
