# Plan: Software Version Labels on Verification Pages

Follows [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions to
the two-phase workflow: Phase 1 is library + page edits only (no test
authoring), Phase 2 does all test work and runs the verification suite.

## ADR

Implements
[`verification-software-version-labels`](../adrs/suggestions/verification-software-version-labels.md)
(Proposed). Per §Change Discipline it is **promoted to `accepted/`** as
part of this PR (P1.4). No new dependency is required — every version is
read through `easydiffraction.utils.utils.package_version` and formatted
for display by a small `verify` helper (`_label_version`, see
Decisions); `stripped_package_version` is **not** used, since it would
drop this repo's `+dev*`/`+dirty*`/`+devdirty*` markers.

The sibling
[`verification-regression-flag`](../adrs/suggestions/verification-regression-flag.md)
ADR is **separate work**. Both touch the same 15 verification `.py`
pages and their regenerated notebooks, so see Open Question 1 on
ordering.

## Branch + PR

- Branch: `verification-software-version-labels` (flat slug off
  `develop`). **Not yet created** — `/draft-impl-1` creates and checks
  it out off `develop` before its first commit. The current working
  branch is `verification-regression-flag`; the uncommitted ADR/plan
  edits travel onto the new branch when it is created.
- PR targets `develop`, not `master`. Do not push unless asked.

## Decisions (from the ADR)

- **All three versions, both surfaces (Decision 1).** Each comparison
  renders FullProf, EasyDiffraction, and the producing engine version in
  **both** the plot legend (`reference_label` / `candidate_label`)
  **and** the agreement table. The `assert_patterns_agree` row label is
  a **combined** string `f'{candidate_label} vs {reference_label}'` so
  all three appear there too (it takes one label per row, not a pair).
- **Bare `X.Y.Z` format (Decision 2).** No `v` prefix on any component.
  `verify.fullprof_label` changes `FullProf vX.YZ` → `FullProf X.YZ`.
  Candidate is `edi X.Y.Z (cryspy X.Y.Z)` / `edi X.Y.Z (crysfml X.Y.Z)`.
- **Dev/pre-release marker (Decision 2a).** Release plus short dev
  marker, dropping the `+g<sha>` local segment: `edi 0.11.0.dev3`.
- **Helper takes an explicit engine tag (Decision 3).**
  `verify.engine_label('cryspy', …)`, **not**
  `experiment.calculator.type` read at render time, so a stored result
  keeps the version of the engine that produced it. Candidate-only; the
  reference side stays `verify.fullprof_label`.
- **Engine version source (Decision 3a).** Resolved through the existing
  engine→package map + `importlib.metadata` path; a visible
  `crysfml ?`-style marker when a version is unresolvable (never silent,
  never a page hard-fail).
- **Refined / annotated candidates keep the version (Decision 4).** e.g.
  `edi X.Y.Z (cryspy X.Y.Z, refined)`.

## Decisions already made for this plan

- **Dev-marker formatter keeps this repo's local markers; drops only a
  git-hash tail.** This repo's versioningit config
  (`pyproject.toml [tool.versioningit.format]`) carries the dev signal
  in the **local** segment — `{base}+dev{N}`, `{base}+dirty{N}`,
  `{base}+devdirty{N}` — which `stripped_package_version` would strip,
  rendering `1.2.3+dev3` as `1.2.3` and hiding a dev build (caught in
  review 1). So `engine_label` must **not** use
  `stripped_package_version` for the EasyDiffraction version. Instead a
  small `verify` formatter (e.g. `_label_version(pkg)`) takes the
  **raw** `package_version` and **keeps** any
  `+dev*`/`+dirty*`/`+devdirty*` marker, trimming **only** a pure
  VCS-hash local part (`+g<hex>`) to honour Decision 2a's "drop the
  noisy commit hash". Net effect on this repo: `1.2.3+dev3` →
  `edi 1.2.3+dev3`; a clean release `1.2.3` → `edi 1.2.3`. The same
  formatter is applied to engine versions. `_is_dev_version` in
  `utils.utils` already encodes the `+dev`/`+dirty`/`+devdirty` marker
  detection and can back the formatter.
- **Engine→package map moves to `utils.utils` (P1.1).** Today the map
  lives as the private `_SOFTWARE_PACKAGE_BY_ENGINE` in `analysis.py`
  (with `_software_version` reading the **raw** version for CIF
  provenance stamping). To satisfy Decision 3a's "single resolution
  path" without `verification.py` importing heavy `analysis.py`, the
  **map** is extracted to `utils.utils` (which both modules already
  import and which already owns `package_version`). `analysis.py`
  imports it and keeps its existing raw-version stamping behavior
  **unchanged**; `verification.py` reads the same map but formats the
  result through the `_label_version` display helper (see the dev-marker
  decision above). The format (raw for CIF vs display for labels) is a
  per-caller choice on top of one shared map.
- **`refined: bool` is generalized to `note: str | None = None`.** Real
  pages carry more than "refined": `(scale only)`,
  `(scale + ext radius)`, `(refined)`. A boolean cannot express those,
  so the helper signature is `engine_label(engine, note=None)` →
  `edi X (cryspy X)` or `edi X (cryspy X, <note>)`. `note='refined'`
  covers Decision 4. This **refines** the ADR's `refined=False` wording;
  the ADR's Decision 3/4 text is updated to `note=` during the promotion
  step (P1.4) so ADR and code agree.
- **SC pages always get a versioned FullProf label — no bare fallback.**
  Single-crystal pages currently pass the literal
  `reference_label='FullProf'` and load
  `verify.load_fullprof_sc_f2calc(dir, '<stem>.out')`. `fullprof_label`
  accepts `.sum`/`.out`, and review 1 confirmed every SC `.out` in use
  (`tbti.out`, `prnio.out`) carries the `FullProf.2k (Version 8.40 …)`
  banner (sibling `.sum` files exist too). So all SC pages call
  `verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)` like
  the powder pages. Keeping the bare `'FullProf'` is **not** an allowed
  outcome (it would reintroduce the versionless state this work
  removes); if a banner source is ever genuinely absent, the fallback is
  a visible `FullProf ?`, never the bare label.

## Open questions

1. **Ordering vs `verification-regression-flag`.** Both edit all 15
   `docs/docs/verification/*.py` pages and regenerate the same
   notebooks, and both are in flight. Recommendation: land this
   **after** `verification-regression-flag` merges to `develop`, then
   branch this off the updated `develop`, so the label edits layer
   cleanly on the migrated pages instead of colliding. Confirm with the
   owner before `/draft-impl-1`.
2. **ADR Decision 4 wording.** The `refined`→`note` generalization above
   edits the ADR at promotion (P1.4). Flagged so the owner can veto the
   signature if a strict boolean is preferred.

_(Resolved in review 1: the SC `.out` banner question — every
single-crystal `.out` in use carries the 8.40 banner, so SC pages use
`fullprof_label` with no versionless fallback; see the SC decision
above.)_

## Concrete files likely to change

- `src/easydiffraction/utils/utils.py` — extract the engine→package map
  (e.g. `SOFTWARE_PACKAGE_BY_ENGINE`) here; it already hosts
  `package_version` / `stripped_package_version`.
- `src/easydiffraction/analysis/analysis.py` — import the shared map;
  drop the local `_SOFTWARE_PACKAGE_BY_ENGINE`; `_software_version`
  unchanged in behavior (still raw version for CIF stamping).
- `src/easydiffraction/analysis/verification.py` — add
  `engine_label(engine, note=None)`; change `fullprof_label` to emit
  `FullProf {version}` (drop `v`); update its docstring example.
- The **15** `docs/docs/verification/*.py` pages (+ regenerated `.ipynb`
  via `pixi run notebook-prepare`): replace bare
  `candidate_label='edi-cryspy'` / `'edi-crysfml'` / `'ed-cryspy'` /
  `'ed-crysfml'` (and `(refined)` / `(scale only)` /
  `(scale + ext radius)` variants) with `verify.engine_label(...)`;
  switch literal `reference_label='FullProf'` to a page
  `FULLPROF_LABEL = verify.fullprof_label(...)` where missing; build
  combined `assert_patterns_agree` row labels.
- `tests/unit/easydiffraction/analysis/test_verification.py` — Phase 2
  only: update `test_fullprof_label_formats_version` (now
  `FullProf 8.40`) and add `engine_label` cases.
- `docs/dev/adrs/suggestions/verification-software-version-labels.md` →
  `git mv` to `accepted/`; `docs/dev/adrs/index.md` row flipped to
  Accepted; links fixed.

Find every label call site first with
`git grep -nE "candidate_label|reference_label|assert_patterns_agree|fullprof_label" -- 'docs/docs/verification/*.py'`
and every map user with `git grep -n "_SOFTWARE_PACKAGE_BY_ENGINE"`.

## Implementation steps (Phase 1)

Each `- [ ]` is one atomic commit; stage only the listed paths; commit
each before the next. No `test_verification.py` changes in Phase 1 — the
existing `fullprof_label` test may be left temporarily stale (it is not
run until Phase 2).

- [x] **P1.1 — Share the engine→package map in `utils.utils`.** Move
      `_SOFTWARE_PACKAGE_BY_ENGINE` from `analysis.py` into
      `src/easydiffraction/utils/utils.py` (public
      `SOFTWARE_PACKAGE_BY_ENGINE`); import it in `analysis.py` so
      `_software_version` keeps its current raw-version behavior
      unchanged. Pure refactor, no behavior change. Commit:
      `Share engine-to-package map from utils`

- [x] **P1.2 — Add `engine_label`; make `fullprof_label` bare.** In
      `verification.py`: add a `_label_version(pkg)` formatter (raw
      `package_version`, keep `+dev*`/`+dirty*`/`+devdirty*`, trim only
      a `+g<hex>` VCS-hash tail — see the dev-marker decision above) and
      `engine_label(engine, note=None)` that builds
      `edi {edi_ver} ({engine} {engine_ver}[, {note}])` via that
      formatter and `SOFTWARE_PACKAGE_BY_ENGINE`, rendering a visible
      `{engine} ?` marker when the engine version is `None` (Decision
      3a). Change `fullprof_label` to return `f'FullProf {version}'` and
      update its docstring example. Docstrings only; no test edits.
      Commit: `Add engine_label helper and drop v from fullprof_label`

- [x] **P1.3 — Migrate the 15 verification pages.** For each
      `docs/docs/verification/*.py`: define page-level label variables
      right after each calculation
      (`LABEL_CRYSPY = verify.engine_label('cryspy')`, refined/annotated
      via `note=`), set
      `FULLPROF_LABEL = verify.fullprof_label(<dir>, <sum-or-out-file>)`
      where the reference label is still the literal `'FullProf'`, pass
      these to `pattern_comparison` / `reflection_comparison`, and build
      each `assert_patterns_agree` row label as
      `f'{LABEL_xxx} vs {FULLPROF_LABEL}'`. SC pages use
      `fullprof_label` with their `.out` (banners confirmed in review 1)
      — no bare `'FullProf'` left anywhere. Run
      `pixi run notebook-prepare`; stage the `.py` + regenerated
      `.ipynb`. Commit: `Show software versions on verification pages`

- [ ] **P1.4 — Promote the ADR.** First reconcile the ADR text with what
      was implemented: (a) update Decision 3/4 wording from
      `refined=False` to `note=None` (Open Question 3); (b) update
      **Decision 3a** and its matching resolved Open Question so they
      name the new shared map location (`SOFTWARE_PACKAGE_BY_ENGINE` in
      `utils.utils`, P1.1) instead of the old private `analysis.py`
      `_SOFTWARE_PACKAGE_BY_ENGINE`/`_software_version`, and record the
      per-caller raw-vs-display formatting split (analysis stamps the
      raw version into CIF; `verify` renders the dev-marker display form
      via `_label_version`); (c) revise **Decision 2a** and its matching
      resolved format Open Question so they describe the implemented
      display formatter — preserve this repo's configured
      `+dev*`/`+dirty*`/ `+devdirty*` local markers and trim **only** a
      pure `+g<hex>` VCS-hash suffix (the `.devN+g…` example may stay as
      the hash-trim illustration). Then `git mv`
      `docs/dev/adrs/suggestions/verification-software-version-labels.md`
      → `accepted/`; set `**Status:** Accepted`; flip its
      `docs/dev/adrs/index.md` row to Accepted with the `accepted/...`
      link; fix any links that pointed at `suggestions/...`
      (`git grep -n verification-software-version-labels`). Commit:
      `Promote verification-software-version-labels ADR to accepted`

- [ ] **P1.5 — Phase 1 review gate.** No-code; mark `[x]` and commit the
      checklist update alone. Commit: `Reach Phase 1 review gate`

## Status checklist

- [x] P1.1 share engine→package map
- [x] P1.2 engine_label + bare fullprof_label
- [x] P1.3 migrate 15 verification pages
- [ ] P1.4 promote ADR
- [ ] P1.5 Phase 1 review gate
- [ ] Phase 2 verification green

## Phase 2 — Verification

Per the two-phase workflow, Phase 2 **starts with the test work**, then
runs the verification commands.

**Step 1 — update and extend `test_verification.py` first.** Before any
`pixi run` command:

- **Update existing case.** `test_fullprof_label_formats_version` must
  now expect `'FullProf 8.40'` (no `v`).
- **Add `engine_label` cases:**
  - basic candidate string for a known engine (assert the
    `edi X.Y.Z (cryspy X.Y.Z)` shape using the installed versions);
  - `note='refined'` appends `, refined`;
  - an unresolvable engine version renders the visible `?` marker, not a
    silent omission and not a raise (monkeypatch the version lookup to
    return `None`);
  - the dev-marker behavior for this repo's configured forms
    (monkeypatch the lookup): `1.2.3+dev3`, `0.5.8+dirty3`, and
    `0.5.8+devdirty3` are **preserved** verbatim in the label (a dev
    build never collapses to its release number), while a pure VCS-hash
    tail such as `1.2.3+g1a2b3c` is trimmed to `1.2.3`.

**Step 2 — run the verification commands.** From the repo root; use the
zsh-safe log-capture when output is needed.

- `pixi run fix` (commit auto-fixes incl. regenerated
  `docs/dev/package-structure/{full,short}.md`).
- `pixi run check > /tmp/edi-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/edi-check.log; exit $check_exit_code`
- `pixi run unit-tests > /tmp/edi-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 120 /tmp/edi-unit.log; exit $unit_tests_exit_code`
- `pixi run integration-tests > /tmp/edi-int.log 2>&1; integration_tests_exit_code=$?; tail -n 120 /tmp/edi-int.log; exit $integration_tests_exit_code`
- `pixi run script-tests > /tmp/edi-script.log 2>&1; script_tests_exit_code=$?; tail -n 120 /tmp/edi-script.log; exit $script_tests_exit_code`
  (every verification page now reads live versions; confirm none fail on
  a missing FullProf banner — Open Question 2).
- `pixi run test-structure-check` (confirms no new test-layout drift
  from the added `engine_label` cases).

## Suggested Pull Request

**Title:** Every verification page now shows the exact software versions
behind its curves

**Description:** Each cross-engine verification page now states which
software produced the compared curves — the FullProf version, the
EasyDiffraction version, and the calculation engine (cryspy or crysfml)
version — right in the plot legend and the agreement table (for example
`edi 0.11.0 (cryspy 2.4.1) vs FullProf 8.40`). Because cross-engine
agreement can depend on the exact build, this makes every comparison
reproducible and lets a reader tell at a glance what was compared, even
after a later software update. The versions are read live, so they stay
correct automatically whenever a component is upgraded.
