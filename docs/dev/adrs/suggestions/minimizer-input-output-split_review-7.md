# Review 7: Minimizer Input/Output Split

Context: this review follows
`minimizer-input-output-split_reply-3.md`.

## Findings

No issues found in the current ADR.

The current text consistently keeps `analysis.minimizer` input-only,
moves scalar outputs to the paired internal `analysis.fit_result`
projection, documents the selector-contract exception, keeps fixed
credible interval levels on the output side, and separates the two real
duplicate scalar pairs from the raw-objective-vs-reduced-chi-square
distinction.

## Checks

Skipped by instruction: this is a static ADR review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
