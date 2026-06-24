# ADR: Software Version Labels on Verification Pages

## Status

Accepted.

## Date

2026-06-17

## Group

Quality.

## Context

The cross-engine **Verification** pages (established by
[`test-suite-and-validation`](test-suite-and-validation.md) §6) overlay
an EasyDiffraction calculator on a frozen FullProf reference and score
the agreement. A scientist reading such a page — or revisiting it after
an engine update — needs to know **which versions of software produced
the curves**, because cross-engine agreement is version dependent. The
Bérar–Baldinozzi case (issue 166) is the clearest example: whether
cryspy and FullProf agree depends on the exact cryspy build, so a page
that does not state its versions cannot be reproduced or trusted over
time.

Today this **provenance is incomplete and inconsistent**:

- The **reference** is labelled with the FullProf version on **some**
  pages via
  `FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)`
  (the version is parsed from the FullProf `.sum`), but **not all**
  pages use it.
- The **candidate** is a bare string — `candidate_label='edi-cryspy'` or
  `'edi-crysfml'` — carrying **no version** for either EasyDiffraction
  or the calculator engine.

So a reader cannot tell which EasyDiffraction release, which cryspy /
crysfml build, or (on some pages) which FullProf version a comparison
reflects.

## Decision

### 1. Every comparison shows the versions of all three components

Each verification comparison renders the versions of (a) FullProf, (b)
EasyDiffraction, and (c) the engine that produced each curve, so
provenance is **visible in the published HTML** and travels with the
page. The versions appear in **both** label surfaces a page already has,
not just one:

- the **plot legend** — the `reference_label` / `candidate_label`
  arguments of `display.pattern_comparison` (and the single-crystal
  reflection equivalent); and
- the **agreement table** — the single `label` element of each
  `(label, reference, candidate)` triple passed to
  `verify.assert_patterns_agree`, which is rendered verbatim in the
  table's `Comparison` column and echoed in the `AssertionError` failure
  message (`src/easydiffraction/analysis/verification.py`).

`assert_patterns_agree` takes **one** comparison label per row, not
separate reference and candidate labels. So its label must be a
**combined** string that names **both** sides — the versioned candidate
and the versioned reference — e.g.
`edi X.Y.Z (cryspy X.Y.Z) vs FullProf X.YZ`. Using the candidate label
alone there would show the EasyDiffraction and engine versions but
**omit FullProf**, defeating the "all three components" goal on that
surface. The page composes the row label as
`f'{candidate_label} vs {reference_label}'` from the same component
labels it uses in the legend (`candidate_label` from
`verify.engine_label`, `reference_label` from `verify.fullprof_label`),
so the legend and the table draw from identical strings and cannot
drift.

### 2. Canonical label formats

Version numbers are rendered **bare** (`X.Y.Z`), with **no `v` prefix**,
across all three components so the labels read uniformly:

- **Reference** → `FullProf X.YZ`, produced by `verify.fullprof_label`
  (the FullProf version parsed from the `.sum`), applied **consistently
  on every page** — not just where it is used today. `fullprof_label`
  currently emits `FullProf vX.YZ`; it is changed to drop the `v` so the
  reference matches the bare candidate style (see Compatibility).
- **Candidate** → `edi X.Y.Z (cryspy X.Y.Z)`, and likewise
  `edi X.Y.Z (crysfml X.Y.Z)`, replacing the bare `edi-cryspy` /
  `edi-crysfml`. The EasyDiffraction version comes first because it is
  the package under test; the engine version is the one it drove the
  calculation with.

### 2a. Pre-release / dev builds

A dev or pre-release install keeps its **dev marker** visible (so a
dev-build comparison is not mistaken for a released one) while dropping
only a **pure VCS-hash local segment** (`+g<hex>`) to keep the label
readable. Concretely, this project's versioningit emits the dev signal
in the _local_ segment — `{base}+dev{N}`, `{base}+dirty{N}`,
`{base}+devdirty{N}` (see `pyproject.toml` `[tool.versioningit.format]`)
— so those markers are **preserved verbatim**: an `edi` install of
`1.2.3+dev3` renders `edi 1.2.3+dev3`. A pure git-hash local part such
as `0.11.0.dev3+g1a2b3c` is trimmed to `edi 0.11.0.dev3`. The same rule
applies to any engine package. (A public-segment-only formatter such as
`stripped_package_version` is deliberately **not** used here: it would
discard the `+dev*`/`+dirty*` local markers and make a dev build look
released.)

### 3. A `verify` helper builds the candidate label from an explicit engine tag

A single helper — `verify.engine_label(engine, note=None)` — returns the
**candidate** string only (the reference side stays the existing
`verify.fullprof_label`, so the two single-purpose helpers mirror each
other). The optional free-text `note` annotates the candidate inside the
parentheses (for example `note='refined'`, `note='scale only'`,
`note='scale + ext radius'`), generalising what would otherwise be a
boolean `refined` flag so the real pages' varied annotations are all
expressible. It builds the candidate string from:

- the **EasyDiffraction** package version
  (`importlib.metadata.version('easydiffraction')`), and
- the **named calculator engine's** version (see Decision 3a).

The engine is passed **explicitly as a tag** (`'cryspy'`, `'crysfml'`),
**not** read from `experiment.calculator.type` at render time. This is a
deliberate contract choice: a verification page computes one engine's
curve, stores it, **switches the calculator**, computes the next, then
compares the **stored** arrays together (e.g.
`docs/docs/verification/pd-neut-cwl_LBCO_basic.py` calculates with
`cryspy`, switches to `crysfml`, then renders both stored results). A
helper that read the _active_ engine at render time would label a stored
`cryspy` result with whichever engine happened to be active later —
silently wrong provenance. Binding the label to an explicit tag keeps it
aligned with the engine that actually produced the curve.

In practice the page captures the label **once, immediately after each
calculation**, alongside the engine tag it already passes to
`verify.calculate_pattern(project, experiment, engine)` /
`verify.calculate_reflections(...)`, and reuses that stored candidate
label both as the legend `candidate_label` and as the candidate half of
the combined agreement-table row label
(`f'{candidate_label} vs {reference_label}'`, Decision 1). The same tag
drives the calculation and the label, so they cannot diverge.

### 3a. Engine version source: the existing engine→package map

Each engine's version is resolved through the project's shared
engine-to-package map `SOFTWARE_PACKAGE_BY_ENGINE` in
`src/easydiffraction/utils/utils.py`, which maps `'cryspy' → 'cryspy'`
and `'crysfml' → 'crysfml'` and is read with `importlib.metadata`
(`package_version`). The map lives in `utils.utils` so both the fit
provenance path (`analysis.py`, which stamps the **raw** version into
CIF) and the `verify` label helper draw from one place without `verify`
importing heavy `analysis.py`; a new engine is covered by adding one map
entry. The per-caller difference is purely formatting: `analysis.py`
records the raw version, while `verify.engine_label` renders the display
form (Decision 2a — keep dev markers, trim a `+g<hex>` tail) via a small
`_label_version` helper.

**Unknown-version behaviour.** If an engine's package version cannot be
resolved (no installed metadata), the helper renders an **explicit,
visible marker** — e.g. `edi X.Y.Z (crysfml ?)` — and never silently
drops the engine version. A missing version is a provenance gap and must
be obvious on the page, consistent with the project's no-silent-failures
principle. This is a render path (it produces a published doc), so it
must not hard-fail the page; the visible marker is the deliberate
fallback.

### 4. Refined-candidate labels keep the version

Where a page shows both a raw and a refined candidate (e.g.
`edi-cryspy (refined)`), the version is preserved:
`edi X.Y.Z (cryspy X.Y.Z, refined)`.

## Consequences

### Positive

- **Reproducible provenance.** Every page states the exact FullProf,
  EasyDiffraction, and engine versions behind its curves; a future
  reader (or a re-run after an engine bump) can tell what was compared.
- **Cross-engine discrepancies become interpretable.** Issue-166-style
  "cryspy disagrees with FullProf" notes are anchored to concrete
  versions instead of "some build".
- **Consistency.** The FullProf label stops being optional; one helper
  drives the candidate label so every page is uniform.
- Labels are **live**: bumping EasyDiffraction or an engine updates the
  rendered versions automatically on regeneration, with no per-page
  edit.

### Trade-offs

- Regenerated notebooks (`notebook-prepare --overwrite`) will show
  **version churn** in their committed outputs whenever a version bumps
  — expected and desirable (it is the provenance), but it does mean the
  `.ipynb` diffs include version strings.
- The helper must resolve each engine's version robustly; an engine
  without a discoverable version renders the visible fallback marker
  defined in Decision 3a.

### Compatibility

- Beta, no shims: the bare `candidate_label='edi-cryspy'` /
  `'edi-crysfml'` literals are replaced by the helper on every
  verification page; `fullprof_label` is added where missing.
- `verify.fullprof_label` changes its output from `FullProf vX.YZ` to
  `FullProf X.YZ` (drop the `v`, Decision 2). Beta, no shims: every page
  already calling it re-renders with the bare label on regeneration; its
  docstring example is updated to match. (The underlying
  `fullprof_version` parser is unchanged — only the label formatting.)
- `notebook-generation` is unaffected: the label is computed in the
  `.py` source and regenerated into the notebook.

## Alternatives Considered

### Keep bare `edi-cryspy` / `edi-crysfml`

No versions at all. Rejected: defeats the provenance purpose and makes
version-dependent agreement (issue 166) unreproducible.

### Record versions in notebook metadata only

Stash versions in `.ipynb` metadata rather than the visible label.
Rejected: invisible to a reader of the rendered page, and splits the
provenance away from the comparison it describes.

### Hard-code version strings in each page

Write the versions as literals next to each label. Rejected: drifts
silently the moment any component is upgraded; the helper keeps them
live.

## Open Questions

All questions are now **resolved** (owner decision); recorded here so
the rationale is not lost:

- **Engine version source — resolved (Decision 3a).** Versions come from
  the shared `SOFTWARE_PACKAGE_BY_ENGINE` map in `utils.utils`
  (`importlib.metadata` via `package_version`), with a visible
  `crysfml ?`-style marker when a version is unresolvable — no
  engine-specific API, no silent omission, no page hard-fail. The fit
  provenance path in `analysis.py` reads the same map (raw version for
  CIF); `verify` renders the display form.
- **Label binding — resolved (Decision 3).** The helper takes an
  explicit engine tag, not `experiment.calculator.type`, so a stored
  result keeps the version of the engine that produced it.
- **Helper name — resolved: `verify.engine_label(engine, note=None)`,
  candidate only (Decision 3).** The reference side stays
  `verify.fullprof_label`; the two small single-purpose helpers mirror
  each other and the page composes the combined table label from both.
  No single dual-return call (it would couple engine-version logic to
  `.sum` parsing). The free-text `note` generalises a boolean `refined`
  so annotations like `scale only` are expressible.
- **Render location — resolved: legend + agreement-table label only
  (Decision 1).** No separate provenance caption/row; the versions live
  on the two label surfaces a page already has, reusing existing label
  plumbing.
- **Format — resolved: bare `X.Y.Z`, no `v` prefix (Decision 2), applied
  to all three components.** `fullprof_label` drops its `v` to match
  (Compatibility). Pre-release/dev builds **keep** this repo's local dev
  markers (`+dev*`/`+dirty*`/`+devdirty*`) and trim only a pure
  `+g<hex>` VCS-hash tail (Decision 2a); `stripped_package_version` is
  not used because it would drop those markers.

## Deferred Work

- Applying the helper across every verification `.py` and regenerating
  notebooks belongs to the implementation plan, not this ADR.
- Relationship to the verification regression-gating change is only
  adjacent: see
  [`verification-regression-flag`](verification-regression-flag.md),
  which flagged this provenance gap; the two can ship independently.
