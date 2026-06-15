# Implementation Plan: Bayesian Resume (DREAM) and MCMC Sidecar Naming

This plan follows the conventions in [`AGENTS.md`](../../../AGENTS.md).
No deliberate exceptions are taken.

## ADR

Implements
[`bayesian-resume-and-mcmc-sidecar.md`](../adrs/accepted/bayesian-resume-and-mcmc-sidecar.md)
(Status: Accepted; promoted from `suggestions/` in Phase A). This plan
**owns** that ADR.

Accepted ADRs this work **substantively amends** — the filename and the
single-sidecar/per-engine-groups wording:

- [`analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
- [`minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)

The `results.h5` → `mcmc.h5` rename additionally updates **plain
references** in other accepted ADRs, the ADR index, the
`fit-output-files-and-data-exports` suggestion, user/CLI docs, and tests
— the full set is enumerated in ADR §4 and under *Concrete files* / P1.1.

Accepted ADRs this work must **respect**:

- [`minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)
  — `analysis.minimizer` (input) / `analysis.fit_result` (output) pairing.
- [`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md)
  — the `minimizer.type` selector surface.
- [`undo-fit.md`](../adrs/accepted/undo-fit.md) — undo clears the sidecar.

## Branch and PR

Flat-slug branch `bayesian-resume-and-mcmc-sidecar` off `develop`
(created by `/draft-impl-1` setup). PR targets `develop`.

## Reference implementation

`easyscience/core` PR #257 ("Bayesian extend/resume", branch
`bayesian_extend`) is the blueprint for the DREAM sampler mechanics:
`src/easyscience/fitting/minimizers/minimizer_bumps.py` —
`mcmc_sample(resume_state=…)`, `_resolve_population_alias`,
`save_sampler_state`/`load_sampler_state`, and the ring-buffer docstring.

## Decisions (already made)

- One sidecar per fit, **renamed `results.h5` → `mcmc.h5`**; filename in
  one constant + a shared path helper (no duplicated literals).
- Per-engine **HDF5 groups** hold resumable raw state: emcee's existing
  `emcee_chain`, plus a new DREAM state group (`DreamFit.h5dump` +
  stored fitted-parameter names).
- Unified API unchanged: `analysis.fit(resume=True, extra_steps=N)`.
  DREAM translates `extra_steps=N` to `samples = current + N, burn = 0`
  (ring-buffer extend); population scale recovered from `state.Npop`;
  state deep-copied before fitting.
- DREAM resume validates parameter count, population, and **names**
  (we persist names, so no positional-only fallback).
- Beta project: no legacy shim; regenerate fixtures/tutorials/tests that
  reference `results.h5`.

## Resolved decisions (no open questions blocking `/draft-impl-1`)

1. **DREAM state layout is fixed in the ADR** — a top-level `dream_state`
   HDF5 group holding the `MCMCDraw` (`DreamFit.h5dump`) plus a
   `param_names` dataset. Not deferred; P1.2/P1.3 implement exactly this.
2. **The `chains` alias is included** as an approved user-facing API
   addition (ADR §1). P1.5 stays in scope; it is not optional.
3. **Unified `extra_steps` semantics** — emcee appends, DREAM extends its
   ring buffer (`samples = current + N`, `burn = 0`); both yield the same
   "added N draws". The Phase 2 cross-engine parity test enforces this.

## Concrete files likely to change

- `src/easydiffraction/io/results_sidecar.py` (filename constant, path
  helper; DREAM state group read/write).
- `src/easydiffraction/analysis/minimizers/bumps_dream.py` (capture
  state, `_sidecar_path`, `fit()` override, resume load/validate/extend,
  `chains` alias).
- `src/easydiffraction/analysis/minimizers/emcee.py` (only if shared
  resume/detection helpers are factored out; otherwise untouched).
- `src/easydiffraction/analysis/minimizers/base.py` (any shared resume
  validation/detection helper).
- `src/easydiffraction/analysis/fitting.py`,
  `src/easydiffraction/analysis/analysis.py` (filename literal → helper;
  DREAM resume-detection alongside `_has_resumable_emcee_sidecar`).
- `src/easydiffraction/__main__.py` (CLI messages naming the sidecar).
- **Rename sweep — every tracked `results.h5` reference** (from
  `git grep -n 'results\.h5'`), excluding generated/transient outputs:
  - Accepted ADRs: `analysis-cif-fit-state.md`,
    `minimizer-category-consolidation.md`, `undo-fit.md`,
    `minimizer-input-output-split.md`, `runtime-fit-results.md`,
    `edstar-project-persistence.md`, and `docs/dev/adrs/index.md` rows.
  - Suggestion ADR: `fit-output-files-and-data-exports.md`.
  - User docs: `docs/docs/cli/index.md`,
    `docs/docs/user-guide/{concept,data-format}.md`,
    `docs/docs/user-guide/analysis-workflow/{analysis,project}.md`.
  - Tests: `tests/unit/easydiffraction/io/test_results_sidecar*.py`,
    `analysis/test_analysis_coverage.py`,
    `analysis/test_fitting_coverage.py`,
    `analysis/minimizers/test_emcee.py`,
    `test___main__*.py`, `tests/integration/fitting/test_emcee.py`,
    `test_bayesian_dream.py`, and any tracked project fixtures.
- DREAM resume tutorial + its registration artifacts:
  `docs/docs/tutorials/bayesian-dream-resume-*.py` (+ regenerated
  `.ipynb`), `docs/docs/tutorials/index.md`,
  `docs/docs/tutorials/index.json`, `tests/tutorials/baseline.json`,
  `docs/mkdocs.yml` nav, and `docs/docs/verification/ci_skip.txt` if the
  page is heavy. (The emcee resume page appears in index.md, index.json,
  and baseline.json — the new page must too.)
- Unit tests under `tests/unit/easydiffraction/analysis/minimizers/` and
  `io/`; integration test under `tests/integration/fitting/`.

## Implementation steps (Phase 1)

**Commit discipline (required of any AI agent following this plan).**
Each step below is one atomic change. Complete the step, edit its
`- [ ]` checkbox to `- [x]`, stage **only** that step's files with
explicit paths (per [`AGENTS.md`](../../../AGENTS.md) §Commits — no
`git add -A`, no unrelated dirty files), and make the local commit with
the step's `Commit:` message **before** starting the next step or the
Phase 1 review gate. Do not batch multiple steps into one commit.

- [x] **P1.1 — Rename sidecar `results.h5` → `mcmc.h5`, single-source
  the name, sweep all references.** Update `SIDECAR_FILE_NAME`, replace
  the duplicated literals in `fitting.py` / `analysis.py` with the
  constant/helper, update `__main__.py` messages. Then run
  `git grep -n 'results\.h5'` and update **every** tracked reference —
  the accepted ADRs (`analysis-cif-fit-state`,
  `minimizer-category-consolidation` incl. the per-engine-groups
  clarification, `undo-fit`, `minimizer-input-output-split`,
  `runtime-fit-results`, `edstar-project-persistence`) and index rows,
  the `fit-output-files-and-data-exports` suggestion, the user-guide and
  CLI docs, and the tests listed in Concrete files — excluding generated
  outputs. End on zero non-historical `results.h5` hits.
  Commit: `Rename Bayesian sidecar to mcmc.h5 and single-source it`.
- [x] **P1.2 — Persist the DREAM raw sampler state.** Capture the
  `MCMCDraw` in `BumpsDreamMinimizer`, add `_sidecar_path` (wired by the
  existing `Fitter._set_minimizer_sidecar_path`), and write a
  `dream_state` HDF5 group (`DreamFit.h5dump` + `param_names`) on save.
  Commit: `Persist bumps-dream sampler state to the mcmc sidecar`.
- [x] **P1.3 — DREAM resume: load, validate, extend.** Override `fit()`;
  load + deep-copy the state; validate count/population/names; translate
  `extra_steps` to `samples = current + N, burn = 0`; pass `fit_state`
  to the driver; add a DREAM resume-detection helper.
  Commit: `Implement bumps-dream resume via saved sampler state`.
- [x] **P1.4 — Reconcile unified resume semantics.** Ensure
  `resume=True, extra_steps=N` behaves consistently for emcee and DREAM
  at the `Fitter`/`analysis.fit` layer; share validation/detection
  helpers where clean. Commit: `Unify emcee and dream resume semantics`.
- [x] **P1.5 — Add `chains` alias for DREAM `population`.** User-facing
  `chains` alias with conflict detection and "population = scale factor"
  documentation. Commit: `Add chains alias for bumps-dream population`.
- [ ] **P1.6 — DREAM resume tutorial (+ registration).** Add
  `bayesian-dream-resume-lbco-hrpt.py` mirroring the emcee resume
  tutorial; `pixi run notebook-prepare`. Register it everywhere the
  emcee resume page is registered: `docs/mkdocs.yml` nav,
  `docs/docs/tutorials/index.md`, `docs/docs/tutorials/index.json`, and
  `tests/tutorials/baseline.json`; add to `ci_skip.txt` if heavy.
  Commit: `Add bumps-dream resume tutorial`.
- [ ] **P1.7 — Regenerate sidecar-referencing fixtures/tutorials.**
  Re-save committed project fixtures and tutorial outputs so the sidecar
  is `mcmc.h5`. Commit: `Regenerate fixtures for mcmc.h5 sidecar`.
- [ ] **P1.8 — Phase 1 review gate (no code).** Mark `[x]` and commit the
  checklist update alone. Commit: `Reach Phase 1 review gate`.

## Phase 2 — Verification

Use the zsh-safe capture pattern when saving output:

```bash
pixi run fix > /tmp/ed-fix.log 2>&1; fix_exit_code=$?; tail -n 40 /tmp/ed-fix.log; exit $fix_exit_code
pixi run check > /tmp/ed-check.log 2>&1; check_exit_code=$?; tail -n 60 /tmp/ed-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/ed-unit.log 2>&1; unit_exit_code=$?; tail -n 40 /tmp/ed-unit.log; exit $unit_exit_code
pixi run integration-tests > /tmp/ed-int.log 2>&1; int_exit_code=$?; tail -n 40 /tmp/ed-int.log; exit $int_exit_code
pixi run script-tests > /tmp/ed-script.log 2>&1; script_exit_code=$?; tail -n 40 /tmp/ed-script.log; exit $script_exit_code
```

New tests required:
- Unit: DREAM state round-trips through the `mcmc.h5` `dream_state`
  group; resume validation rejects mismatched count/population/names;
  `extra_steps` → `samples=current+N` translation; `chains`/`population`
  alias conflict.
- Unit — raw-state lifecycle (one sidecar, several engines):
  - a fresh (non-resume) fit clears **all** raw sampler-state groups
    (every engine), so no prior chain survives — including the
    emcee→fresh-DREAM→emcee-`resume=True` path, which must **not** resume
    the original emcee chain;
  - resume detection and resume read **only** the active minimizer's
    group;
  - explicit `resume=True` with a missing or malformed `dream_state`
    group raises a clear error; without `resume`, it is ignored and the
    fit starts fresh;
  - `undo_fit` clears the raw-state group(s).
- Integration: a small DREAM fit, `project.save()`, reload,
  `fit(resume=True, extra_steps=…)`, assert the chain grew by the
  expected number of draws and parity with a single longer run (mirror
  `test_emcee_resume_matches_small_dream_posterior`).
- Confirm `pixi run check` (link-check) passes after the tutorial/nav
  and ADR edits.

## Suggested Pull Request

**Title:** Resume and extend Bayesian (bumps-DREAM) refinements; clearer
MCMC results file

**Description:** You can now pause a Bayesian analysis run with the
bumps-DREAM sampler and later continue it for more steps — exactly as
already works for emcee — without losing the samples collected so far.
Saved sampling state is stored in the project's analysis folder in a
file now named `mcmc.h5` (previously `results.h5`), which better
reflects that it holds MCMC sampling output. Reloading a saved project
and asking for more steps simply extends the existing chains.
