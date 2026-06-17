# ADR: Notebook-Owned Verification Regression Gating

## Status

Accepted.

## Date

2026-06-17

## Group

Quality.

## Context

The cross-engine **Verification** pages (established by
[`test-suite-and-validation`](test-suite-and-validation.md) §6, and
built as `.py` sources per
[`notebook-generation`](notebook-generation.md)) serve two roles at
once: each page is a **regression test** (its calculated pattern is
checked against a frozen FullProf reference) and a **published HTML
doc** (it renders a comparison and an agreement table for scientists).

Historically that dual role was controlled by two separate mechanisms:

1. **`verify.assert_patterns_agree(..., raise_on_failure=...)`** — the
   per-page agreement check. With the default `raise_on_failure=True` it
   raised `AssertionError` when any metric was out of tolerance. With
   `raise_on_failure=False` it rendered the table but did not raise.
2. **`docs/docs/verification/ci_skip.txt`** — an external list of
   notebook stems consumed by `notebook-tests`/nbmake and
   `script-tests`.

That split was confusing. Deciding "this page is known-bad, do not gate
regression on it, but still publish it" required editing a flag inside
the notebook and adding the stem (with a reason) to a separate file. The
reason a page was exempt was invisible on the rendered page.

The project owner wants a **single source of truth, set at the end of
the notebook**, with this intent:

> If a verification page is good, it is a regression test and a doc
> page. If I know its regression is bad because a feature is not
> implemented yet, I mark that page as a known discrepancy but still
> keep it as an HTML doc.

This ADR makes the notebook source own that decision and removes the
external skip list.

## Decision

### 1. One in-notebook flag is the single source of truth

The agreement check gains an intention-revealing parameter that replaces
`raise_on_failure`:

```python
verify.assert_patterns_agree(
    [('cryspy vs FullProf', reference, candidate)],
    known_discrepancy=True,
    reason='FCJ S_L/D_L not implemented in cryspy yet (issue 166)',
)
```

- `known_discrepancy=False` (**default**) asserts the patterns **agree**
  within tolerance. Out-of-tolerance metrics raise `AssertionError`. The
  page is a regression test and a doc page.
- `known_discrepancy=True` asserts the patterns **still disagree** (the
  documented known-bad state). Out-of-tolerance metrics render and pass.
  If the page unexpectedly agrees within tolerance, the check raises a
  re-gate `AssertionError`.

`reason` is required when `known_discrepancy=True`, so every exemption
is explained on the published page.

`raise_on_failure` is replaced by `known_discrepancy` (default `False`).
Beta, no shims: existing pages are migrated, not aliased.

### 1a. A re-gated discrepancy fails CI, per comparison

`known_discrepancy=True` is a **two-sided** assertion. It does not
merely silence a failure; it asserts the discrepancy is **still there**.
The moment a known-bad page starts matching within tolerance, the page
**hard-fails** with a re-gate message. A developer clears it by deleting
`known_discrepancy` / `reason` (re-gating the page) or, if the match is
spurious, by tightening the tolerance.

The assertion is evaluated **per comparison**: a
`known_discrepancy=True` call asserts that _every_ listed
`(label, reference, candidate)` comparison still disagrees, and re-gates
if **any** of them now agrees. This stops a known-bad comparison from
masking a regression in an expected-good one that shares the same call —
for example a page that overlays both engines where one matches the
reference and the other does not. Expected-good comparisons therefore
stay in their own default (gated) `assert_patterns_agree(...)` call, and
only the genuinely known-bad comparisons carry `known_discrepancy=True`.

### 1b. Return value means "expectation met"

`assert_patterns_agree` returns `True` when the assertion holds:
patterns agree for a default page, or patterns still disagree for a
`known_discrepancy=True` page. Otherwise it raises `AssertionError`.

The return value is no longer the raw agreement boolean. Callers that
need raw metrics continue to use `verify.pattern_closeness(...)`.

### 2. Delete `ci_skip.txt` and derive runner behavior from source

A page that runs to completion is handled entirely from its in-notebook
flag:

- `notebook-tests`/nbmake executes every page. A
  `known_discrepancy=True` page renders and runs its two-sided
  assertion: still-discrepant pages pass; pages that start agreeing
  hard-fail and force manual re-gating.
- `script-tests` statically detects `known_discrepancy=True` in the page
  source and skips that page, so the fast runner does not spend time on
  known-bad refinement fits that it cannot use as regression gates.

No external list is needed. `docs/docs/verification/ci_skip.txt` and the
nbmake `xfail` hook are removed. The script-test runner skips pages only
from an in-source `known_discrepancy=True` literal or an in-source
`raises-exception` cell tag (Decision 3).

### 3. Pages that error before the flag use a cell tag

An end-of-notebook flag can only govern a notebook that reaches the end.
A page that raises mid-execution (for example because it needs an
unreleased calculator API) never reaches `assert_patterns_agree`.

Those temporary pages tag the failing cell `raises-exception` in the
Jupytext source (`# %% tags=["raises-exception"]`) and include a short
markdown note explaining why. nbmake executes the notebook and allows
only the tagged cell to raise; `script-tests` statically detects the tag
and skips the page because subprocess execution cannot enforce
cell-level precision.

### 4. `reason` is on-page provenance

The old `ci_skip.txt` comments move into `reason=` (or the
`raises-exception` companion note), so the explanation is visible in the
published page and travels with the code that sets it.

### 5. No fit section on pages that already agree

A verification page includes a refinement (`fit`) section only when the
raw calculation does **not** match the reference within tolerance and a
fit is needed to reach agreement, or when a `known_discrepancy=True`
page needs to show how the engine can match with its own parameters. A
page whose calculated pattern already agrees within tolerance just
calculates and asserts.

## Consequences

### Positive

- **One place, in the notebook.** Whether a page gates regression is
  decided where the page is authored, next to the data it checks.
- **Provenance is public.** The exemption reason renders on the page
  instead of hiding in a list file.
- **Approved pages are unchanged and still regression-checked** in both
  runners.
- **Fixed pages cannot stay silently exempt.** A known-bad page that
  starts agreeing hard-fails in nbmake, forcing manual re-gating.
- **The fast runner stays fast.** `script-tests` skips known-bad and
  crash pages from in-source declarations, while nbmake still executes
  and renders every page.

### Trade-offs

- Known-bad pages are exercised by nbmake rather than `script-tests`, so
  setup errors unique to those pages surface in the slower pass.
- The `raises-exception` boundary must be applied per failing cell.
- Static detection of `known_discrepancy=True` and `raises-exception`
  must inspect the actual call/marker, not a loose substring.

## Compatibility

- Beta, no shims. Every verification page that used
  `raise_on_failure=False` is migrated with an explicit per-page
  decision: either re-gate by removing the flag, or keep
  `known_discrepancy=True, reason=...`.
- `notebook-generation` is unaffected: sources remain `.py` files; any
  `raises-exception` tag is expressed in the `.py` and regenerated into
  the notebook via `notebook-prepare`.
- Revises [`test-suite-and-validation`](test-suite-and-validation.md) §6
  and removes the old `ci_skip.txt`/conftest wiring described by the
  documentation test workflow.

## Alternatives Considered

### Keep both mechanisms

Rejected. Two places to edit and the reason stays invisible on the page.

### Keep an external list as the source of truth

Rejected. The decision then lives outside the notebook, opposite to the
desired authoring model.

### Notebook-level metadata

Rejected as the primary mechanism. It is not near the agreement check,
is not visible in the rendered page, and still needs a separate rendered
reason. The narrower per-cell `raises-exception` tag is retained only
for pre-flag crashes.

### A separate render-only function

Rejected. Two functions double the surface and still need a way to make
fixed known-bad pages fail CI.

## Resolved Questions

- **Naming:** `known_discrepancy=True` was chosen because it is longer
  but self-descriptive at the call site.
- **Fast-runner speed:** `script-tests` skips known-discrepancy pages by
  statically reading the in-source flag; nbmake still executes them.
- **Re-enable signal:** a known-discrepancy page that starts agreeing
  hard-fails CI instead of warning.

## Deferred Work

- Any future speed optimization must stay derived from the in-source
  flag/tag, not reintroduce an external semantic list.
- Software and engine version provenance is covered by
  [`verification-software-version-labels`](verification-software-version-labels.md).
