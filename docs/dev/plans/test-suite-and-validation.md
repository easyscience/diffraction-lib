# Plan: Test Suite and Validation Strategy

This plan follows [`AGENTS.md`](../../../AGENTS.md) with one **declared
exception** to the two-phase workflow. [`AGENTS.md`](../../../AGENTS.md)
§Workflow keeps test creation in Phase 2 ("Phase 1 — Code and docs
updates only ... Do not create or run tests unless the user explicitly
asks"). Because this ADR's subject *is* the test suite, Phase 1 here
necessarily includes test relocation, shared fixtures, new unit/property
tests, and benchmark tests as implementation work — deferring them to
verification would leave Phase 1 empty of its actual deliverable. The
implementer running `/draft-impl-1` will therefore edit and add files
under `tests/**` during Phase 1. Phase 2 remains the standard
verification gate (`pixi run fix`/`check`/`unit-tests`/
`integration-tests`/`script-tests`) and does not author new test
suites.

A scope decision is also recorded below (§Scope): the cross-repository
work is documented for the future rather than implemented in this
branch, per the author's instruction.

## ADR

Implements the suggestion ADR
[`test-suite-and-validation.md`](../adrs/suggestions/test-suite-and-validation.md)
(drafted via `/draft-adr`; review cycle closed). The plan owns this ADR.
Per [`AGENTS.md`](../../../AGENTS.md) §Change Discipline, the ADR is
promoted from `suggestions/` to `accepted/` as part of this change,
before the PR is opened (step P1.15).

Coordinated, not implemented here:
[`documentation-ci-build.md`](../adrs/suggestions/documentation-ci-build.md)
(stays a suggestion; this plan implements only its strict-build, link,
and spelling subset for the every-push test workflow — see §Open
questions).

Amends the accepted
[`test-strategy.md`](../adrs/accepted/test-strategy.md) (sharper layer
definitions).

## Branch and PR

- Branch: `test-suite-and-validation` (already checked out, created off
  `develop`).
- PR target: `develop`.
- Do not push the branch until asked.

## Scope

**In scope (all in-repository ADR work):** §1 strict layers +
relocation, §2 cost-tier markers, §3 structure-check CI gate, §4
coverage target + `hypothesis`, §5 codecov policy, §6 engine support
matrix + cross-engine (cryspy ↔ crysfml) calculation-only comparison
pages, §7 `pytest-benchmark` suite, §9 fast docs build gate.

**Documented for the future (cross-repository, NOT implemented here):**
- §8 nightly COD corpus harness, its results database, and the
  pip-install acceptance CI job that writes results back to the
  `diffraction` data repository.
- §8 generative random-structure fuzzing (already ADR-deferred).
- §7 benchmark baseline history committed to the `diffraction` data
  repository, and any performance regression gate.
- §6 external-software comparison (FullProf/GSAS-II) via zipped projects
  stored in the `diffraction` data repository.

These are captured in step P1.14 (a future-work record in
`docs/dev/issues/open.md`) and remain in the ADR's Deferred Work.

## Decisions (already made)

- **Layers (§1):** functional is in-process with bundled fixtures only —
  **no real calculation engine and no network/`download_data()`**; those
  move to integration. A test goes to the lowest layer whose constraints
  it can satisfy.
- **Markers (§2):** opt-in escalation. Default (unmarked) = fast.
  Add `@pytest.mark.pr` (PR + `develop`/`master`) and
  `@pytest.mark.nightly` (scheduled only). **Retire the current `fast`
  marker** (6 integration files). CI selection:
  `not pr and not nightly` (feature push) / `not nightly` (PR + main) /
  all (nightly schedule). Because markers are **orthogonal to layers**,
  the selected expression is applied to **every** pytest invocation under
  the policy — unit, functional, and integration, in both the source and
  package CI jobs — not to integration alone as today. The **integration
  layer defaults to the `pr` tier** (auto-marked once in
  `tests/integration/conftest.py`) because every integration test uses a
  real engine; unit/functional default to fast and escalate individually.
- **Structure gate (§3):** unify on a single `src/` tree walk shared by
  `tools/generate_package_docs.py` and `tools/test_structure_check.py`;
  run the check in CI as a gate.
- **Coverage (§4):** raise `fail_under` 65 → 80 (ramp to 90–95 later).
  Adopt `hypothesis` (approved) in a deterministic profile; input-domain
  tests target the validators in `core/validation.py`. One documented
  numeric-tolerance convention via a root `tests/conftest.py`.
- **Codecov (§5):** unit-only upload (unchanged), `patch` →
  `informational: true`, `project` → target 80% blocking. No new upload
  path.
- **Verification (§6):** calculation-only (no minimisation) cross-engine
  comparison pages with profile-difference / max-deviation /
  integrated-intensity metrics and overlay plots; new top-level
  `Verification` nav node; pages double as `script-tests`. Engine
  support matrix declared first.
- **Benchmarks (§7):** `pytest-benchmark` (approved), per
  `beam_mode × radiation_probe × engine`, `nightly`-marked, output as a
  CI artifact; informational.
- **Docs gate (§9):** fast every-push job in `test.yml` — strict
  `mkdocs build` (no tutorial execution), link check (`lychee`), spell
  check (`codespell`) — separate from the slow `docs.yml`.
- **Dependencies named for pre-approval** (per
  [`AGENTS.md`](../../../AGENTS.md) §Architecture): `hypothesis`,
  `pytest-benchmark`, `codespell` (dev dependencies); `lychee` (CI
  link-checker, GitHub Action or binary — no Python dependency).

## Open questions

1. **Engine support matrix — extend existing metadata (§6, P1.11).** The
   `TypeInfo`/`Compatibility`/`CalculatorSupport` dataclasses already
   exist in `src/easydiffraction/core/metadata.py` (lines 19, 40, 88)
   and are populated per instrument category (e.g.
   `datablocks/experiment/categories/instrument/cwl.py` declares
   `compatibility` and `calculator_support`). P1.11 therefore *applies
   and extends* this model — notably adding `radiation_probe` to
   `Compatibility` if missing, and exposing a query to enumerate
   comparable engine × condition combinations — rather than introducing
   new classes. **Stop and ask** about a dedicated ADR only if extending
   the metadata shape proves structural (a broad change to
   `Compatibility`).
2. **`fail_under = 80` feasibility (§4, P1.9).** Current unit-only
   coverage is unverified against 80. If Phase 2 shows it below 80 after
   the new tests, either add more unit tests or set a documented
   intermediate value and ramp — decide in Phase 2, do not silence the
   gate.
3. **`documentation-ci-build` promotion (§9).** The ADR text says
   promoting it "is part of this work," but this plan implements only a
   subset (strict build + link + spell). Recommendation: keep it a
   suggestion and cross-reference; revisit promotion when its remaining
   items (mkdocstrings, snippet smoke tests, notebook-freshness) land.
4. **`lychee` packaging.** GitHub Action vs pinned binary in the pixi
   environment — pick during P1.10.
5. **Location of the strict-criteria testing guide and the
   tolerance-convention text (§1/§4).** A new `docs/dev/` testing guide
   vs extending the amended `test-strategy.md` — decide in P1.5.

## Concrete files likely to change

- `.codecov.yml` (status config)
- `pyproject.toml` (`[tool.pytest.ini_options].markers`,
  `[tool.coverage.report].fail_under`, `hypothesis`/`codespell` config,
  dev dependencies)
- `pixi.toml` (new tasks: `docs-build-strict`, `link-check`,
  `spell-check`, `benchmarks`; structure-check wiring; deps)
- `.github/workflows/test.yml` (marker selection, nightly scheduled job,
  strict-docs job, structure-check gate)
- `tools/test_structure_check.py`, `tools/generate_package_docs.py`
  (shared tree walk)
- `tests/conftest.py` (new: seeded RNG + tolerance fixtures)
- `tests/functional/**`, `tests/integration/**`, `tests/unit/**`
  (relocation; remove `fast` marks; new property tests)
- `tests/integration/fitting/*.py` (6 files: remove `@pytest.mark.fast`)
- `tests/benchmarks/**` (new: `nightly` benchmarks)
- `src/easydiffraction/core/metadata.py`,
  `src/easydiffraction/datablocks/experiment/categories/instrument/**`,
  `src/easydiffraction/analysis/calculators/**` (engine support matrix —
  extend existing `Compatibility`/`CalculatorSupport`)
- `src/easydiffraction/core/validation.py` (property-test target; expose
  domains if needed)
- `docs/mkdocs.yml` (Verification nav node)
- `docs/docs/verification/*.py` (new comparison tutorials)
- `docs/dev/adrs/suggestions/test-suite-and-validation.md` → `accepted/`
  (promotion); `docs/dev/adrs/index.md` (status flip)
- `docs/dev/issues/open.md` (cross-repo future-work record)
- new config: `.codespellrc` (or `[tool.codespell]`), `lychee` config

## Implementation discipline

When an AI agent follows this plan, **every completed Phase 1 step must
be staged with explicit paths and committed locally before moving to the
next step or the Phase 1 review gate**, per
[`AGENTS.md`](../../../AGENTS.md) §Commits. Keep commits atomic,
single-purpose, and aligned to the step. Do not stage unrelated dirty
files or generated artifacts. Do not run Phase 2 commands during Phase 1.

## Implementation steps (Phase 1)

- [x] **P1.1 — Codecov status policy (§5)**
  Edit `.codecov.yml`: add `informational: true` to `patch.default`; set
  `project.default` to `target: 80%`, `informational: false`. Leave the
  unit-only upload untouched.
  Files: `.codecov.yml`.
  Commit: `Make codecov patch informational and gate project at 80%`

- [x] **P1.2 — Cost-tier markers and test retagging (§2)**
  Register `pr` and `nightly` markers in
  `[tool.pytest.ini_options].markers`; remove the `fast` marker
  definition. Remove `@pytest.mark.fast` from the 6
  `tests/integration/fitting/*.py` files (retag the genuinely heavy ones
  with `pr` where appropriate).
  Files: `pyproject.toml`, `tests/integration/fitting/*.py`.
  Commit: `Replace fast marker with pr and nightly test tiers`

- [x] **P1.3 — CI marker selection across all layers and nightly job (§2)**
  Update `.github/workflows/test.yml` mark logic to
  `-m "not pr and not nightly"` (feature push) and `-m "not nightly"`
  (PR + `develop`/`master`), and apply the selected expression to
  **every** pytest invocation in both the source-test and package-test
  jobs — unit, functional, and integration (today `-m` reaches only the
  integration runs at lines 132 and 311; unit/functional run unfiltered).
  Thread a marker passthrough into the `unit-tests` and `functional-tests`
  pixi tasks (the `integration-tests` task already accepts an appended
  expression). Add a `schedule:` trigger and a nightly job running
  `-m nightly`.
  Files: `.github/workflows/test.yml`, `pixi.toml`.
  Commit: `Select test tiers per trigger across all test layers`

- [x] **P1.4 — Unify src-tree walk and gate structure check (§3)**
  Extract the `src/` enumeration so `tools/test_structure_check.py` and
  `tools/generate_package_docs.py` share one walker; add the check to CI
  (lint/format or test workflow) as a blocking gate.
  Files: `tools/test_structure_check.py`,
  `tools/generate_package_docs.py`, `.github/workflows/*.yml`,
  `pixi.toml`.
  Commit: `Gate unit-test structure check on shared src tree walk`

- [x] **P1.5 — Strict layer-criteria testing guide (§1)**
  Write the may/must-not criteria and the "where does this test go?"
  decision list (location per Open question 5), and tighten the layer
  wording referenced by the amended `test-strategy.md`.
  Files: new `docs/dev/` testing guide (or `test-strategy.md` update).
  Commit: `Document strict test layer placement criteria`

- [x] **P1.6 — Test relocation pass (§1)**
  Move functional tests that call real `download_data()` into
  integration; relocate or correctly mark slow/engine/network-touching
  unit tests (the 16 `download_data()` unit call sites must be explicit
  mocks or move out). Keep `test-structure-check` green.
  Files: `tests/functional/**`, `tests/integration/**`,
  `tests/unit/**`.
  Commit: `Relocate network and engine tests to correct layers`

- [x] **P1.7 — Shared fixtures, hypothesis profile, tolerance convention (§4)**
  Add `hypothesis` (dev dep) and a deterministic profile
  (`derandomize`, fixed seed, no committed `.hypothesis` DB). Add a root
  `tests/conftest.py` with seeded-RNG and one documented
  `rtol`/`atol` pair (intra-engine) and one cross-engine pair.
  Files: `pyproject.toml`, `pixi.toml`, `tests/conftest.py`, testing
  guide.
  Commit: `Add hypothesis deterministic profile and shared test fixtures`

- [x] **P1.8 — Input-domain property tests on validators (§4)**
  Property-based + explicit boundary-table tests against
  `core/validation.py` (`TypeValidator`, content `ValidatorBase`
  subclasses) through parameter (`core/variable.py`) and category
  (`core/category.py`): valid-domain acceptance and invalid/ wrong-type
  rejection or fallback per contract.
  Files: `tests/unit/easydiffraction/core/**` (validator/variable/
  category tests).
  Commit: `Add property-based input-domain tests for validators`

- [x] **P1.9 — Raise coverage gate to 80% (§4)**
  Set `[tool.coverage.report] fail_under = 80`. (Resolve Open question 2
  in Phase 2 if unit coverage is below 80 after P1.8.)
  Files: `pyproject.toml`.
  Commit: `Raise coverage fail_under to 80 percent`

- [ ] **P1.10 — Fast docs build gate (§9)**
  Add `docs-build-strict` (`mkdocs build --strict`, tutorials not
  executed), `link-check` (`lychee`), and `spell-check` (`codespell`)
  pixi tasks with config and ignore lists; add a fast every-push job to
  `test.yml`. Add `codespell` dev dep; wire `lychee` (Open question 4).
  Files: `pixi.toml`, `pyproject.toml`, `.github/workflows/test.yml`,
  `.codespellrc`, `lychee` config.
  Commit: `Add strict docs build, link, and spell checks on every push`

- [ ] **P1.11 — Apply/extend calculator support metadata (§6 prerequisite)**
  Build on the existing `Compatibility`/`CalculatorSupport` model in
  `core/metadata.py` (already declared per instrument category): add
  `radiation_probe` to `Compatibility` if missing, and add a small query
  helper to enumerate comparable engine × experiment-condition
  combinations for the verification pages. Prefer this declared metadata
  over the ad-hoc per-calculator `if beam_mode == …` checks. **Stop and
  ask** only if extending the metadata shape proves structural (Open
  question 1).
  Files: `src/easydiffraction/core/metadata.py`,
  `src/easydiffraction/datablocks/experiment/categories/instrument/**`,
  `src/easydiffraction/analysis/calculators/**`.
  Commit: `Extend calculator support metadata with radiation probe`

- [ ] **P1.12 — Cross-engine verification pages + script wiring (§6)**
  Add the `Verification` nav node (between Tutorials and Command-Line)
  and calculation-only `.py` comparison pages (cryspy ↔ crysfml) across
  the supported experiment combinations, with closeness metrics, overlay
  plots, and metric-tolerance assertions. **Wire the new
  `docs/docs/verification/` directory into the script-test runner** —
  `tools/test_scripts.py` discovers only `docs/docs/tutorials/*.py`
  today (lines 24-27) — and into the notebook pipeline (`notebook-prepare`
  / `notebook-convert` / `notebook-tests`, which target the tutorials
  dir), so the pages are generated and exercised as regressions. Run
  `pixi run notebook-prepare`.
  Files: `docs/mkdocs.yml`, `docs/docs/verification/*.py` (+ generated
  `*.ipynb`), `tools/test_scripts.py`, `pixi.toml`.
  Commit: `Add cross-engine verification comparison pages and script wiring`

- [ ] **P1.13 — Per-experiment performance benchmarks (§7)**
  Add `pytest-benchmark` (dev dep), `nightly`-marked benchmarks keyed by
  `beam_mode × radiation_probe × engine`, and a `benchmarks` pixi task
  emitting JSON as a CI artifact (data-repo history deferred).
  Files: `pyproject.toml`, `pixi.toml`, `tests/benchmarks/**`.
  Commit: `Add per-experiment performance benchmarks (nightly)`

- [ ] **P1.14 — Record cross-repository future work (§8 + deferred)**
  Add prioritised entries to `docs/dev/issues/open.md` for the nightly
  COD harness + results DB + pip-install acceptance job, generative
  fuzzing, data-repo benchmark history, and external-software
  comparison data. Confirm the ADR Deferred Work covers them.
  Files: `docs/dev/issues/open.md`.
  Commit: `Record cross-repo nightly harness and benchmarks as future work`

- [ ] **P1.15 — Promote ADR to accepted (§Change Discipline)**
  `git mv docs/dev/adrs/suggestions/test-suite-and-validation.md
  docs/dev/adrs/accepted/`; set its `## Status` to `Accepted.`; flip the
  `docs/dev/adrs/index.md` row to `Accepted` with the `accepted/...`
  link; fix any links that pointed at the `suggestions/` path
  (`git grep -n`).
  Files: ADR file (moved), `docs/dev/adrs/index.md`.
  Commit: `Promote test-suite-and-validation ADR to accepted`

- [ ] **P1.16 — Phase 1 review gate (no code)**
  Confirm every box above is `[x]`. Mark this step and commit the
  checklist update alone.
  Commit: `Reach Phase 1 review gate`

## Phase 2 verification

Run after the Phase 1 review gate closes. Use the zsh-safe log-capture
pattern where output is needed.

```shell
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

Phase 2 also: confirm `pixi run test-structure-check` passes after the
relocation; confirm the new `docs-build-strict`/`link-check`/
`spell-check` tasks pass; resolve Open question 2 if `fail_under = 80`
fails. `pixi run fix` regenerates
`docs/dev/package-structure/{full,short}.md` — accept those. Leave
generated `docs/dev/benchmarking/*.csv` and tutorial project outputs
untracked unless explicitly asked.

## Status checklist

- [ ] Phase 1 complete (P1.1–P1.16) and reviewed via `/review-impl-1`.
- [ ] Phase 2 verification complete and reviewed via `/review-impl-2`.
- [ ] ADR promoted to `accepted/`.
- [ ] Cross-repository follow-ups recorded in `docs/dev/issues/open.md`.

## Suggested Pull Request

**Title:** Stronger, clearer test suite with cross-engine verification

**Description:** This change makes EasyDiffraction's tests easier to
trust and easier to contribute to. It defines exactly which kind of test
belongs where (fast unit checks vs. slower engine tests), so the suite
stays quick day to day and runs the heavy checks on pull requests and
overnight. It fixes the long-standing red "patch" mark on pull requests
by correcting how coverage is reported, and raises the coverage target
while adding smarter tests that probe edge cases (negative, zero, and
out-of-range inputs), not just lines of code. It adds a new
**Verification** section to the documentation that calculates the same
diffraction pattern with each supported engine and shows, with clear
metrics and overlaid plots, how closely they agree. It also adds an
every-push documentation check (strict build, working links, spelling)
and a performance-benchmark suite. Larger overnight checks against many
real-world crystal files, and comparisons with external software such as
FullProf, are documented as planned follow-up work.
