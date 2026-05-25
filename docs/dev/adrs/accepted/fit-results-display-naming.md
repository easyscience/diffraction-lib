# ADR: Fit Results Display Naming Convention

## Status

Accepted.

## Date

2026-05-25

## Group

User-facing API.

## Context

`project.display.fit.results()` and `project.display.posterior.*` (see
[`display-ux.md`](display-ux.md)) currently emit fit-result tables with
inconsistent and sometimes long column headers across the two fitting
modes:

- **LSQ:** `📈 Fitted parameters:` with columns
  `start | fitted | uncertainty | change`.
- **Bayesian:** two tables.
  - `📈 Committed parameters:` with columns
    `start | best posterior sample | uncertainty | change`.
  - `📊 Posterior parameter summaries:` with columns
    `median | 95% interval | r-hat | ess bulk`.

Three problems:

1. `best posterior sample` (21 chars) is too wide for HTML / markdown
   layouts and forces the other columns into narrow space.
2. `uncertainty` is the column header in both LSQ and Bayesian committed
   tables but the underlying quantities differ (covariance-derived σ vs
   posterior SD). The display layer does not annotate the difference.
3. LSQ's `fitted` and Bayesian's `best posterior sample` are
   conceptually parallel (the value committed back to the project) but
   the headers do not signal that parallelism, complicating side-by-side
   reading.

Two conventions guide the cross-method naming choice:

- **IUCr CIF** prefers the `_su` suffix (standard uncertainty); `_esd`
  (estimated standard deviation) is deprecated.
- **GUM** (Guide to the Expression of Uncertainty in Measurement) treats
  Bayesian posterior SD and frequentist standard uncertainty as the same
  physical quantity — 1σ of the inferred distribution of the measurand.

Both converge on `s.u.` as the appropriate cross-method label.

[`display-ux.md`](display-ux.md) defines facade method names but not
column headers or footnotes;
[`iucr-cif-tag-alignment.md`](../suggestions/iucr-cif-tag-alignment.md)
defines persisted CIF tag names but not display labels;
[`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) defines Python
and CIF attribute names but not user-visible labels. Display naming for
fit-results tables is a real gap.

## Decision

### 1. Short headers paired with a footnote glossary

Every fit-results table emits a glossary block immediately below the
table that expands the short column headers into one-line descriptions.
The footnote disambiguates per fitting mode so the column header itself
can stay short.

### 2. Cross-method consistency where the physical quantity is the same

Same column header where the underlying physical quantity matches:

- `start` — initial parameter value, both modes.
- `value` — refined / committed value, both modes.
- `s.u.` — 1σ standard uncertainty, both modes (covariance for LSQ,
  posterior SD for Bayesian; same physical meaning per GUM).
- `change` — `value − start`, both modes.

Different headers only for Bayesian-only quantities (no LSQ analogue):
`median`, `95% CI`, `r-hat`, `ess bulk`.

### 3. Canonical column layouts and titles

**LSQ — `📈 Refined parameters:`**

```
| datablock | category | entry | parameter | units | start | value | s.u. | change |
```

Footnote:

```
start  = parameter value before refinement
value  = refined value from least-squares minimization
s.u.   = standard uncertainty (1σ), from the covariance matrix
change = relative change from start, in %; ↑ = increase, ↓ = decrease
```

**Bayesian — `📈 Committed parameters:`** (title unchanged)

```
| datablock | category | entry | parameter | units | start | value | s.u. | change |
```

Footnote:

```
start  = parameter value before sampling
value  = estimate written back to the project (best posterior sample)
s.u.   = standard uncertainty (1σ), the posterior standard deviation
change = relative change from start, in %; ↑ = increase, ↓ = decrease
```

**Bayesian — `📊 Posterior distribution:`**

```
| datablock | category | entry | parameter | units | median | 95% CI | r-hat | ess bulk |
```

Footnote:

```
median   = 50th percentile of the marginal posterior
95% CI   = 95% credible interval (2.5%–97.5%, asymmetric)
r-hat    = Gelman–Rubin diagnostic (good convergence: r-hat ≤ 1.01)
ess bulk = bulk effective sample size (typically ≥ 400)
```

### 4. Title changes from the current implementation

- `📈 Fitted parameters:` → `📈 Refined parameters:` (IUCr-style
  "refinement" wording, also matches the cross-method `value` column).
- `📈 Committed parameters:` stays unchanged — the duality of "committed
  values" vs "posterior distribution" is meaningful and worth preserving
  on the Bayesian side.
- `📊 Posterior parameter summaries:` → `📊 Posterior distribution:`
  (shorter and explicit about what the second table shows).

### 5. Chart legend convention

Chart legends use the full footnote-form name where the chart has
horizontal space. Where the plot title already signals context (e.g.
"Posterior distribution of <param>"), legends may shorten to the
table-header form:

- Posterior distribution plots: `estimate`, `median`,
  `95% credible interval`.
- Measured-vs-calculated plots: `measured`, `calculated`.

Existing chart legends that describe plot **type** (e.g.
`Marginal density`, `Posterior contours`, `Posterior samples`) are not
parameter-value labels and are out of scope for this ADR.

### 6. Internal attribute names unchanged

`Parameter.value`, `Parameter.uncertainty`,
`Parameter.posterior_uncertainty`, and every persisted CIF tag stay as
they are. This ADR governs **display strings only**, not the Python or
CIF API.

## Addendum (2026-05-25): Fit-results table replaces emoji-line summary

The original ADR specified two parameter-level tables for Bayesian fits
(`Committed parameters`, `Posterior distribution`) and one for LSQ
(`Refined parameters`), each below an emoji-line summary block
(`✅ Success: True`, `📏 Goodness-of-fit (reduced χ²): 1.29`, …). In
practice the emoji-line block grew long, mixed multi-value lines
(`📊 Convergence: status=passed, max_r_hat=1.004, …`) with single-value
lines (`📏 R-factor (Rf): 5.65%`), and split related information across
visually-different formats.

The block is now rendered as **one additional 2-column table** per fit
method, sitting directly above the parameter tables:

- LSQ: `📋 Least-squares fit results:` — title.
- Bayesian: `📋 Bayesian fit results:` — title.

Column layout: `Metric | Value`, left/right alignment. Each row carries
one emoji-prefixed metric name in the first column and one scalar value
in the second. The previous `console.paragraph('Fit results')` /
`console.paragraph('Bayesian fit results')` section header is dropped —
the table title now signals the section.

Canonical row order (top-to-bottom):

1. `🧪 Minimizer` / `🧪 Sampler` — the minimizer.type string (e.g.
   `lmfit (leastsq)`, `bumps (dream)`).
2. `✅ Overall status` — single shared value vocabulary: `success` /
   `failed`. For LSQ this mirrors `FitResults.success`. For Bayesian
   this is `success` only when the sampler completed _and_ convergence
   passed, else `failed`. Per-metric convergence detail goes in rows
   12–16 below.
3. `💬 Engine message` _(Bayesian, optional)_ — the engine's free-form
   status message, e.g. `DREAM sampling completed`.
4. `⏱️ Fitting time (seconds)` — `fitting_time`.
5. `🔁 Iterations` _(LSQ, optional)_ — shown only when
   `FitResults.iterations > 0`.
6. `📏 Goodness-of-fit (reduced χ²)` — `reduced_chi_square`. 7–10.
   `📏 R-factor (Rf, %)`, `📏 R-factor squared (Rf², %)`,
   `📏 Weighted R-factor (wR, %)`, `📏 Bragg R-factor (BR, %)` — each
   row when the corresponding inputs are available. Units appear in the
   metric name, so the value cell holds a bare number. (R-factors come
   immediately after goodness-of-fit and before `Best log-posterior` —
   both methods agree on this order.)
7. `📉 Best log-posterior` _(Bayesian, optional)_ — shown when
   `best_log_posterior is not None`. 12–16. _(Bayesian only)_
   Convergence rows derived from `convergence_diagnostics`: -
   `📊 Convergence status` — `passed` / `failed`. - `📊 Max r-hat` —
   formatted to 3 decimals. - `📊 Min ess bulk` — formatted to 1
   decimal. - `📊 Draws per chain`. - `📊 Chains`.

The shared-vocabulary `success` / `failed` for `Overall status` is
intentional cross-method consistency: a reader scanning LSQ and Bayesian
outputs side-by-side sees the same status word in the same row position
regardless of method. Bayesian-specific nuance (sampler completed but
convergence flagged, etc.) is exposed in the convergence rows below.

**Rows dropped relative to the previous emoji-line summary:**

- `🎯 Committed point estimate: Best posterior sample` — already
  documented by the `Committed parameters` table footnote
  (`value = estimate written back to the project (best posterior sample)`).
- `🔁 Sampler completed: yes` — redundant with `Overall status`.
- `⚙️ Sampler settings: steps=…, burn=…, …` — already in the
  `Settings used` table above the fit-results table.
- The derived `samples = n_draws × n_chains` count — derived from the
  `Draws per chain` and `Chains` rows immediately below.

**Table-title icons.** The four fit-output tables now carry a
distinguishing icon in their title so the four blocks are visually
separable when scrolling:

| Table                             | Title prefix                                                 |
| --------------------------------- | ------------------------------------------------------------ |
| Minimizer settings                | `⚙️ Settings used:`                                          |
| Fit-method summary                | `📋 Least-squares fit results:` / `📋 Bayesian fit results:` |
| Committed values                  | `📈 Refined parameters:` / `📈 Committed parameters:`        |
| Posterior summary (Bayesian only) | `📊 Posterior distribution:`                                 |

The icons are also the same emoji used inside the rows of the
corresponding fit-results-summary table (📏 for goodness-of-fit metrics,
📊 for convergence diagnostics), so the visual language is internally
consistent.

**Internal-implementation note.** Helper `print_metrics_table(rows)` in
`easydiffraction.utils.utils` renders the new 2-column table from a list
of `[label, value]` rows. Both `reporting.FitResults.display_results()`
and `bayesian.BayesianFitResults.display_results()` build their rows via
a `_build_fit_results_rows()` instance method and feed
`print_metrics_table()`. The shared signature keeps the two methods
structurally parallel.

## Consequences

### Positive

- Tables fit standard HTML / markdown width without truncating the
  formerly 21-character `best posterior sample` column.
- Users can compare LSQ and Bayesian results column-by-column (`start`,
  `value`, `s.u.`, `change` line up identically).
- IUCr / GUM-aligned terminology.
- The inline footnote glossary gives non-programmer users a
  discoverability path without having to leave the table to read
  external docs.
- Setting the convention in an ADR keeps future fit-result tables (a new
  sampler, an alternative refinement strategy) on the same naming.

### Trade-offs

- Existing tutorials, tests, and integration outputs that pin the
  literal strings `Fitted parameters`, `Posterior parameter summaries`,
  `fitted`, `best posterior sample`, `uncertainty`, `95% interval` need
  updating in the implementation PR.
- `s.u.` is unfamiliar to readers who do not know GUM or IUCr CIF. The
  footnote covers this; the compactness win at the column header is the
  main argument.

### ADRs related to this ADR

None directly amended. This ADR complements:

- [`display-ux.md`](display-ux.md) — defines facade method names; this
  ADR fills in the column-header layer underneath.
- [`iucr-cif-tag-alignment.md`](../suggestions/iucr-cif-tag-alignment.md)
  — defines persisted CIF tag names; this ADR is the matching
  display-time label layer.
- [`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) — defines
  Python / CIF attribute names (e.g. `Parameter.uncertainty`,
  `posterior_uncertainty`); display headers map to those without
  renaming them.

## Alternatives Considered

### A. Keep `uncertainty` as the column header for both modes

Pros: zero changes. Cons: ambiguous in Bayesian context (users may
confuse it with the 95% credible interval below); inconsistent with the
IUCr CIF `_su` convention; reinforces the wider `best posterior sample`
problem because it does not solve the layout issue.

### B. `posterior SD` for Bayesian, `uncertainty` for LSQ

Pros: explicit on the Bayesian side. Cons: different column headers for
the same physical quantity (1σ width), breaking the column-by-column
comparison; longer (10 chars vs 4 for `s.u.`).

### C. Different headers for the committed-value column (`refined` vs

`estimate` vs `value`)

Three different headers for "the value committed to the project". Pros:
each method-accurate. Cons: breaks the cross-method consistency goal;
readers seeing `refined` next to `estimate` in side-by-side tables
wonder what the semantic difference is even though the underlying
quantity is the same. Decision: use neutral `value` everywhere, let the
footnote disambiguate.

### D. Single Bayesian table covering both committed values and

posterior summary

Pros: one table to read. Cons: nine value columns plus identity columns
exceed standard HTML width and truncate. The two-table split is forced
by layout and meaningfully preserves the "what did I commit" vs "what
does the posterior look like" duality.

## Deferred Work

- The `acceptance rate` column in the posterior distribution table. Not
  displayed by default today; a future ADR can decide whether it joins
  the canonical layout or stays in a verbose mode.
- Inline footnote text vs Markdown link to a docs-site glossary. Inline
  is the initial form; promotion to a glossary page is a future ADR if
  footnote lengths grow.
- Localisation. All display strings are English; non-English UIs are out
  of scope.
