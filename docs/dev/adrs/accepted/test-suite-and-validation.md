# ADR: Test Suite and Validation Strategy

## Status

Accepted.

## Date

2026-06-05

## Group

Quality.

## Context

EasyDiffraction now has five test layers — unit, functional,
integration, script, and notebook — plus a tutorial-output regression
check. The layers were established by
[Test Strategy](../accepted/test-strategy.md), which defines each in a
single line and states that the unit tree mirrors the source tree "where
practical."

That high-level statement is no longer enough. Concrete problems have
accumulated:

- **Placement is under-specified and already violated.** The only
  discriminator between functional and integration is "without heavy
  external dependencies" vs "real calculation engines and data," yet
  functional tests perform real network `download_data()`. Some unit
  tests are slow (parametrised sampler/plotting/display cases) and some
  call `download_data()` (mocked, but undocumented). There is no written
  rule an author can apply to a borderline test.
- **Codecov patch status is always red.** `.codecov.yml` runs a blocking
  `patch: target: auto` against a **unit-only** coverage upload
  (`coverage.yml` uploads only `coverage-unit.xml`). Any pull request
  that touches code exercised mainly by functional, integration, or
  script tests scores near-zero patch coverage and fails the blocking
  patch check. `coverage.yml` already runs on pull requests (not only on
  push to `develop`), so the baseline is current — the failure is purely
  a blocking patch status graded against unit-only data, not a stale
  baseline. See
  [discussion #69](https://github.com/orgs/easyscience/discussions/69).
- **Coverage is line-only and unenforced.** `fail_under = 65` is checked
  locally but never gated in CI, and line coverage says nothing about
  input-domain coverage (negative/zero/non-numeric inputs to numeric
  code, out-of-range crystallographic values, etc.).
- **The mirrored structure is enforced by a script that CI never runs.**
  `tools/test_structure_check.py` validates the `src` ↔ `tests/unit`
  mirror (209/209 modules today) but is not wired into any workflow, so
  drift can land.
- **No cross-engine numerical validation and no place to show it.** The
  documentation has no section comparing calculated patterns or refined
  parameters across calculation engines (`cryspy`, `crysfml`, `pdffit`)
  or against external software (FullProf, GSAS-II). Engines are keyed
  only by `scattering_type`, so there is no declared matrix of which
  `beam_mode × radiation_probe` each engine supports.
- **No performance-regression control.** `tools/benchmark_tutorials.py`
  records local-only, whole-tutorial wall-clock CSVs with no baseline,
  no per-experiment granularity, and no gate.
- **No broad robustness check against real-world files.** Nothing
  exercises EasyDiffraction against a large, varied corpus of CIF files
  to catch parsing/recognition failures before users hit them.
- **Documentation drift is not caught on every push.** `docs.yml`
  executes all tutorials and then builds and deploys the site; it is
  slow and therefore runs on pull requests only. There is no fast,
  every-push check that the site builds strictly, links resolve, and
  prose is clean. This overlaps the unimplemented
  [Documentation CI and Build Verification](documentation-ci-build.md)
  suggestion.

This ADR amends [Test Strategy](../accepted/test-strategy.md): the
five-layer decomposition stands, but its definitions become strict and
testable, and the strategy is extended to cover test cost tiers,
coverage policy, codecov configuration, cross-engine verification
documentation, performance benchmarks, a nightly validation harness, and
a fast documentation-build gate. It deliberately combines these into one
document because they are one coherent quality story with shared
infrastructure (markers, the data repository, CI triggers); large
sub-areas are explicitly phased and several are documented now but
implemented in follow-up pull requests.

## Decision

### 1. Strict layer definitions and placement criteria

Replace the one-line definitions with observable, testable rules. A test
belongs to the **lowest** layer whose constraints it can satisfy.

| Layer           | May use                                                                                         | Must NOT use                                                                                             | Speed       |
| --------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ----------- |
| **unit**        | one module under test; in-process logic; `tmp_path`                                             | real calculation engine; network / `download_data()`; filesystem outside `tmp_path`; `sleep`; subprocess | sub-second  |
| **functional**  | several modules / a workflow; small bundled fixtures                                            | real calculation engine; **network / `download_data()`**                                                 | seconds     |
| **integration** | real engines, real fits, real downloaded data; the only layer allowed network and real backends | —                                                                                                        | slow; xdist |
| **script**      | full tutorial `.py` executed subprocess-isolated                                                | (already correct)                                                                                        | slow; xdist |
| **notebook**    | generated `.ipynb` executed via `nbmake`                                                        | —                                                                                                        | slow        |

Mocking a forbidden dependency (for example a mocked `download_data()`)
keeps a test in a lower layer **only when the mock is explicit**; an
implicit or accidental real call is a layer violation.

Consequences for the current suite:

- The functional tests that call real `download_data()` move to
  integration (the hard line: functional is in-process with bundled
  fixtures, never network).
- A one-time relocation pass moves slow, engine-adjacent, or
  network-touching "unit" tests to their correct layer, and tags the
  remainder per §2.
- The ADR ships a short "where does this test go?" decision list so
  authors do not re-derive the boundary.

### 2. Test cost tiers via opt-in escalation markers

Cost tiers are **orthogonal** to layers. The default is fast; expensive
tests opt _into_ a heavier tier, so only the minority are tagged.

- **default (unmarked):** fast. Runs on every push, every pull request,
  and nightly.
- **`@pytest.mark.pr`:** heavier. Runs on pull requests and on
  `develop`/`master`, skipped on intermediate feature-branch pushes.
- **`@pytest.mark.nightly`:** very expensive (the §8 corpus harness,
  generative fuzzing, full cross-engine sweeps, full benchmarks). Runs
  on the scheduled nightly job and on demand; never on ordinary pushes.

Orthogonality holds at the **unit and functional** layers: those default
to fast, and an individual test opts into `pr`/`nightly`. The
**integration** layer is the one principled exception — _every_
integration test uses a real engine and/or downloaded data, so the layer
**defaults to the `pr` tier**, applied once in
`tests/integration/conftest.py` rather than by tagging each of ~150
tests. An integration test may still escalate to `nightly`. This keeps
feature-branch pushes fast (unit + functional only) without scattering
`@pytest.mark.pr` across the whole integration suite.

CI marker selection:

```text
feature-branch push:   -m "not pr and not nightly"
pull request + main:   -m "not nightly"
nightly schedule:      (all markers, including -m nightly)
```

The current `fast` marker (which today selects a _cheap subset_ and is
applied to six integration files) is **retired**; its intent is inverted
into the scheme above. Markers are registered in
`[tool.pytest.ini_options].markers`.

### 3. Mirrored unit structure as a CI gate

`tools/test_structure_check.py` remains the canonical enforcer of the
`src/easydiffraction/<pkg>/<mod>.py` →
`tests/unit/easydiffraction/<pkg>/test_<mod>.py` mirror, including its
three match strategies (direct mirror, known aliases such as
`singleton → singletons` and `variable → parameters`, and parent-level
roll-up for `default.py`/`factory.py` category packages). It is added to
CI (the lint/format or test workflow) as a fast, static gate so
structural drift fails before merge.

The check should be driven by a **single source-of-truth enumeration of
the `src/` tree**. `tools/generate_package_docs.py` already walks that
tree (`build_tree()`) to generate `docs/dev/package-structure/short.md`
and `full.md` (regenerated by `pixi run fix`). Today
`test_structure_check.py` walks `src/` independently, so the two can
drift. Reuse or adapt the existing tree-walk so structure generation and
the mirror check share one enumeration; the check fails CI and local
runs on any discrepancy between `src/` and `tests/unit/`. The related
scaffold generator `tools/gen_tests_scaffold.py` stays the way authors
create the mirrored test file for a new module.

### 4. Coverage policy: line/branch and input-domain

Two distinct bars, because line coverage and case coverage are different
guarantees.

- **Line/branch coverage.** Raise `fail_under` from 65 to **80 now**,
  with a documented ramp toward **90–95** as the suite fills, and gate
  it in CI through the codecov project status (§5) rather than only
  locally.
- **Validators are the input boundary.** All user input is verified at
  runtime through the project's custom validator framework in
  `src/easydiffraction/core/validation.py`: an `AttributeSpec` pairs a
  `TypeValidator` (data type) with a content `ValidatorBase` subclass
  (membership, range, and similar), and parameter (`core/variable.py`)
  and category (`core/category.py`) classes route writes through it.
  Input-domain tests therefore target the **validators directly** — both
  that they accept the full valid domain and that they reject (or fall
  back, per their contract) on invalid values — rather than re-checking
  the same boundaries at every call site. This matches the project
  principle of explicit handling at the boundary and no defensive
  padding past it.
- **Input-domain coverage.** Adopt **property-based testing with
  `hypothesis`** for the validator-guarded numeric and crystallographic
  inputs: cell lengths (> 0), cell angles (valid ranges and lattice
  constraints), fractional coordinates, site occupancies ∈ [0, 1],
  ADP/`Biso` positivity and ranges, space-group numbers (1–230),
  wavelengths (> 0), plus rejection of wrong-typed input
  (int/float/str). `hypothesis` runs in a **deterministic profile**
  (`derandomize`, fixed seed, no committed `.hypothesis` database) to
  honour the no-flakiness and no-ordering-dependence rules.
  Known-critical boundary cases are also written as **explicit
  parametrised tables** so they are visible and named; `hypothesis` adds
  generative exploration on top.
- **Numeric tolerance convention.** Replace the scattered mix of
  `pytest.approx`, `np.testing.assert_allclose`, and
  `assert_almost_equal(decimal=...)` with one documented intra-engine
  `rtol`/`atol` pair and one cross-engine pair, defined once (a root
  `tests/conftest.py` fixture) and referenced everywhere.

### 5. Codecov policy

The always-red patch status has a single cause: a **blocking `patch`
status (`target: auto`) graded against a unit-only coverage upload**.
Diff lines exercised mainly by functional, integration, or script tests
show near-zero unit coverage and fail the patch check. `coverage.yml`
already uploads unit coverage on pull requests and on push to `develop`,
so the baseline is current; only the status configuration needs to
change — **no new coverage-upload path is introduced**.

Adopt the recommendation from
[discussion #69](https://github.com/orgs/easyscience/discussions/69):

- **Upload unit-test coverage only** (keep the single, fast, reliable
  source already produced by `coverage.yml`; functional/integration
  coverage stays out of codecov).
- **`project` status: target 80%, blocking** (`informational: false`) —
  this becomes the real coverage gate.
- **`patch` status: `informational: true`** (non-blocking) — stops the
  always-red patch failures, which were an artefact of grading diff
  lines against a unit-only baseline.

### 6. Verification documentation (cross-engine pattern comparison)

Add a new top-level **Verification** section to the documentation nav
(between Tutorials and Command-Line), generated like tutorials (`.py`
source → notebook via `pixi run notebook-prepare`, built with
`execute: false`).

- **Calculation-only comparisons (no minimisation).** Feed identical
  input parameters to each supported engine, compute patterns, and
  compare them pairwise (`ed-cryspy`, `ed-crysfml`, … and later
  `fullprof`). This is far faster than fitting, so the same pages double
  as **fast regression scripts** under `script-tests`.
- **Metrics.** Report clear, documented closeness metrics per pair — a
  profile-difference metric (Rwp-style), maximum point-wise deviation,
  and an integrated-intensity ratio — with explicit tolerances.
- **Overlay plots.** Plot all engines on one chart with distinct colours
  and line styles (solid/dotted/…) for visual comparison.
- **Coverage of conditions.** Grow to cover **every valid experiment ×
  instrument-parameter combination at least once** (powder/single
  crystal × constant-wavelength/time-of-flight × neutron/x-ray ×
  bragg/total, per the support matrix below). The section ships with the
  framework and the first cross-engine comparison (constant-wavelength
  powder, cryspy ↔ crysfml); the remaining supported combinations
  (time-of-flight powder, single crystal) are added **incrementally**
  and tracked in the open-issues list.
- **External software, incrementally.** External tools (FullProf first,
  then GSAS-II/TOPAS) are compared by loading a **pre-calculated profile
  from a zipped project** stored in the `diffraction` data repository
  (§8), so EasyDiffraction need not run them. The page structure ships
  now with an external placeholder; data is added incrementally.
- **Prerequisite — engine support matrix.** Declare which engine
  supports which `beam_mode × radiation_probe` (and `scattering_type`)
  via the existing `CalculatorSupport`/`Compatibility` metadata, so
  "every valid combination" is well-defined. Today engines are keyed
  only by `scattering_type` at the factory level. The precise metadata
  wiring is a scoped sub-task (see Deferred Work).

### 7. Performance-regression benchmarks

Replace the ad-hoc `tools/benchmark_tutorials.py` CSV tool with
**`pytest-benchmark`**, matching the prior art in `deps-pycrysfml`:

- Benchmark **per experiment type** (one benchmark per
  `beam_mode × radiation_probe × engine`) rather than whole-tutorial
  wall-clock.
- Store baseline JSON (full machine info + per-benchmark statistics) in
  the `diffraction` data repository (§8), written by a CI job.
- **Informational now** (no gating), to avoid false failures from noisy
  CI timing. A regression gate (`--benchmark-compare-fail`) is added
  later once variance is characterised, ideally on a dedicated runner
  (see Deferred Work). Benchmarks run in the `nightly` tier.

### 8. Nightly validation harness (CIF corpus and generative fuzzing)

A robustness harness exercising EasyDiffraction against many real and
synthetic structures.

- **Code vs data split.** Harness _code_ lives in `diffraction-lib`
  (`tests/nightly/`, `@pytest.mark.nightly`) so it versions with the
  code it checks. The _corpus_, _results database_, FullProf profiles,
  and benchmark baselines live in the **`diffraction` data repository**
  (consistent with `download_data()`), fetched at runtime.
- **Acceptance-style run.** A scheduled nightly CI job installs
  EasyDiffraction **from PyPI**, runs the harness, and writes results
  back to the data repository via a bot commit (the `deps-pycrysfml`
  "auto-push" pattern). The same harness runs locally on demand.
- **CIF corpus check.** Download ~100–200 CIF files from the
  Crystallography Open Database (COD), load each, and record per-file
  status:
  - `ok` — parsed, all recognised;
  - `partial` — parsed, some information missing (EasyDiffraction
    applied defaults), with a comment naming what was not recognised;
  - `fail` — could not be parsed, with the error. The status lets the
    harness (a) skip re-downloading already-`ok` files on later nights
    and (b) flag genuine EasyDiffraction recognition bugs vs malformed
    files; problematic files convert to issues.
- **Results database — CSV.** A git-diffable manifest, **one row per CIF
  keyed by COD id and ordered by id** (so new files insert in order):
  `id, parse_status, missing_fields, calc_status_per_engine, comment, last_checked`.
  CSV keeps diffs reviewable and issue-friendly.
- **Re-check flag.** The harness script exposes a flag to **re-run only
  the failed/partial entries already in the database** (rather than
  drawing new random files from COD), so fixes in EasyDiffraction can be
  re-validated against the exact files that previously failed.
- **Cross-engine calculation on the corpus.** For loadable structures,
  call each supported calculator, compare patterns, and store the
  per-engine result (with comments) in the same database.
- **Generative fuzzing (documented now, implemented later).** Randomly
  generate ~100–200 structures (random space group, cell parameters,
  1–10 atoms with random coordinates/ADP/occupancy), compute patterns
  across engines, and record disagreements in the same database. This
  reuses the corpus harness and database; its implementation is a
  follow-up pull request (see Deferred Work).

### 9. Fast documentation-build gate in the test workflow

Add a **fast, every-push job to `test.yml`** that does **not execute
tutorials**:

- `mkdocs build --strict` (catches missing nav entries and broken
  internal references; tutorials build with `execute: false`),
- link checking (`lychee` or equivalent, with an allowlist), and
- spelling/grammar (`codespell` first; `Vale` later, see Deferred Work).

This is expected to take about a minute and runs on every push, giving
prompt drift feedback. It is deliberately **separate from `docs.yml`**,
which executes all tutorials and then builds and deploys — slow, and
therefore pull-request-only. The detailed catalogue of documentation
checks is owned by
[Documentation CI and Build Verification](documentation-ci-build.md),
which this ADR coordinates with: that ADR defines _what_ the checks are;
this ADR's decision is that the cheap, deterministic subset runs as part
of the every-push test workflow. Promoting that ADR is part of this
work.

Known limitation: links that appear **only inside executed notebook
output cells** (for example a generated table linking to parameter
definitions) are invisible to the non-executing strict-build job. That
output-cell-link feature does not exist yet; the limitation is recorded
for the future rather than solved now.

### Implementation phasing

1. **Quick wins:** §5 codecov policy, §3 structure-check gate, §9 fast
   docs gate, §2 markers + §1 placement rules and the relocation pass.
2. **Coverage and cases:** §4 `fail_under` 80 + `hypothesis` + tolerance
   convention.
3. **Verification + benchmarks:** §6 engine support matrix and
   calculation-only comparison pages; §7 `pytest-benchmark`.
4. **Nightly harness:** §8 corpus check and results database; generative
   fuzzing in a later pull request.

## Consequences

### Positive

- A test's correct layer and cost tier are decidable from written rules,
  not judgement, so the suite stops drifting.
- Codecov patch stops failing spuriously and the project status becomes
  a meaningful, enforced 80% gate.
- Coverage gains a case-quality dimension (input domains, boundaries,
  wrong types), not just line counts.
- Cross-engine and (later) external agreement is visible to scientists
  in the documentation and regression-checked cheaply.
- Performance and real-world-file robustness gain dedicated, low-noise
  signals without slowing ordinary development.
- Documentation drift is caught on every push in about a minute.

### Trade-offs

- Relocating functional/unit tests and retiring `fast` touches many
  existing test files in one pass.
- New dependencies (`hypothesis`, `pytest-benchmark`, plus `codespell`
  and a link checker for the docs job) add configuration and
  maintenance.
- The nightly harness and data-repository round-trip add CI and
  cross-repository coordination.
- Raising `fail_under` to 80 and gating it can block merges until
  coverage catches up; the ramp is deliberate.

## Alternatives Considered

- **One combined ADR vs several focused ADRs.** A split (taxonomy /
  codecov / benchmarks / verification) was considered. Chosen: one
  combined ADR, because the goals share infrastructure (markers, the
  data repository, CI triggers) and read as one quality story; large
  sub-areas are phased instead.
- **Upload combined coverage to codecov.** Rejected for now: slower,
  flakier (engine-dependent), and needs per-flag setup. Unit-only upload
  with a non-blocking patch status is simpler and fixes the reported
  pain directly.
- **Keep the current `fast` marker semantics.** Rejected: marking the
  cheap majority is more error-prone than opt-in escalation of the
  expensive minority.
- **`asv` for benchmarking.** Rejected vs `pytest-benchmark`: `asv`
  wants a dedicated dashboard/runner; `pytest-benchmark` reuses pytest,
  matches `deps-pycrysfml`, and supports committed JSON baselines.
- **SQLite results database.** Rejected as the source of truth: opaque
  in diffs and harder to convert to issues. CSV keyed and ordered by id
  is reviewable; a derived cache can be added later if querying demands
  it.
- **`syrupy` snapshot testing and `mutmut` mutation testing.** Deferred,
  not adopted now (see Deferred Work): the tutorial `baseline.json`
  already covers fit-result regression, and mutation testing is only
  meaningful once line coverage is solid.

## Deferred Work

- Generative random-structure fuzzing implementation (§8) — follow-up
  pull request.
- External-software reference data and comparisons (FullProf, then
  GSAS-II/TOPAS) for the Verification section (§6).
- Benchmark regression gating threshold and a dedicated, low-noise
  runner (§7).
- Precise `CalculatorSupport`/`Compatibility` wiring for the engine
  support matrix (§6 prerequisite); may warrant its own short ADR.
- `Vale` prose linting after `codespell` has a baseline and a
  crystallography/CIF-tag vocabulary (§9).
- Link-checking of URLs that appear only in executed notebook output
  cells (§9 limitation); revisit if/when that output feature exists.
- Mutation testing (`mutmut`) once line coverage reaches ≥ 80%.
- Snapshot testing (`syrupy`) for CIF/report output — reconsider if
  explicit assertions prove insufficient.
- The exact coverage ramp schedule from 80% toward 90–95%.

## Dependencies

New dependencies introduced by this ADR (approval recorded in the
drafting conversation, per the dependency-approval rule):

- `hypothesis` — property-based / input-domain testing (§4).
- `pytest-benchmark` — performance-regression benchmarks (§7).

Coordinated with
[Documentation CI and Build Verification](documentation-ci-build.md),
which carries the documentation-check tools (`codespell`, a link checker
such as `lychee`, and later `Vale`) used by §9.

## Related ADRs

- [Test Strategy](../accepted/test-strategy.md) — amended by this ADR.
- [Documentation CI and Build Verification](documentation-ci-build.md) —
  coordinated with §9.
- [Lint Complexity Thresholds](../accepted/lint-complexity-thresholds.md)
  — sibling Quality guardrail.
- [Notebook Generation Source of Truth](../accepted/notebook-generation.md)
  — the `.py` → notebook pipeline reused by §6.
- [Factory Contracts and Metadata](../accepted/factory-contracts.md) —
  the `CalculatorSupport`/`Compatibility` metadata used by §6.
- [Enum-Backed Closed Value Sets](../accepted/enum-backed-closed-values.md)
  — any new closed set (engine tags, experiment axes) stays
  `(str, Enum)`.
