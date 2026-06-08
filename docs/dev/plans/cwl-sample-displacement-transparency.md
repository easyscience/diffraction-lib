# Plan — CWL sample-displacement & transparency peak-position corrections

Governing conventions: [`AGENTS.md`](../../../AGENTS.md).

**Deliberate exceptions to AGENTS.md in this plan**

- **History.** This plan was drafted and reviewed in `tmp/plans/`
  (git-ignored) to avoid interfering with in-flight work on the
  `more-validation-notebooks` branch, then moved here to
  `docs/dev/plans/` and committed at the start of the `/draft-impl-1`
  cycle. Implementation runs on a dedicated
  `cwl-sample-displacement-transparency` branch off `develop` (not on
  `more-validation-notebooks`).
- **Dependency timing.** The feature depends on unreleased cryspy
  functionality (PR #46). Phase 2 verification of the cryspy path can
  only pass against a locally patched cryspy until that PR ships in a
  released version. See *Decisions → cryspy dependency* and the
  *Testing against unreleased cryspy* section.

---

## Goal

Add two FullProf-style systematic peak-position corrections to the
constant-wavelength powder instrument so the
`pd-neut-cwl_tch-fcj_lab6` verification page can be completed:

| User-facing API                                   | FullProf | cryspy CIF / dict key            | Physical effect              | 2θ shift term      |
| ------------------------------------------------- | -------- | -------------------------------- | ---------------------------- | ------------------ |
| `experiment.instrument.calib_sample_displacement` | `SyCos`  | `_setup_offset_SyCos` / `offset_sycos` | Specimen displacement | ∝ cos(θ) = cos(½·2θ) |
| `experiment.instrument.calib_sample_transparency` | `SySin`  | `_setup_offset_SySin` / `offset_sysin` | Sample transparency/absorption | ∝ sin(2θ)     |

These join the existing `calib_twotheta_offset` (FullProf `Zero`,
cryspy `offset_ttheta`) as the third and fourth `calib_*` corrections on
`CwlPdInstrument`.

cryspy applies all three together
(`cryspy/procedure_rhochi/rhochi_pd.py`, PR #46):

```python
ttheta_zs = ttheta - (
    offset_ttheta
    + numpy.radians(offset_sycos) * numpy.cos(0.5 * ttheta)
    + numpy.radians(offset_sysin) * numpy.sin(ttheta)
)
```

So the EasyDiffraction parameter values are plain **degrees**, exactly
like `calib_twotheta_offset`. As the notebook already warns for `Zero`,
the FullProf-vs-cryspy sign/convention may differ, so the `.pcr` values
(`SyCos = 0.05395`, `SySin = 0.09127`) may need adjustment when wired in
— resolve this empirically in Phase 1 step P1.5.

## Naming decision (confirmed with user)

`calib_sample_displacement` / `calib_sample_transparency` — cause-based,
self-explanatory to non-programmer scientists, and consistent with the
`calib_*` peak-position-correction family already on the instrument
category. Chosen over `calib_sycos`/`calib_sysin` (cryptic) and over
`calib_twotheta_displacement`/`calib_twotheta_transparency` (more
verbose, no added clarity).

## ADR

No new ADR is required. This adds two parameters to the existing
`instrument` category following the established `Parameter` +
getter/setter + `CifHandler` pattern used by `calib_twotheta_offset`
(`src/.../instrument/cwl.py`). It introduces no new category, factory,
switchable-category wiring, or datablock. It does extend CIF
serialisation toward the cryspy backend, but only by adding rows to the
existing CWL-powder instrument mapping, which the
[`factory-contracts.md`](../adrs/accepted/factory-contracts.md)
and existing instrument design already cover. Per AGENTS.md
§Change Discipline, the relevant accepted ADRs were reviewed; none
constrains this change beyond the existing pattern.

## Decisions

- **Scope: CWL powder only.** The corrections are defined only for
  constant-wavelength powder diffraction (cryspy restricts them to that
  geometry). Add the two parameters to `CwlPdInstrument` (the
  `cwl-pd` instrument), **not** to `CwlInstrumentBase` (which is shared
  with the single-crystal `cwl-sc` instrument) and **not** to TOF.
- **CIF handler names.** Follow the existing `_instr.*` local
  convention: `_instr.sample_displacement` and
  `_instr.sample_transparency` (mirroring `_instr.2theta_offset`).
- **cryspy CIF emission.** Extend the CWL-powder branch of
  `_cif_instrument_section` in
  `src/easydiffraction/analysis/calculators/cryspy.py` with two rows:
  `calib_sample_displacement → _setup_offset_SyCos` and
  `calib_sample_transparency → _setup_offset_SySin`.
- **cryspy dict update (fast minimizer path).** Extend
  `_update_experiment_in_cryspy_dict` (CWL-powder branch) to set
  `cryspy_expt_dict['offset_sycos'][0]` and
  `cryspy_expt_dict['offset_sysin'][0]` from the two new parameters,
  mirroring how `offset_ttheta` is set. **Confirm the dict shape during
  P1.3** (scalar vs `[0]`-indexed array) by inspecting the dict cryspy
  builds from the emitted CIF on the PR branch; `offset_ttheta` uses
  `[0]`-indexed access, so the new keys are expected to as well — verify
  before committing.
- **crysfml: no support.** crysfml has no SyCos/SySin equivalent. Do
  **not** add rows to `_INSTRUMENT_ATTRIBUTE_MAP` in
  `crysfml.py`; `_copy_present_values` silently skips unmapped
  attributes, so crysfml keeps ignoring the corrections. The notebook
  already documents that crysfml will retain a systematic offset; this
  is expected and acceptable. (Optionally add a one-line code comment
  noting SyCos/SySin are intentionally unmapped for crysfml.)
- **cryspy dependency.** Do **not** bump the `cryspy` pin in
  `pyproject.toml` in this plan: PR #46 is unreleased. The library code
  is written so that, with current released cryspy (0.11.0), the new
  CIF rows are simply ignored / the dict keys fall back to `0.0`
  (`dict_pd.get("offset_sycos", 0.0)`), so nothing breaks. The cryspy
  path of the notebook only matches FullProf once cryspy ships PR #46.
  When that release exists, a **follow-up change** bumps the pin and
  un-skips the page. This plan does not add a dependency under
  AGENTS.md §Architecture (no pin change), so no dependency approval is
  needed here.
- **Verification page un-skip is deferred.** Keep
  `pd-neut-cwl_tch-fcj_lab6` in `docs/docs/verification/ci_skip.txt`
  until a released cryspy supports the corrections. The notebook's two
  commented `calib_*` lines get uncommented (P1.5) so the page is
  ready, but it stays CI-skipped because the released engine still
  differs. Note: the page is also skipped for `11B` scattering and
  TCH/FCJ reasons per the current `ci_skip.txt` comment, which are
  independent of this change.

## Open questions

1. **Sign/convention of the FullProf values.** Does
   `calib_sample_displacement = 0.05395` / `calib_sample_transparency =
   0.09127` reproduce FullProf directly, or is a sign flip / scale
   needed (as happened conceptually with `Zero`)? Resolve empirically in
   P1.5 against a PR-#46 cryspy; record the final notebook values and
   any adjustment in a code/notebook comment.
2. **cryspy dict key array shape.** Confirm `offset_sycos`/`offset_sysin`
   are `[0]`-indexed arrays in the built dict (expected, matching
   `offset_ttheta`). Resolved during P1.3.
3. **Released cryspy version string.** The exact released version that
   first contains PR #46 is unknown today; the pin bump + un-skip is a
   deferred follow-up, not part of this plan.

## Testing against unreleased cryspy (local only — not committed)

To exercise the cryspy path before PR #46 is released, replace the
cryspy installed in the pixi default env with the PR branch. This is a
**local developer step**; it touches `.pixi/` only and must never be
committed.

```bash
# From a scratch dir outside the repo:
git clone --branch <pr-46-branch> https://github.com/ikibalin/cryspy.git /tmp/cryspy-pr46
# Install into the project's default pixi env (editable, so edits are live):
cd /home/andrewsazonov/Development/github.com/easyscience/diffraction-lib
.pixi/envs/default/bin/python -m pip install --no-deps -e /tmp/cryspy-pr46
# Verify it took:
.pixi/envs/default/bin/python -c "import cryspy, inspect, os; print(os.path.dirname(cryspy.__file__))"
```

To restore the released cryspy afterwards (so the env matches
`pixi.lock` again):

```bash
pixi install            # or: .pixi/envs/default/bin/python -m pip install --no-deps --force-reinstall cryspy==0.11.0
```

Notes:
- `<pr-46-branch>` is the head branch of
  https://github.com/ikibalin/cryspy/pull/46 — confirm the exact branch
  name on the PR page before cloning.
- Because `pixi install` will overwrite the patched env, any
  `pixi run check` / test invocation that re-syncs the env can silently
  revert the patch. Run cryspy-path verification with explicit
  `.pixi/envs/default/bin/python` invocations, or re-apply the patch
  after any `pixi install`.
- Unit tests (P2) must **not** depend on the patched cryspy — they stub
  the engine and assert on the emitted CIF string / dict mutations, per
  AGENTS.md §Testing ("no real calculation engines" in unit tests).

## Concrete files likely to change

Source (Phase 1):

- `src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`
  — add two `Parameter`s + getter/setter properties to `CwlPdInstrument`.
- `src/easydiffraction/analysis/calculators/cryspy.py`
  — `_cif_instrument_section` (CWL-powder mapping) and
  `_update_experiment_in_cryspy_dict` (CWL-powder branch).
- `src/easydiffraction/analysis/calculators/crysfml.py`
  — comment only (intentionally unmapped); no functional change.
- `docs/docs/verification/pd-neut-cwl_tch-fcj_lab6.py`
  — uncomment the two `calib_*` lines using the new names; regenerate
  the notebook with `pixi run notebook-prepare`.

Tests (Phase 2):

- `tests/unit/easydiffraction/datablocks/experiment/categories/instrument/test_cwl.py`
  — assert the two new parameters are settable and carry correct
  defaults/units/CIF names.
- A cryspy-calculator unit test (new
  `test_cryspy_coverage.py` or extend an existing calculator test)
  asserting the emitted CIF contains `_setup_offset_SyCos` /
  `_setup_offset_SySin` with the set values, and that
  `_update_experiment_in_cryspy_dict` writes `offset_sycos`/
  `offset_sysin` into a stub dict. No real engine.

Docs / structure (auto-generated, do not hand-edit):

- `docs/dev/package-structure/full.md`, `short.md` — regenerated by
  `pixi run fix` if the public surface changes.

## Implementation steps (Phase 1)

> When executed via `/draft-impl-1`, each step is one atomic commit:
> stage only the files the step lists (explicit paths), update this
> checklist to `[x]` in the same commit, and use the step's `Commit:`
> message. Commit locally before moving to the next step. Do not run
> tests or `pixi run check` in Phase 1.

- [x] **P1.1 — Add the two parameters to `CwlPdInstrument`.**
  In `cwl.py`, inside `CwlPdInstrument.__init__`, add
  `self._calib_sample_displacement` and
  `self._calib_sample_transparency` `Parameter`s modeled on
  `_calib_twotheta_offset`: `name='sample_displacement'` /
  `'sample_transparency'`, descriptive `description`, `units='degrees'`,
  `DisplayHandler` (display names "Sample displacement" / "Sample
  transparency", `display_units='deg'`, sensible LaTeX), default `0.0`,
  `RangeValidator()`, and `CifHandler(names=['_instr.sample_displacement'])`
  / `['_instr.sample_transparency']`. Add the matching getter +
  setter properties (numpy-style one-line ≤72-char docstrings).
  Files: `src/.../instrument/cwl.py`.
  Commit: `Add CWL sample displacement and transparency parameters`

- [x] **P1.2 — Emit the corrections in the cryspy CIF.**
  In `cryspy.py` `_cif_instrument_section`, CWL+powder branch, extend
  `instrument_mapping` with
  `'calib_sample_displacement': '_setup_offset_SyCos'` and
  `'calib_sample_transparency': '_setup_offset_SySin'`.
  Files: `src/easydiffraction/analysis/calculators/cryspy.py`.
  Commit: `Emit SyCos/SySin offsets in cryspy CWL instrument CIF`

- [x] **P1.3 — Update the cached cryspy dict (fast path).**
  In `cryspy.py` `_update_experiment_in_cryspy_dict`, CWL+powder
  branch, set `cryspy_expt_dict['offset_sycos'][0]` and
  `cryspy_expt_dict['offset_sysin'][0]` from the two new parameters,
  next to the existing `offset_ttheta` assignment. First confirm the
  built dict exposes these keys with `[0]`-indexed shape (see Open
  question 2); guard with `if 'offset_sycos' in cryspy_expt_dict:` only
  if released cryspy lacks the keys and would otherwise KeyError on the
  minimizer fast path — prefer the unconditional form if released
  cryspy already provides zero-initialized keys.
  Files: `src/easydiffraction/analysis/calculators/cryspy.py`.
  Commit: `Update cryspy dict with SyCos/SySin offsets`

- [x] **P1.4 — Document crysfml non-support.**
  In `crysfml.py` `_update_experiment_dict_from_instrument`, add a
  one-line comment near the instrument map noting SyCos/SySin
  (`calib_sample_displacement` / `calib_sample_transparency`) are
  intentionally unmapped because crysfml has no equivalent correction.
  No functional change.
  Files: `src/easydiffraction/analysis/calculators/crysfml.py`.
  Commit: `Note crysfml lacks SyCos/SySin instrument corrections`

- [x] **P1.5 — Wire the corrections into the verification page.**
  In `pd-neut-cwl_tch-fcj_lab6.py`, uncomment the two correction lines
  using the new names and the empirically confirmed values
  (start from `calib_sample_displacement = 0.05395`,
  `calib_sample_transparency = 0.09127`; adjust per Open question 1 if
  the cryspy convention differs). Update the surrounding markdown so it
  no longer says "pending EasyDiffraction support". Keep the page in
  `ci_skip.txt` (still skipped until released cryspy supports PR #46);
  update only the cryspy-path narrative if needed. Regenerate the
  notebook with `pixi run notebook-prepare`.
  Files: `docs/docs/verification/pd-neut-cwl_tch-fcj_lab6.py`,
  `docs/docs/verification/pd-neut-cwl_tch-fcj_lab6.ipynb`.
  Commit: `Enable SyCos/SySin corrections in LaB6 verification page`

- [ ] **P1.6 — Phase 1 review gate** (no-code). Mark `[x]`, commit the
  checklist update alone.
  Commit: `Reach Phase 1 review gate`

## Implementation steps (Phase 2)

> Run after Phase 1 review is approved. When executed via
> `/draft-impl-2`, **add/extend the tests first (P2.1)**, then run the
> verification suite (P2.2–P2.6) in order, committing atomically per
> auto-fix or per logical fix. Use the zsh-safe log-capture pattern
> below whenever a task's output must be analyzed. Do not silence lint
> thresholds (`# noqa`, threshold bumps) — refactor instead per
> AGENTS.md §Code Style.

- [ ] **P2.1 — Add/extend unit tests (engine-free).**
  - Extend
    `tests/unit/.../instrument/test_cwl.py` to assert
    `calib_sample_displacement` / `calib_sample_transparency` are
    settable, default to `0.0`, carry `units='degrees'`, and expose CIF
    names `_instr.sample_displacement` / `_instr.sample_transparency`.
  - Add a cryspy-calculator unit test (new
    `tests/unit/.../analysis/calculators/test_cryspy_coverage.py` or
    extend an existing calculator test) asserting that
    `_cif_instrument_section` emits `_setup_offset_SyCos` /
    `_setup_offset_SySin` with the set values, and that
    `_update_experiment_in_cryspy_dict` writes `offset_sycos` /
    `offset_sysin` into a stub experiment dict. **No real cryspy
    engine** (AGENTS.md §Testing); the unreleased PR-#46 cryspy is
    exercised manually per *Testing against unreleased cryspy*,
    outside `pixi run unit-tests`.
  - Confirm test/source mirroring with `pixi run test-structure-check`
    (also run inside `pixi run check`).
  - Commit: `Add tests for CWL SyCos/SySin instrument corrections`

- [ ] **P2.2 — `pixi run fix`.** Apply auto-fixes; include any
  regenerated `docs/dev/package-structure/full.md` / `short.md`.
  Commit: `Apply pixi run fix auto-fixes` (skip if nothing changed).

- [ ] **P2.3 — `pixi run check`** until clean. Fix mechanical lint
  nits directly; refactor (don't silence) any complexity/type breach.
  ```bash
  pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
  ```

- [ ] **P2.4 — `pixi run unit-tests`** until green.
  ```bash
  pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
  ```

- [ ] **P2.5 — `pixi run integration-tests`** until green. For
  sandbox-only multiprocessing/process-pool failures, rerun with the
  approved escalated permission path before treating it as a defect.
  ```bash
  pixi run integration-tests
  ```

- [ ] **P2.6 — `pixi run script-tests`** until green.
  `pd-neut-cwl_tch-fcj_lab6` remains skipped via `ci_skip.txt`, so the
  still-divergent cryspy path will not fail CI; confirm the page still
  parses/builds where the runner loads it. Leave generated
  `docs/dev/benchmarking/*.csv` untracked.
  ```bash
  pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
  ```

## Follow-up (out of scope, deferred)

- When a released cryspy includes PR #46: bump the `cryspy` pin in
  `pyproject.toml` / refresh `pixi.lock`, remove
  `pd-neut-cwl_tch-fcj_lab6` from `ci_skip.txt` (if the remaining
  `11B` / TCH-FCJ discrepancies are also resolved), and finalize the
  notebook reference values. Track in `docs/dev/issues/open.md`.

## Status checklist

- [x] P1.1 Add parameters to `CwlPdInstrument`
- [x] P1.2 Emit offsets in cryspy CIF
- [x] P1.3 Update cryspy cached dict
- [x] P1.4 Comment crysfml non-support
- [x] P1.5 Wire corrections into verification page
- [ ] P1.6 Phase 1 review gate
- [ ] P2.1 Add/extend engine-free unit tests
- [ ] P2.2 `pixi run fix`
- [ ] P2.3 `pixi run check` clean
- [ ] P2.4 `pixi run unit-tests` green
- [ ] P2.5 `pixi run integration-tests` green
- [ ] P2.6 `pixi run script-tests` green

## Suggested branch

`cwl-sample-displacement-transparency` (off `develop`, per AGENTS.md
§Planning). Note: current work is on `more-validation-notebooks`; create
the implementation branch when starting `/draft-impl-1`.

## Suggested Pull Request

**Title:** Add sample-displacement and transparency peak corrections for
constant-wavelength powder data

**Description:** Constant-wavelength powder instruments can now correct
for two common sources of systematic peak-position error: **sample
displacement** (the specimen sitting slightly off the diffractometer
axis) and **sample transparency** (the beam penetrating into the
sample). These match FullProf's `SyCos` and `SySin` corrections and sit
alongside the existing zero-offset correction:

```python
experiment.instrument.calib_sample_displacement = 0.05395
experiment.instrument.calib_sample_transparency = 0.09127
```

This lets EasyDiffraction reproduce FullProf peak positions for datasets
where these effects matter (e.g. the LaB₆ verification reference) when
using the cryspy engine. The crysfml engine does not yet support these
corrections. Until the upstream cryspy release that adds them is
available, the LaB₆ verification page remains marked as a known
work-in-progress and is excluded from CI.
