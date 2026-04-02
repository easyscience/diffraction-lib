# Sequential Fitting — Architecture Design

**Status:** Draft — for discussion before implementation  
**Date:** 2026-04-02

---

## 1. Motivation

The current single-fit mode (`fit_mode = 'single'`) iterates over
pre-loaded experiments sequentially. Structural parameters propagate
from one fit to the next, and per-experiment snapshots are stored in
memory (`Analysis._parameter_snapshots`). This works well for tens or
hundreds of datasets (e.g. the D20 temperature scan in `ed-17.py`) but
does not scale to thousands or tens of thousands of files:

| Limitation                   | Impact at scale (N > 1000)                    |
| ---------------------------- | --------------------------------------------- |
| All experiments pre-loaded   | Memory grows linearly with N                  |
| Single-threaded              | Wall-clock time grows linearly with N         |
| Snapshots in memory only     | Lost on crash; no incremental persistence     |
| Structure params overwritten | Cannot replot earlier datasets after the loop |

Users at ESS request fitting of up to ~50 000 data files from
dose-resolved or time-resolved experiments.

---

## 2. Current State

### 2.1 Single-fit loop (Analysis.fit, mode='single')

```
for each experiment in project.experiments:
    create dummy Experiments wrapper (1 experiment)
    fitter.fit(structures, dummy_experiments)
    snapshot fitted params in memory dict
```

- Structure parameters are shared: the `Structures` collection is passed
  directly to `Fitter.fit()`, so each fit mutates the same `Structure`
  objects.
- Experiment parameters are independent: each `ExperimentBase` has its
  own instrument, peak, background, etc.
- After the loop, `_parameter_snapshots[expt_name]` contains
  `{unique_name: {value, uncertainty, units}}` per experiment.
- `plot_param_series()` reads from `_parameter_snapshots` and the live
  `experiments` collection (for diffrn metadata like temperature).

### 2.2 Limitations for the proposed feature

- `ExperimentFactory.from_data_path()` creates a fresh experiment with
  default parameters — it cannot directly clone a template experiment's
  full configuration (instrument type, peak type, background points,
  excluded regions, linked phases).
- `ConstraintsHandler` and `UidMapHandler` are process-wide singletons —
  concurrent access from multiple threads would cause state corruption.
- `CryspyCalculator` stores `_cryspy_dicts` per
  `{structure}_{experiment}` — pure-Python computation, does not release
  the GIL.

---

## 3. Requirements

Numbered to match the original request.

1. **No bulk preloading** — do not create all experiment objects in
   advance.
2. **Parallel fitting** — run multiple independent fits simultaneously.
3. **Parameter propagation** — reuse fitted parameters from the previous
   chunk as starting values for the next chunk.
4. **Chunk-based processing** — load N datasets, fit N independently in
   parallel, propagate, repeat.
5. **Incremental CSV output** — one row per dataset, written after each
   chunk; includes χ², fit status, and all fitted parameter values +
   uncertainties.
6. **Crash recovery** — on restart, read CSV, skip already-fitted files,
   resume from the last fitted row's parameters.
7. **Separate initial fit** — the user runs a regular `fit()` on one
   dataset first to establish good starting values.
8. **Store all fitted parameters in CSV** — both structure and
   experiment params, so any dataset can be replayed later. The project
   file retains only the template structure CIF and template experiment
   CIF.
9. **Scalable** — works for N = 1 (degenerate case) and N = 50 000.
10. **`max_workers` configuration** — default `1` (sequential), user can
    set higher or `'auto'`.
11. **Consider alternatives** — see § 7.

---

## 4. Design Overview

A new method `Analysis.fit_sequential()` orchestrates the batch. It does
**not** reuse the existing `fit()` loop — the data-flow is fundamentally
different (data paths in → CSV out, experiments are ephemeral).

```
User sets up: 1 Structure + 1 template Experiment
         │
         ▼
  project.analysis.fit()          ← initial fit on template
         │
         ▼
  project.analysis.fit_sequential(
      data_paths=[...],
      output_csv='results.csv',
      max_workers=4,
  )
         │
         ▼
  ┌──────────────────────────────┐
  │  Read CSV for crash recovery │
  │  Skip already-fitted files   │
  │  Seed params from last row   │
  └──────┬───────────────────────┘
         │
         ▼
  ┌──────────────────────────────┐
  │  For each chunk of N files:  │
  │                              │
  │  ┌────┐ ┌────┐     ┌────┐   │
  │  │ W1 │ │ W2 │ ... │ Wn │   │  Workers (processes)
  │  └──┬─┘ └──┬─┘     └──┬─┘   │
  │     │      │           │     │
  │     ▼      ▼           ▼     │
  │  Collect results             │
  │  Append rows to CSV          │
  │  Propagate params from       │
  │  last file in chunk          │
  └──────────────────────────────┘
         │
         ▼
  CSV with all results
  (one row per dataset)
```

---

## 5. User-Facing API

### 5.1 The template workflow

```python
import easydiffraction as ed

project = ed.Project()
project.verbosity = 'short'

# ── Structure ────────────────────────────────────────────
project.structures.create(name='cosio')
structure = project.structures['cosio']
structure.space_group.name_h_m = 'P n m a'
structure.cell.length_a = 10.31
# ... atom sites ...

# ── Template experiment ──────────────────────────────────
data_paths = ed.extract_data_paths_from_zip('scans.zip')

project.experiments.add_from_data_path(
    name='template',
    data_path=data_paths[0],
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)
expt = project.experiments['template']
expt.instrument.setup_wavelength = 1.87
expt.peak.broad_gauss_u = 0.24
expt.background.create(id='1', x=8, y=609)
# ... more experiment config ...
expt.linked_phases.create(id='cosio', scale=1.2)

# ── Free parameters ──────────────────────────────────────
structure.cell.length_a.free = True
expt.linked_phases['cosio'].scale.free = True
expt.instrument.calib_twotheta_offset.free = True
for point in expt.background:
    point.y.free = True

# ── Constraints (optional) ───────────────────────────────
project.analysis.aliases.create(
    label='biso_Co1',
    param_uid=structure.atom_sites['Co1'].b_iso.uid,
)
project.analysis.constraints.create(expression='biso_Co2 = biso_Co1')
project.analysis.apply_constraints()

# ── Initial fit on the template ──────────────────────────
project.analysis.fit()
project.analysis.show_fit_results()

# ── Sequential fit over all files ────────────────────────
project.analysis.fit_sequential(
    data_paths=data_paths,
    output_csv='results.csv',
    max_workers=4,
)
```

### 5.2 Method signature

```python
def fit_sequential(
    self,
    data_paths: list[str],
    output_csv: str,
    max_workers: int = 1,
    chunk_size: int | None = None,
    verbosity: str | None = None,
) -> None:
```

| Parameter     | Description                                                                           |
| ------------- | ------------------------------------------------------------------------------------- |
| `data_paths`  | Ordered list of data file paths to process.                                           |
| `output_csv`  | Path to the output CSV file. Created if missing, appended if exists (crash recovery). |
| `max_workers` | Number of parallel worker processes. `1` = sequential (no subprocess overhead).       |
| `chunk_size`  | Files per chunk. Default `None` → uses `max_workers`.                                 |
| `verbosity`   | `'full'`, `'short'`, `'silent'`. Default: project verbosity.                          |

### 5.3 Plotting results from CSV

After `fit_sequential()`, parameter evolution is read from the CSV file
rather than from in-memory snapshots:

```python
project.plot_param_series_from_csv(
    csv_path='results.csv',
    param=structure.cell.length_a,
    versus=expt.diffrn.ambient_temperature,
)
```

Alternatively, `plot_param_series()` could detect whether the data
source is in-memory snapshots (small N) or a CSV file (large N) based on
whether `output_csv` was produced. This is a UX decision to discuss.

### 5.4 Replaying a single dataset

To replot or inspect one dataset from the batch:

```python
# Load template project
project = ed.Project.load('my_project')

# Replace fitted params for dataset #500 from CSV
project.apply_params_from_csv('results.csv', row=500)

# Plot
project.plot_meas_vs_calc(expt_name='template')
```

This requires loading the dataset's data file and overriding parameter
values from the CSV row. The exact API can be refined; the key point is
that CSV + template CIF is sufficient to reconstruct any dataset's
state.

---

## 6. Internal Architecture

### 6.1 Preconditions

`fit_sequential()` validates before starting:

- Exactly 1 structure in `project.structures`.
- Exactly 1 experiment in `project.experiments` (the template).
- At least 1 free parameter.
- `output_csv` path is writable.
- `data_paths` is non-empty.

### 6.2 Template snapshot

Before dispatching workers, the method captures a **template snapshot**
— everything a worker needs to recreate the project independently:

```python
@dataclass(frozen=True)
class SequentialFitTemplate:
    structure_cif: str          # structure.as_cif
    experiment_cif: str         # experiment.as_cif (template experiment)
    experiment_axes: dict       # {sample_form, beam_mode, radiation_probe, scattering_type}
    initial_params: dict        # {unique_name: value} for ALL free params
    free_param_names: list[str] # unique_names of free params
    alias_defs: list[dict]      # [{label, param_uid}, ...]
    constraint_defs: list[str]  # [expression, ...]
    minimizer_tag: str          # e.g. 'lmfit'
    calculator_tag: str         # e.g. 'cryspy'
```

This is a plain, picklable data object (no live references to
`GuardedBase` instances).

### 6.3 Chunk-based processing

```python
remaining_paths = [p for p in data_paths if p not in already_fitted]

for chunk in chunked(remaining_paths, chunk_size):
    if max_workers == 1:
        results = [_fit_worker(template, path) for path in chunk]
    else:
        with ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=get_context('spawn'),
        ) as pool:
            futures = {
                pool.submit(_fit_worker, template, path): path
                for path in chunk
            }
            results = [f.result() for f in as_completed(futures)]

    # Sort results to match file order (as_completed is unordered)
    results.sort(key=lambda r: data_paths.index(r['file_path']))

    _append_to_csv(output_csv, results)

    # Propagate: use last file's params as next chunk's starting values
    last_result = results[-1]
    template = replace(template, initial_params=last_result['params'])
```

The `'spawn'` context is required because:

- `cryspy` is pure Python — the GIL prevents true thread parallelism.
- `fork` can deadlock with C extensions and is unreliable on macOS.
- `spawn` creates a fresh Python interpreter per worker — singletons
  (`UidMapHandler`, `ConstraintsHandler`) are naturally isolated.

### 6.4 Worker function

The worker is a **module-level function** (required for pickling by
`ProcessPoolExecutor`):

```python
def _fit_worker(
    template: SequentialFitTemplate,
    data_path: str,
) -> dict[str, Any]:
    """
    Fit a single dataset in an isolated process.

    Creates a fresh Project, loads the template configuration,
    replaces data from data_path, applies initial parameters, fits,
    and returns a plain dict of results.
    """
    # 1. Create fresh project (isolated singletons, no shared state)
    project = Project(name='_worker')

    # 2. Load structure from CIF
    project.structures.add_from_cif_str(template.structure_cif)

    # 3. Create experiment from data path (loads measured data)
    project.experiments.add_from_data_path(
        name='expt',
        data_path=data_path,
        sample_form=template.experiment_axes['sample_form'],
        beam_mode=template.experiment_axes['beam_mode'],
        radiation_probe=template.experiment_axes['radiation_probe'],
        scattering_type=template.experiment_axes['scattering_type'],
        verbosity='silent',
    )

    # 4. Apply template experiment configuration
    _apply_template_config(
        experiment=project.experiments['expt'],
        template=template,
    )

    # 5. Override parameter values from propagated starting values
    _apply_param_overrides(project, template.initial_params)

    # 6. Set free flags
    _set_free_params(project, template.free_param_names)

    # 7. Apply constraints
    _apply_constraints(project, template.alias_defs, template.constraint_defs)

    # 8. Set calculator and minimizer
    project.experiments['expt'].calculator_type = template.calculator_tag
    project.analysis.current_minimizer = template.minimizer_tag

    # 9. Fit
    project.analysis.fit(verbosity='silent')

    # 10. Collect results
    return _collect_results(project, data_path)
```

#### Step 4: Applying template configuration

The template experiment's CIF contains instrument, peak, background,
excluded regions, linked phases, and their parameters. However,
`add_from_data_path` creates an experiment with default configuration.
The worker must then apply the template's configuration on top.

**Two approaches:**

| Approach                                   | Pros                                               | Cons                                                                                                      |
| ------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **A. Create from CIF, reload data**        | All config comes from CIF; no manual param copying | Requires `_load_ascii_data_to_experiment()` to work after CIF construction; CIF must round-trip perfectly |
| **B. Create from data path, apply config** | Data loading is clean; explicit param assignment   | Requires enumerating which template settings to copy; more fragile if experiment categories change        |

**Recommended: Approach A** — create from template CIF, then reload
data. This is more robust because:

- CIF serialisation already captures the full experiment state.
- Adding new categories or parameters requires no changes to the worker.
- `_load_ascii_data_to_experiment()` already exists on all concrete
  experiment classes.

```python
# Approach A sketch:
# 3. Create experiment from template CIF (full config + template data)
project.experiments.add_from_cif_str(template.experiment_cif)
expt = project.experiments['template']
expt.name = 'expt'  # rename for consistency

# 4. Replace data from new data path
expt._load_ascii_data_to_experiment(data_path)
```

**Prerequisite:** `_load_ascii_data_to_experiment` must correctly
overwrite the existing data category contents (clear old data points and
load new ones). This needs to be verified and potentially adjusted.

**Open question:** Does `experiment.as_cif` round-trip cleanly through
`ExperimentFactory.from_cif_str()`? If not, Approach A is blocked until
CIF round-trip is reliable (see `issues_open.md` issue #1 and #12).
Approach B would be the fallback. See § 8 open question 2.

### 6.5 Parameter propagation strategy

After each chunk completes:

1. Take the results from the **last file** in the chunk (by file sort
   order).
2. Extract all free parameter values.
3. Use these as `initial_params` for all workers in the next chunk.

**Why the last file?** Assuming files are ordered (by time, temperature,
dose), the last file's parameters are the closest extrapolation for the
next chunk. Within a chunk, all workers start from the same values, so
parameter evolution within a chunk comes only from the fit — not from
propagation.

**Edge case — last file's fit failed:** if the last file in a chunk
fails, fall back to the last _successful_ result in the chunk (scanning
from the end). If no file in the chunk succeeded, keep the previous
chunk's parameters and log a warning.

**Within-chunk ordering matters for `max_workers=1`:** when running
sequentially (`max_workers=1`), the chunk size is 1, so propagation
happens after every file — identical to the current single-fit mode.
This preserves backward compatibility.

### 6.6 CSV output format

The CSV uses a flat header with two columns per free parameter (value +
uncertainty) plus metadata columns:

```
file_path,chi_squared,reduced_chi_squared,fit_success,n_iterations,cosio.cell.length_a,cosio.cell.length_a.uncertainty,cosio.atom_sites.Co1.b_iso,cosio.atom_sites.Co1.b_iso.uncertainty,template.instrument.calib_twotheta_offset,template.instrument.calib_twotheta_offset.uncertainty,...
/data/scan_001.xye,142.3,1.23,True,45,10.312,0.001,0.31,0.02,0.29,0.01,...
/data/scan_002.xye,138.1,1.19,True,32,10.315,0.002,0.32,0.03,0.28,0.01,...
```

| Column                      | Type  | Description                     |
| --------------------------- | ----- | ------------------------------- |
| `file_path`                 | str   | Absolute path to the data file  |
| `chi_squared`               | float | χ² of the fit                   |
| `reduced_chi_squared`       | float | Reduced χ²                      |
| `fit_success`               | bool  | Whether the minimizer converged |
| `n_iterations`              | int   | Number of minimizer iterations  |
| `{unique_name}`             | float | Fitted value of parameter       |
| `{unique_name}.uncertainty` | float | Uncertainty of parameter        |

**Implementation:** use `csv.DictWriter` (stdlib). Header is written
once on file creation. Rows are appended after each chunk and flushed
immediately (no buffered writes that could be lost on crash).

### 6.7 Crash recovery

On entry, `fit_sequential()` checks for an existing CSV at `output_csv`:

1. If the file exists and is non-empty:
   - Read all rows.
   - Build a set of already-fitted `file_path` values.
   - Extract parameter values from the last row as starting values
     (overrides `initial_params` from the template).
   - Log a message: `"Resuming from row N (M files already fitted)."`.
2. If the file does not exist or is empty:
   - Create the file with the header row.
   - Use the template's current parameter values as starting values.

The file path comparison uses absolute paths to avoid mismatches.

### 6.8 Verbosity and progress reporting

| Verbosity | Behaviour                                                           |
| --------- | ------------------------------------------------------------------- |
| `full`    | Per-chunk progress: chunk N/M, per-file χ² table (updated in place) |
| `short`   | One-line per chunk: `✅ Chunk 3/500: 10 files, avg χ² = 1.45`       |
| `silent`  | No output                                                           |

Workers always run silently. Only the main process produces console
output.

---

## 7. Alternatives Considered

### 7.1 Threading instead of multiprocessing

Threading (`concurrent.futures.ThreadPoolExecutor`) is simpler — no
pickling, shared memory. However:

- `cryspy` is pure Python and does not release the GIL. Threaded fits
  would execute serially despite multiple threads.
- `crysfml` is a Fortran extension; it may release the GIL during
  computation, but this is not guaranteed.
- Singletons (`UidMapHandler`, `ConstraintsHandler`) would need locks or
  thread-local storage.

**Verdict:** threading does not provide true parallelism for the primary
compute backend. Multiprocessing is required.

### 7.2 Dask / joblib / Ray

These are mature parallel computing frameworks.

| Framework | Pros                            | Cons                                   |
| --------- | ------------------------------- | -------------------------------------- |
| Dask      | Lazy graphs, dashboard, retry   | Heavy dependency, learning curve       |
| joblib    | Simple `Parallel(n_jobs=N)` API | Less control over chunking/propagation |
| Ray       | Distributed, stateful actors    | Very heavy dependency                  |

**Verdict:** the stdlib `concurrent.futures.ProcessPoolExecutor` is
sufficient. Adding a large dependency is not justified when the
parallelism pattern (chunked map with reduce between chunks) is
straightforward. Can reconsider if cluster-scale execution becomes a
requirement.

### 7.3 Adaptive chunk sizing

Start with large chunks when parameter evolution is slow (fits converge
quickly), shrink chunks when fits fail or χ² increases. This maximises
parallelism when it is safe.

**Verdict:** valuable optimisation but adds complexity. Defer to a
future iteration. Fixed `chunk_size = max_workers` is the safe default.

### 7.4 Neighbour-seeded propagation

Instead of propagating from the last file in a chunk, propagate from the
nearest successful fit to each file (based on file order or metadata
like temperature). This helps with non-monotonic parameter evolution.

**Verdict:** interesting for non-sequential scans but out of scope for
the initial implementation. The file-order assumption is valid for the
primary use case (temperature / dose scans).

### 7.5 Parallel single-fit for pre-loaded experiments

Add `max_workers` to the existing `fit()` method for pre-loaded
experiments. Internally, chunk the experiments and fit in parallel using
the same worker pattern.

**Verdict:** this is a natural follow-up that reuses the same
infrastructure. However, the primary value of `fit_sequential` is
avoiding bulk preloading. Adding `max_workers` to `fit()` is a separate,
smaller enhancement that can come later.

---

## 8. Open Questions

1. **Should `max_workers='auto'` use `os.cpu_count()`?** Or a fraction
   like `cpu_count() - 1` to leave headroom? Or
   `min(cpu_count(), len(data_paths))`?

2. **CIF round-trip reliability.** Approach A (§ 6.4) depends on
   `experiment.as_cif → ExperimentFactory.from_cif_str()` reproducing
   the full experiment state. Is this currently reliable, or does it
   lose information (e.g. category type selections, calculator tag)? If
   unreliable, Approach B (explicit config copy) is the fallback but
   requires more maintenance.

3. **Does `_load_ascii_data_to_experiment()` work on an experiment that
   already has data?** If it appends rather than replaces, a clear/reset
   step is needed before the call.

4. **Should the worker use the project's current verbosity, or always
   run silently?** Workers running in subprocesses cannot safely write
   to the same terminal. Silent is safest, but progress from workers is
   lost.

5. **Constraint UIDs.** Constraints reference parameters by UID
   (`param_uid`). When the worker creates a fresh project, UIDs are
   regenerated. If UIDs are deterministic (derived from CIF path), this
   is fine. If they are random, constraints will fail in the worker.
   Need to verify UID generation strategy.

6. **`plot_param_series` unification.** Should the existing
   `plot_param_series()` learn to read from CSV, or should there be a
   separate `plot_param_series_from_csv()` method? Unification is
   cleaner for the user but adds complexity.

7. **Metadata in CSV.** Should the CSV include per-file metadata (e.g.
   temperature, dose) extracted from the data files? This would make the
   CSV self-contained for plotting. But it requires knowing which
   metadata to extract — perhaps via a user-provided extraction function
   or regex pattern.

---

## 9. Implementation Plan

Each phase is independently testable and deployable.

### Phase 1: Streaming sequential fit (max_workers=1)

- Add `fit_sequential()` to `Analysis`.
- Implement `SequentialFitTemplate` dataclass.
- Implement `_fit_worker()` as a plain function (called directly, no
  subprocess).
- Implement CSV writing with `csv.DictWriter`.
- Implement crash recovery (CSV reading + resumption).
- Implement parameter propagation (simple: last result → next
  iteration).
- Unit tests for CSV writing, crash recovery, and parameter propagation.
- Integration test: small sequential fit (5 files), verify CSV output.

**Validates:** the core data flow, CSV format, and parameter
propagation. No multiprocessing complexity yet.

### Phase 2: Parallel fitting (max_workers > 1)

- Refactor `_fit_worker()` to be a module-level picklable function.
- Implement `ProcessPoolExecutor` dispatch with `spawn` context.
- Handle worker failures (catch exceptions, mark as failed in CSV,
  continue with next chunk).
- Implement propagation with failed-fit fallback.
- Integration test: parallel sequential fit (10 files, 2 workers).

**Validates:** multiprocessing isolation, singleton safety, no shared
state corruption.

### Phase 3: Plotting from CSV

- Add `plot_param_series_from_csv()` to `Project`.
- Read CSV with `pandas`, resolve column names to parameter
  unique_names.
- Reuse the existing `Plotter.plot_scatter` backend.
- Optionally unify with `plot_param_series()`.

### Phase 4: Dataset replay

- Add `apply_params_from_csv()` to `Project` (or a helper method).
- Load a specific CSV row, override parameter values in the live
  project.
- Reload data from the file path in the CSV row.
- Allow `plot_meas_vs_calc()` to work with the replayed state.

### Phase 5 (optional): max_workers on existing fit()

- Add `max_workers` parameter to `Analysis.fit()`.
- When `fit_mode == 'single'` and `max_workers > 1`, serialize
  pre-loaded experiments and dispatch to the same worker pool.
- Propagate between chunks, store snapshots in memory (existing
  behaviour) or CSV if `output_csv` is provided.

---

## 10. Dependencies and Risks

### New dependencies

**None.** `concurrent.futures`, `csv`, `multiprocessing`, `dataclasses`
are all stdlib.

### Risks

| Risk                                              | Mitigation                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------- |
| CIF round-trip loses information                  | Verify with a round-trip test before Phase 1; fall back to Approach B if needed |
| UID non-determinism breaks constraints in workers | Verify UID generation; make deterministic if needed                             |
| Worker memory leak (large N, long-running pool)   | Use `max_tasks_per_child=100` on the pool to recycle workers                    |
| Pickling failures for SequentialFitTemplate       | Keep it a plain dataclass with only str/dict/list fields                        |
| crysfml Fortran global state in forked processes  | Enforced `spawn` context avoids fork issues                                     |

### Related open issues

- **Issue #1 (Project.load):** `fit_sequential` does not depend on
  `load()`, but Phase 4 (dataset replay) benefits from it.
- **Issue #7 (dummy Experiments wrapper):** `fit_sequential` bypasses
  this entirely — each worker creates its own `Experiments`.
- **Issue #4 (constraint refresh):** the worker's fresh project applies
  constraints from scratch — no stale state. But the main process must
  still correctly capture alias/constraint definitions in the template.

---

## 11. Summary

| Aspect               | Decision                                                |
| -------------------- | ------------------------------------------------------- |
| Parallelism backend  | `concurrent.futures.ProcessPoolExecutor` with `spawn`   |
| Worker isolation     | Each worker creates a fresh `Project` — no shared state |
| Data flow            | Template CIF + data path → worker → result dict → CSV   |
| Parameter seeding    | Last successful result in chunk → next chunk            |
| Crash recovery       | Read existing CSV, skip fitted files, resume            |
| Configuration        | `max_workers` argument on `fit_sequential()`            |
| New dependencies     | None (stdlib only)                                      |
| First implementation | Phase 1 (sequential, no parallelism) to validate design |
