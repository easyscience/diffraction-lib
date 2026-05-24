# Review 6: Minimizer Input/Output Split

Context: this review follows
`minimizer-input-output-split_reply-2.md`.

## Findings

1. **Medium — The context still says credible interval levels are currently writable inputs.** The decision now keeps `credible_interval_inner` and `credible_interval_outer` on the output side as fixed `BayesianFitResult` fields (`minimizer-input-output-split.md:140-151`, `:162-165`), and the deferred-work section explicitly treats user-configurable interval levels as future work (`:368-375`). However the context still lists those two fields under the current live "Writable inputs" (`:26-32`). Please remove them from that current-writable list, or move them to the fit-filled-output list, so the motivation matches the decision and live code.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
