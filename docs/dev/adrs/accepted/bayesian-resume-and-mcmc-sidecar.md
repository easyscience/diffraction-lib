# ADR: Bayesian Resume (DREAM) and MCMC Sidecar Naming

## Status

Accepted.

## Date

2026-06-15

## Group

Analysis and fitting.

## Context

EasyDiffraction supports two Bayesian MCMC minimizers: **emcee** and
**bumps DREAM**. Resume (continue/extend a previously sampled chain
across sessions) is implemented for **emcee only**:

- `MinimizerFitOptions.resume` / `extra_steps` and the matching
  `FitterFitOptions` already exist and are engine-agnostic.
- `MinimizerBase.fit()` raises `NotImplementedError("…does not support
  resume")`; `EmceeMinimizer` overrides `fit()` to implement it.
- emcee persists its raw chain **live during sampling** via
  `emcee.backends.HDFBackend(name='emcee_chain')` into the project's
  `analysis/results.h5` sidecar. Resume reads the last state from that
  HDF5 group and runs `extra_steps` more iterations.
- `BumpsDreamMinimizer` runs `FitDriver.fit()`, captures
  `driver.fitter.state` (a bumps `MCMCDraw`), but **discards** it. Only
  the *derived* posterior arrays reach the sidecar via
  `write_analysis_results_sidecar()`. The raw sampler state is never
  persisted, so there is nothing to resume from.

bumps DREAM **does** support resume — `FitDriver.fit(fit_state=…)` plus
`bumps.dream.state.save_state`/`load_state` (gzipped `.mc` text files) or
`DreamFit.h5dump`/`h5load` (HDF5). The capability is unused because the
caller must persist the state explicitly; emcee only looks "automatic"
because its backend streams to disk during the run.

`easyscience/core` PR #257 ("Bayesian extend/resume") is a reference
implementation for the DREAM-side mechanics: it surfaces the `MCMCDraw`
state in the result, accepts a `resume_state`, recovers the population
scale factor from `state.Npop`, validates parameter count/order, deep-
copies the state before fitting (bumps mutates it in place), and
documents the **ring-buffer contract** — DREAM keeps only the last
`samples` draws, so extending an M-draw chain by N means
`samples = M + N, burn = 0`.

Separately, the sidecar filename `results.h5` is misleading: the file
only ever holds MCMC/Bayesian content (posterior arrays, distribution
and pair caches, posterior-predictive sets, and emcee's raw chain) and
is created only for Bayesian minimizers — deterministic least-squares
results live in CIF, not here.

Two accepted ADRs currently fix the sidecar name and the
one-file rule:

- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — "The sidecar filename is fixed to `results.h5`".
- [`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
  — "There is exactly **one** sidecar file per fit, regardless of
  minimizer: `analysis/results.h5`".

## Decision

### 1. Extend resume to bumps DREAM, consistent with emcee

`BumpsDreamMinimizer` gains resume parity with `EmceeMinimizer` behind
the existing engine-agnostic API: `analysis.fit(resume=True,
extra_steps=N)`. The owner-level surface and `MinimizerFitOptions`
do not change. Internally:

- `BumpsDreamMinimizer` overrides `fit()` (like emcee) instead of
  inheriting the `NotImplementedError` guard.
- On a fresh run the resumable `MCMCDraw` state is **captured** and
  written to the sidecar at `project.save()`.
- On resume the state is loaded, deep-copied (bumps mutates it in
  place), validated against the current model, and passed as
  `FitDriver.fit(fit_state=…)`.
- The unified `extra_steps=N` is translated to DREAM's ring-buffer
  semantics: request `samples = current_draws + N` with `burn = 0`,
  recovering the population scale factor from `state.Npop` so the
  population is unchanged. emcee keeps its existing append semantics;
  the user-facing contract (`resume=True, extra_steps=N` adds N) is the
  same for both engines.

Resume validation mirrors emcee's `_validate_resume` but for DREAM
quirks: matching fitted-parameter count and population, and — because we
control persistence — **name-based** parameter validation (we store our
parameter names alongside the state, avoiding core's positional-only
fallback).

The DREAM minimizer also gains a user-facing **`chains` alias** for the
bumps `population` setting (an approved API addition): `chains` is the
discoverable name, `population` is accepted for parity with bumps, and
supplying both with different values raises. The documentation states
that `population` is a *scale factor* — bumps creates
`ceil(population · n_parameters)` chains.

### 2. Persist resumable raw sampler state per engine, in one sidecar

Both engines write their raw, resumable state into a **single** sidecar
file, distinguished by an **engine-keyed HDF5 group**:

- emcee: the existing `emcee_chain` group (unchanged mechanics).
- DREAM: a new top-level **`dream_state`** group containing the
  `MCMCDraw` written by `DreamFit.h5dump(group, state)`, plus a
  **`param_names`** dataset (the fitted-parameter names, in order) for
  name-based resume validation. This layout is fixed by this ADR, not
  deferred to implementation.

The derived posterior arrays (`/posterior/*`, caches, predictive sets)
continue to be written by `write_analysis_results_sidecar()` as today.

**State lifecycle (one sidecar, several engines).** A *fresh*
(non-resume) fit clears **all** raw sampler-state groups (both
`emcee_chain` and `dream_state`) before writing — consistent with the
existing rule that `analysis.fit()` truncates the sidecar (see
`minimizer-category-consolidation.md` §4). Clearing *every* group, not
just the active engine's, is what prevents the stale-state trap: an
emcee fit, then a fresh DREAM fit, then `emcee resume=True` must **not**
resume the original emcee chain. Resume detection and resume then read
**only** the group matching the active minimizer
(`analysis.minimizer.type`). On explicit `resume=True` a missing or
malformed active-engine group is a clear error; otherwise it is ignored
and the fit starts fresh. `undo_fit` clears the raw-state group(s) the
same way it already clears the sidecar.

### 3. Rename the sidecar `results.h5` → `mcmc.h5`

The sidecar is renamed to reflect its content. It remains **one file per
fit** (the consolidation ADR's invariant holds; only the name changes).
The filename is defined once as a single constant and the two duplicated
string literals in `analysis/fitting.py` and `analysis/analysis.py` are
replaced by that constant / a shared path helper.

### 4. Amendments to accepted ADRs

The rename touches **every** repository reference to `results.h5`, not
only the two ADRs that fix the name. On implementation, a
`git grep -n 'results\.h5'` sweep updates all source, docs, tests, and
tracked fixtures (excluding generated/transient outputs). Concretely
this currently spans:

- Accepted ADRs: `analysis-cif-fit-state.md` (filename `results.h5` →
  `mcmc.h5`), `minimizer-category-consolidation.md` (filename + the
  per-engine-state-groups clarification above), `undo-fit.md`,
  `minimizer-input-output-split.md`, `runtime-fit-results.md`,
  `edstar-project-persistence.md`, and the `docs/dev/adrs/index.md` rows.
- Suggestion ADR `fit-output-files-and-data-exports.md`.
- User docs: `docs/docs/cli/index.md`,
  `docs/docs/user-guide/{concept,data-format}.md`,
  `docs/docs/user-guide/analysis-workflow/{analysis,project}.md`.
- Source: `io/results_sidecar.py`, `analysis/fitting.py`,
  `analysis/analysis.py`, `__main__.py`.
- Tests referencing the literal, and any tracked project fixtures.

## Consequences

- Resume/extend works identically for emcee and DREAM from the user's
  point of view; the long-running Bayesian tutorials gain a DREAM resume
  page mirroring the emcee one.
- The sidecar name communicates intent (`mcmc.h5`), and the filename
  lives in exactly one place.
- The project is in beta (no legacy shims): committed project fixtures,
  tutorials, and any test referencing `results.h5` are regenerated /
  updated to `mcmc.h5`; old saved projects must be re-saved.
- No new third-party dependency: `bumps` is already a dependency and its
  `MCMCDraw`/`h5dump`/`h5load` API is used directly.
- DREAM resume persists a second representation of the chain (raw state)
  alongside the derived posterior; the sidecar grows modestly.

## Alternatives Considered

- **Per-engine filenames (`mcmc_emcee.h5`, `mcmc_bumps-dream.h5`).**
  Rejected: forces the load/undo/clear paths to resolve "which file"
  from the active minimizer and breaks the one-sidecar invariant for
  little gain over engine-keyed groups in one file.
- **Persist DREAM state as bumps `.mc.gz` text triples (as
  `easyscience/core` does).** Rejected: three extra files per fit and a
  dependence on bumps' text parser, which has a known 1.0.4 regression
  (`load_state` collapses single-row buffers to 1-D). `DreamFit.h5dump`
  into the existing sidecar avoids both.
- **Keep the `results.h5` name.** Rejected: misleading; the file is
  MCMC-only.
- **In-memory-only resume (no disk persistence).** Rejected: resume must
  survive `project.save()`/load across sessions, which is the whole
  point.
