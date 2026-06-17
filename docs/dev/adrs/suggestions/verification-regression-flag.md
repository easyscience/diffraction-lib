# ADR: Notebook-Owned Verification Regression Gating

## Status

Proposed.

## Date

2026-06-17

## Group

Quality.

## Context

The cross-engine **Verification** pages (established by
[`test-suite-and-validation`](accepted/test-suite-and-validation.md) §6,
and built as `.py` sources per
[`notebook-generation`](accepted/notebook-generation.md)) serve two
roles at once: each page is a **regression test** (its calculated
pattern is checked against a frozen FullProf reference) and a
**published HTML doc** (it renders a comparison and an agreement table
for scientists).

Today that dual role is controlled by **two separate mechanisms**, and a
single page can need both:

1. **`verify.assert_patterns_agree(..., raise_on_failure=…)`** — the
   per-page agreement check. With the default `raise_on_failure=True` it
   raises `AssertionError` when any metric is out of tolerance, which is
   what makes the page a regression test. With `raise_on_failure=False`
   it renders the table but does not raise.
2. **`docs/docs/verification/ci_skip.txt`** — an external list of
   notebook stems, consumed by two runners:
   - `docs/docs/conftest.py` marks listed notebooks **`xfail`
     (`strict=False`)** for `notebook-tests`/nbmake — they still execute
     and render, but a failure is tolerated;
   - `tools/test_scripts.py` **`pytest.skip`s** them in `script-tests`
     (the fast runner that executes each page's `.py` as a subprocess
     and fails if it raises).

This split is confusing: deciding "this page is known-bad, do not gate
regression on it, but still publish it" requires editing a flag inside
the notebook **and** adding the stem (with a `# reason`) to a separate
file. The reason a page is exempt lives in `ci_skip.txt`, invisible to
readers of the published page. The PbSO₄ Bérar–Baldinozzi page
(issue 166) is the current live example: it carries both
`raise_on_failure=False` **and** a `ci_skip.txt` entry.

The project owner wants a **single source of truth, set at the end of
the notebook**, with this intent:

> If a verification page is good, it is a regression test and a doc
> page. If I know its regression is bad because a feature is not
> implemented yet, I mark that page as "not regression-gated" but still
> keep it as an HTML doc.

This ADR makes the notebook itself own that decision and removes
`ci_skip.txt`, within one boundary that is intrinsic to "decide from
inside the notebook".

## Decision

### 1. One in-notebook flag is the single source of truth

The agreement check gains an intention-revealing, **self-documenting**
parameter that subsumes `raise_on_failure`:

```python
verify.assert_patterns_agree(
    [('cryspy vs FullProf', reference, candidate)],
    regression=False,                         # known-bad: render, don't gate
    reason='FCJ S_L/D_L not implemented in cryspy yet (issue 166)',
)
```

- `regression=True` (**default**) → assert on out-of-tolerance; the page
  is a **regression test and a doc page**.
- `regression=False` → render the comparison table, **do not raise**,
  and surface `reason` in the rendered output. `reason` is **required**
  when `regression=False` so every exemption is explained on the page
  itself.

`raise_on_failure` is renamed to `regression` (its inverse). Beta, no
shims: existing pages are migrated, not aliased (see Compatibility).

### 2. Delete `ci_skip.txt` and its two consumers

For every page that **runs to completion** (the normal case — an
unimplemented feature means the engine ignores the unsupported parameter
and produces a different curve, it does not crash), the in-notebook flag
fully determines behaviour:

- `notebook-tests`/nbmake: the page executes, the `regression=False`
  check does not raise, the notebook **passes and renders** to HTML.
- `script-tests`: the `.py` subprocess completes without raising, so the
  page **passes**.

No external list is needed. `docs/docs/verification/ci_skip.txt`, the
`xfail` logic in `docs/docs/conftest.py`, and the `pytest.skip` block in
`tools/test_scripts.py` are **removed**.

### 3. Boundary: pages that error _before_ the flag use a cell tag

An end-of-notebook flag can only govern a notebook that **reaches the
end**. A page that raises mid-execution — e.g. one needing an
**unreleased** calculator API that errors rather than no-ops — never
reaches `assert_patterns_agree`, and `script-tests` fails on a raising
subprocess regardless of any flag.

For those (temporary, "waiting on a dependency release") cases the
**failing cell is tagged `raises-exception`** in the source `.py`
(jupytext cell metadata, honoured by nbmake and reproduced into the
generated notebook). This keeps control **inside the notebook** — still
one place, still no external list — and is paired with a short markdown
note stating why. A page in this state is, by definition, not currently
runnable as a regression test; tagging documents that explicitly.

### 4. `reason` replaces the `ci_skip.txt` comment as on-page provenance

The `# reason` strings currently buried in `ci_skip.txt` move into the
`reason=` argument (and the `raises-exception` companion note), so the
explanation is **visible in the published page** and travels with the
code that sets it.

## Consequences

### Positive

- **One place, in the notebook.** Whether a page gates regression is
  decided where the page is authored, at the end, next to the data it
  checks — matching the owner's mental model.
- **Provenance is public.** The exemption reason renders on the page
  instead of hiding in a list file.
- **Approved pages are unchanged and still regression-checked** in both
  runners (default `regression=True`); the dual "test + doc" role is
  preserved.
- **All pages are still generated and rendered to HTML**, exactly as
  today (this never depended on `ci_skip.txt`).
- Three coupled artifacts (`ci_skip.txt`, the conftest filter, the
  script-test skip) collapse into one library parameter.

### Trade-offs

- **Known-bad pages now run in `script-tests`** instead of being
  skipped, so the fast runner does the refinement fit for those pages
  too and gets somewhat slower. Acceptable for the current page count;
  if it ever matters, speed is a _separate_ concern from regression
  intent and must not reintroduce a second semantic list (see Open
  Questions).
- **Loss of the `xfail`/`xpass` signal.** Today a known-bad page is an
  `xfail`; if it unexpectedly starts agreeing it shows as `xpass`. Under
  this ADR a `regression=False` page simply passes, so "this known-bad
  page now actually matches — time to re-enable the gate" is no longer
  surfaced automatically. Mitigation in Open Questions (optional
  `xpass`-style warning when a `regression=False` page is within
  tolerance).
- The `raises-exception` boundary (Decision 3) is less automatic than a
  list entry and must be applied per failing cell.

### Compatibility

- Beta, no shims. Every verification `.py` is migrated:
  `raise_on_failure=False` → `regression=False, reason=…`; the implicit
  default stays "regression-gated". `ci_skip.txt` entries become
  `regression=False` flags (runnable pages) or `raises-exception` tags
  (pre-flag crashes).
- `notebook-generation` is unaffected: sources remain the `.py` files;
  the `raises-exception` tag is expressed in the `.py` and regenerated
  into the notebook via `notebook-prepare`.
- Revises
  [`test-suite-and-validation`](accepted/test-suite-and-validation.md)
  §6 (the `script-tests` "skip via `ci_skip.txt`" detail) and the
  `ci_skip.txt`/conftest wiring under
  [`documentation-ci-build`](accepted/documentation-ci-build.md). Those
  ADRs are updated when this is implemented.

## Alternatives Considered

### Keep both mechanisms (status quo)

Two places to edit, reason invisible on the page. Rejected per the
owner's explicit request for a single in-notebook control.

### Make `regression=False` (or `ci_skip`) auto-derived, keep the list

Drive `xfail`/skip from the list only and drop the per-page flag.
Rejected: the decision then lives outside the notebook, the opposite of
what is wanted, and the reason stays hidden.

### Notebook-level metadata instead of an end-of-notebook call

Encode "not regression-gated" in notebook-level metadata read at pytest
**collection** time (so even a crashing page could be `xfail`ed without
a separate file). Rejected as the primary mechanism: it is not "at the
end of the notebook like `raise_on_failure`", it is invisible in the
rendered page, and it splits the control surface between a metadata key
and the agreement call. The narrower per-cell `raises-exception` tag
(Decision 3) is preferred for the rare crash case.

### A `verify.show_patterns(...)` function distinct from

`assert_patterns_agree(...)`

Two functions — one that asserts, one that only renders — instead of one
function with a flag. Rejected: it still needs the `raises-exception`
boundary for crashes, doubles the surface, and a boolean on the existing
call is closer to the requested "like `raise_on_failure=False`" shape.

## Open Questions

- **Naming.** `regression=False` vs keeping `raise_on_failure` vs
  `gate_regression=`/`expected=`. Proposed: `regression` with a required
  `reason`.
- **Fast-runner speed.** Should `script-tests` still avoid the
  refinement fit for `regression=False` pages? Any "skip for speed" must
  be derivable from the in-notebook flag (e.g. the runner statically
  detects `regression=False` in the `.py`) so it does **not** become a
  second semantic list. Needs the page audit below.
- **Re-enable signal.** Should a `regression=False` page that is
  actually within tolerance emit a visible warning (an `xpass` analogue)
  so a fixed page gets re-gated? Proposed: yes, a non-failing warning.
- **Audit dependency.** How many current `ci_skip.txt` pages merely
  disagree (Decision 2) versus crash before the flag (Decision 3)? The
  implementation plan must classify each of the eight pages first.

## Deferred Work

- The page-by-page audit (disagree-cleanly vs crash) and the migration
  of all verification `.py` files belong to the implementation plan, not
  this ADR.
- Any static "skip slow `regression=False` pages in `script-tests`"
  optimisation is deferred until the audit shows it is needed.

### Adjacent ADR needed — show software/engine versions on verification pages

Separate from regression gating, the verification pages should record
the **provenance** of every comparison: which versions of
EasyDiffraction, the calculator engine, and FullProf produced the
curves. This is only partly done today — some pages label the reference
via
`FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)`
(the FullProf version parsed from the `.sum`), but **not all pages do**,
and the candidate is still a bare `edi-cryspy` / `edi-crysfml` with no
version.

The intended labelling is, for example:

- reference → `FullProf vX.YZ` (already via `fullprof_label`, applied
  consistently);
- candidate → `edi vX.Y.Z (cryspy vX.Y.Z)`, and likewise
  `edi vX.Y.Z (crysfml vX.Y.Z)`, instead of the current `edi-cryspy` /
  `edi-crysfml`.

This needs its **own ADR** (or an extension of the
verification-framework decision in
[`test-suite-and-validation`](accepted/test-suite-and-validation.md)
§6): a `verify` helper that builds the candidate label from the
EasyDiffraction package version and the **active calculator engine's**
version, applied on every page next to `fullprof_label`. Recorded here
only as a pointer; it is out of scope for this regression-gating ADR.
