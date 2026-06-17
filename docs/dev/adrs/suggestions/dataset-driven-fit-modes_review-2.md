# Review 2: Dataset-Driven Fit Modes and Sequential Redefinition

## Findings

### P1. Give loaded-dataset `reverse` a public home or defer it

The revised ADR now says loaded-dataset `sequential` has deterministic
project collection order "with an opt-in reverse (mirroring the existing
`reverse` flag)" (`dataset-driven-fit-modes.md` lines 121-123). But
Decision 5a also says loaded-dataset `sequential` uses neither
`sequential_fit` nor `sequential_fit_extract`, and the folder sweep
categories are parked, hidden, and omitted from CIF
(`dataset-driven-fit-modes.md` lines 215-221). Today `reverse` lives on
`analysis.sequential_fit`, so after parking that category there is no
public or persisted surface left for this opt-in reverse setting. The
ADR also preserves the category-owned selector contract and does not add
new owner-level setters.

Please either remove reverse ordering from the first-step loaded-dataset
contract, or define its new public/persisted home. For example, the ADR
could introduce a small loaded-series configuration category with only
settings that apply to loaded datasets, or explicitly defer reverse
until the folder/input-source follow-up. As written, the plan would have
to invent API surface that the ADR has not approved.

## Checks

Static review only. Per `AGENTS.md`, I did not run tests, lint,
formatters, build commands, or any `pixi` command.
