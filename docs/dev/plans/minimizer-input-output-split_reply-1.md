# Reply to Review 1: Minimizer Input/Output Split Plan

Reply to
[`minimizer-input-output-split_review-1.md`](minimizer-input-output-split_review-1.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

All four findings agreed. Each was addressed by editing the plan text;
no item is deferred. The plan is updated in the same commit as this
reply.

## Findings

### Finding 1 — `_clear_persisted_fit_state` resets `_fit_result` to common-only class

**Verdict: agree — real omission in P1.6.**

The current `_clear_persisted_fit_state` (analysis.py:1204) does
`self._fit_result = FitResult()` and calls
`_clear_minimizer_result_projection()`. The original P1.6 wired the
initial `_fit_result` and the swap path but said nothing about the reset
path that fires before every fit. After the split, that path would
discard the paired `LeastSquaresFitResult` / `BayesianFitResult` and
reinstall the bare common class — so the first family-specific `_set_*`
call in P1.7 / P1.8 would write to an attribute that no longer exists on
the live instance.

**Action taken.** Extended P1.6 to enumerate every `_fit_result`
construction and reset site in `analysis.py`:

- `__init__` builds via `self._minimizer._fit_result_class()`.
- `_replace_minimizer` builds via `new_minimizer._fit_result_class()`
  after detaching the old.
- `_clear_persisted_fit_state` rebuilds via
  `self.minimizer._fit_result_class()` so the paired-class invariant
  survives a reset.
- `_clear_minimizer_result_projection` is renamed
  `_clear_fit_result_projection` and retargeted to call
  `self.fit_result._reset_result_descriptors()`, since
  `LeastSquaresMinimizerBase` / `BayesianMinimizerBase` lose their
  `_result_descriptor_names` content at P1.9 / P1.10.
- A
  `git grep -nE 'self\._fit_result\s*=' src/easydiffraction/analysis/analysis.py`
  check at the end of P1.6 confirms every construction goes through the
  paired class. P1.9 also notes that the LSQ `_result_descriptor_names`
  becomes `()` after the removal, so the rename in P1.6 is the correct
  landing.

**Plan section:** P1.6 (rewritten), P1.9 (added confirmation note).

### Finding 2 — P1.2 regresses pre-fit LSQ output defaults

**Verdict: agree — would undo a consolidation-cleanup decision.**

The consolidation cleanup (Review 8 F6, addressed in commit `28d4291cb`)
explicitly moved LSQ result descriptors to
`default=None, allow_none=True` so a pre-fit CIF emits `?` rather than
misleading `0` / `false` / `''` values. The original P1.2 said "bool
defaults `False`; string defaults `''`", which would undo that fix on
every LSQ output relocated to `LeastSquaresFitResult`.

**Action taken.** Rewrote P1.2 to specify:

> All defaults are `None` with `allow_none=True`, matching the
> consolidation cleanup that previously moved LSQ outputs off `0` /
> `false` / `''` so a pre-fit CIF emits `?` rather than a value that
> looks like a degenerate result. This applies to numeric, integer-like,
> string, and bool fields alike; the descriptor helpers in
> `LeastSquaresMinimizerBase` that currently produce these descriptors
> are the model — they can be lifted into `LeastSquaresFitResult`
> verbatim before being removed from `lsq_base.py` at P1.9.

The lift-verbatim instruction also reduces drift risk: the helper
functions move with their existing defaults rather than being rewritten.

**Plan section:** P1.2 (rewritten).

### Finding 3 — Package-level `FitResult` imports outside `fit_result/__init__.py`

**Verdict: agree — four sites missing from the plan.**

`git grep -nP '\bFitResult\b' src/` lists four references that the
original P1.1 did not call out explicitly:

- `src/easydiffraction/analysis/__init__.py:14`
- `src/easydiffraction/analysis/categories/__init__.py:14`
- `src/easydiffraction/analysis/analysis.py:18` (import)
- `src/easydiffraction/analysis/analysis.py:432` (property type
  annotation)
- `src/easydiffraction/analysis/analysis.py:483` (construction in
  `__init__`)
- `src/easydiffraction/analysis/analysis.py:1208` (construction in
  `_clear_persisted_fit_state`)

Without explicit migration, after P1.16 removes the old `FitResult`
re-export, these imports break or keep loading the wrong class.

**Action taken.** Rewrote P1.1 to enumerate every site explicitly, with
a `git grep -nP '\bFitResult\b' src/` verification gate at the end of
the step. The two `self._fit_result = FitResult()` constructions become
`FitResultBase()` temporarily and are then retargeted to the paired
class in P1.6.

**Plan section:** P1.1 (rewritten with the full call-out list and
verification grep).

### Finding 4 — Fit-result factory inconsistency

**Verdict: agree — `factory.py` already exists, and the original text
was internally inconsistent about whether it or `_fit_result_class` is
authoritative for swap.**

The current `fit_result/factory.py` is a 15-line `FactoryBase`
registration shell. The original P1.4 called it "new" and said the
factory is used by `_swap_minimizer`, while P1.6 said
`_replace_minimizer` constructs via `new_minimizer._fit_result_class()`
directly — pick one.

**Action taken.** Two coordinated edits:

- The §"Created" list now says the factory exists; this plan extends
  rather than creates it. The same note clarifies that the authoritative
  swap mechanism is `_fit_result_class` (on the minimizer base), with
  the factory as a registration/introspection helper.
- P1.4 now says "Register fit-result classes with the existing
  `FitResultFactory`" and adds an explicit "Authoritative mechanism"
  paragraph stating that `_swap_minimizer` reads the paired class off
  `new_minimizer._fit_result_class`, not via a factory lookup.

**Plan section:** §"Created" (factory bullet), P1.4 (rewritten).

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter, or
test command was executed.

## Summary of files touched by this reply

- [`docs/dev/plans/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — plan updated per all four findings above (P1.1, P1.2, P1.4, P1.6,
  P1.9 + §"Created" bullet).
- [`docs/dev/plans/minimizer-input-output-split_reply-1.md`](minimizer-input-output-split_reply-1.md)
  — this reply.
