# Sequential Fitting — Architecture Design

**Status:** Implementation in progress (PRs 1–10 complete, PRs 11–14
remaining) **Date:** 2026-04-02 (updated 2026-04-03)

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

### 2.3 UID vs unique_name

Parameter UIDs are **random** (16-char `secrets.choice`) and
non-deterministic. They do not survive CIF round-trips or cross-process
recreation. The `unique_name` property (e.g. `cosio.cell.length_a`) is
**deterministic** — derived from the parent chain — and is already used
as the column key in CIF serialisation (`CifHandler.uid` returns
`unique_name`).

The alias system currently stores `param_uid` (the random UID) as a
`StringDescriptor`. For sequential fitting to work across processes,
constraints must reference parameters by `unique_name` instead. This is
a prerequisite change (see § 9.1).

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
   chunk; includes χ², fit status, diffrn metadata, and all fitted
   parameter values + uncertainties.
6. **Crash recovery** — on restart, read CSV, skip already-fitted files,
   resume from the last fitted row's parameters.
7. **Separate initial fit** — the user runs a regular `fit()` on one
   dataset first to establish good starting values. The template is a
   complete working experiment, not just a skeleton.
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
different (data directory in → CSV out, experiments are ephemeral).

```
User sets up: 1 Structure + 1 template Experiment (fully configured)
         │
         ▼
  project.analysis.fit()          ← initial fit on template
         │
         ▼
  project.analysis.fit_sequential(
      data_dir='data/',
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
  │  Report progress             │
  │  Propagate params from       │
  │  last file in chunk          │
  └──────────────────────────────┘
         │
         ▼
  CSV in project_dir/analysis/results.csv
```

---

## 5. User-Facing API

### 5.1 Data path handling

Data files can come from various sources: a local directory, a ZIP
archive, or (in future) an online catalogue. The library already
provides helpers for extracting paths:

- `ed.extract_data_paths_from_zip(zip_path)` → extracts to a temp dir,
  returns sorted file paths.
- `ed.extract_data_paths_from_dir(dir_path)` → lists files in a
  directory, returns sorted file paths.

For sequential fitting, the user points `fit_sequential` at a
**directory** containing the data files. If the data arrives as a ZIP,
the user first extracts it:

```python
# From a ZIP archive — extract first, then point to directory
ed.extract_data_paths_from_zip('scans.zip', destination='data/')
project.analysis.fit_sequential(data_dir='data/')

# From a local directory — use directly
project.analysis.fit_sequential(data_dir='/experiment/scans/')
```

The `extract_data_paths_from_zip` function gains an optional
`destination` parameter. When provided, it extracts to that directory
instead of a temp dir. This gives a consistent directory-based entry
point for all data sources (local, ZIP, future catalogue downloads).

Internally, `fit_sequential` calls `extract_data_paths_from_dir` to
discover and sort files from the given directory.

### 5.2 The template workflow

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

# ── Template experiment (fully configured) ───────────────
project.experiments.add_from_data_path(
    name='template',
    data_path='data/scan_001.xye',
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
    param_unique_name=structure.atom_sites['Co1'].b_iso.unique_name,
)
project.analysis.constraints.create(expression='biso_Co2 = biso_Co1')
project.analysis.apply_constraints()

# ── Initial fit on the template ──────────────────────────
project.analysis.fit()
project.analysis.show_fit_results()

# ── Save project (defines project path) ──────────────────
project.save_as(dir_path='cosio_project')

# ── Sequential fit over all files in data/ ───────────────
project.analysis.fit_sequential(
    data_dir='data/',
    max_workers=4,
)
```

### 5.3 Method signature

```python
def fit_sequential(
    self,
    data_dir: str,
    max_workers: int | str = 1,
    chunk_size: int | None = None,
    file_pattern: str = '*',
    extract_diffrn: Callable[[str], dict[str, float | str]] | None = None,
    verbosity: str | None = None,
) -> None:
```

| Parameter        | Description                                                                                          |
| ---------------- | ---------------------------------------------------------------------------------------------------- |
| `data_dir`       | Path to directory containing data files.                                                             |
| `max_workers`    | Number of parallel worker processes. `1` = sequential. `'auto'` = physical CPU count.                |
| `chunk_size`     | Files per chunk. Default `None` → uses `max_workers`.                                                |
| `file_pattern`   | Glob pattern to filter files in `data_dir`. Default `'*'` (all non-hidden files).                    |
| `extract_diffrn` | User callback: `f(file_path) → {diffrn_field: value}`. Called per file. `None` = no diffrn metadata. |
| `verbosity`      | `'full'`, `'short'`, `'silent'`. Default: project verbosity.                                         |

The CSV output path is **not** a parameter — it is determined by the
project directory structure (see § 5.4).

When `max_workers='auto'`, the worker count is resolved as
`os.cpu_count()` (physical CPU count), following the `pytest-xdist`
convention for `-n auto`.

### 5.4 Project directory structure

The current project layout has `analysis.cif` as a top-level file next
to directories like `structures/` and `experiments/`. Adding an
`analysis/` directory alongside a file named `analysis.cif` at the same
level is confusing and violates the principle of least surprise.

**Decision:** move `analysis.cif` into the `analysis/` directory. All
analysis-related artifacts live under one directory — settings _and_
results:

```
project_dir/
├── project.cif
├── summary.cif
├── structures/
│   └── cosio.cif
├── experiments/
│   └── template.cif           ← the fully-configured template
└── analysis/
    ├── analysis.cif           ← analysis settings (was at top level)
    └── results.csv            ← sequential fit output
```

This is a clean, self-consistent layout:

- Every major concept (`structures`, `experiments`, `analysis`) gets its
  own directory.
- `project.cif` and `summary.cif` remain at the top level because they
  describe the project as a whole, not a single domain.
- No name collision between a file and a directory.
- Future analysis artifacts (e.g. per-experiment fit logs, constraint
  snapshots) naturally live under `analysis/`.

**Migration:** `Project.save()` writes `analysis.cif` to
`project_dir/analysis/analysis.cif` instead of
`project_dir/analysis.cif`. `Project.load()` (when implemented) reads
from the new location. Existing saved projects with `analysis.cif` at
the top level can be handled by a fallback in `load()` — check the new
path first, then fall back to the old path.

The CSV path is always `project_dir / 'analysis' / 'results.csv'`. This
means:

- The user must call `save_as()` before `fit_sequential()` to establish
  the project path.
- `fit_sequential()` validates that `project.info.path` is set.
- No need to pass `output_csv` — the location is deterministic and
  discoverable.

### 5.5 Plotting results

`plot_param_series()` **always** reads from the CSV file in the
project's `analysis/` directory. This unifies the small-N and large-N
cases — every sequential or single-mode fit produces a CSV, making
results persistent, portable, and usable by external tools.

```python
# Plot parameter evolution (reads from analysis/results.csv)
project.plot_param_series(
    param=structure.cell.length_a,
    versus=expt.diffrn.ambient_temperature,
)
```

The method resolves `param` and `versus` to their `unique_name`
internally, then looks up the corresponding CSV columns. The user passes
the live descriptor object (e.g. `structure.cell.length_a`) for
discoverability and autocomplete — they never need to type or know the
`unique_name` string.

**Why `param` objects, not strings?** The user already has a reference
to `structure.cell.length_a` — passing it directly is more natural and
typo-safe than passing `'cosio.cell.length_a'`. The method extracts
`.unique_name` itself. This matches the current API.

### 5.6 Replaying a single dataset

To replot or inspect one dataset from the batch:

```python
# Load project (when Project.load() is implemented)
project = ed.Project.load('cosio_project')

# Replace fitted params for dataset #500 from CSV
project.apply_params_from_csv(row=500)

# Plot (uses the template experiment with overridden params)
project.plot_meas_vs_calc(expt_name='template')
```

The CSV row index identifies the dataset. `apply_params_from_csv`:

1. Reads the CSV row.
2. Loads the data file from the `file_path` column into the template
   experiment.
3. Overrides all parameter values from the CSV columns.

### 5.7 Diffrn metadata in CSV

The CSV includes all descriptors from the `diffrn` category
(temperature, pressure, magnetic field, electric field) as additional
columns. This makes the CSV self-contained for plotting parameter
evolution against any condition axis, e.g. temperature vs. magnetic
field, without needing to re-read the original data files.

#### Why metadata extraction stays explicit

In the current `ed-17.py` tutorial, the user writes:

```python
expt.diffrn.ambient_temperature = ed.extract_metadata(
    file_path=data_path,
    pattern=r'^TEMP\s+([0-9.]+)',
)
```

This is explicit and understandable — the user sees exactly what is
extracted and where it goes. Hiding extraction inside `fit_sequential()`
via a `metadata_patterns` dict would be less transparent: the user would
not see the assignment, could not inspect the value before fitting, and
the mapping between regex capture groups and diffrn fields would be
implicit.

**Decision:** metadata extraction is a user-provided **callback**
instead of a hidden dict-based extraction. The user defines a plain
function that receives a file path and returns a dict of diffrn values.
This keeps the extraction visible, testable, and flexible (e.g. the user
can read from file headers, file names, companion JSON, or a database):

```python
def extract_diffrn(file_path: str) -> dict[str, float | str]:
    return {
        'ambient_temperature': ed.extract_metadata(
            file_path=file_path,
            pattern=r'^TEMP\s+([0-9.]+)',
        ),
    }

project.analysis.fit_sequential(
    data_dir='data/',
    max_workers=4,
    extract_diffrn=extract_diffrn,
)
```

If `extract_diffrn` is `None` (the default), the diffrn columns in the
CSV are left empty. The callback is called once per file in the **main
process** after worker results are collected (not inside the worker —
see § 6.2 for why). The returned dict keys must match `diffrn`
descriptor names (e.g. `'ambient_temperature'`, `'ambient_pressure'`).
Unrecognised keys are ignored with a warning.

This approach:

- Keeps extraction logic **visible** in the user's notebook.
- Allows **any** extraction strategy (regex, filename parsing, external
  lookup), not just regex on file content.
- Is easily testable — the user can call `extract_diffrn(path)` outside
  of fitting to verify.
- Follows the existing pattern where users explicitly assign diffrn
  values rather than having the library guess.

---

## 6. Internal Architecture

### 6.1 Preconditions

`fit_sequential()` validates before starting:

- Exactly 1 structure in `project.structures`.
- Exactly 1 experiment in `project.experiments` (the template).
- At least 1 free parameter.
- `project.info.path` is set (project has been saved).
- `data_dir` exists and contains at least 1 data file.

### 6.2 Template snapshot

Before dispatching workers, the method captures a **template snapshot**
— everything a worker needs to recreate the project independently:

```python
@dataclass(frozen=True)
class SequentialFitTemplate:
    structure_cif: str            # structure.as_cif
    experiment_cif: str           # experiment.as_cif (full template)
    initial_params: dict          # {unique_name: value} for ALL free params
    free_param_unique_names: list # unique_names of free params
    alias_defs: list[dict]        # [{label, param_unique_name}, ...]
    constraint_defs: list[str]    # [expression, ...]
    minimizer_tag: str            # e.g. 'lmfit'
    calculator_tag: str           # e.g. 'cryspy'
    diffrn_field_names: list      # ['ambient_temperature', ...]
```

This is a plain, picklable data object (no live references to
`GuardedBase` instances, no callables). Note: uses `unique_name` instead
of random `uid` for parameter identification.

**`extract_diffrn` callback handling:** the user-provided callback is
_not_ stored in the template because arbitrary callables (lambdas,
closures) cannot be pickled reliably for multiprocessing. Instead:

- In **single-worker mode** (`max_workers=1`), the callback is called
  directly in the main process after `_fit_worker()` returns.
- In **multi-worker mode**, the callback is called in the main process
  after collecting results from the worker pool. Since diffrn metadata
  extraction is I/O-bound (reading file headers) and fast, running it in
  the main process is not a bottleneck.

This means `_fit_worker()` does not extract diffrn metadata — it only
fits. The main process calls `extract_diffrn(data_path)` for each file
and merges the returned dict into the result row before writing to CSV.

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

    # Extract diffrn metadata in the main process (avoids pickling callables)
    if extract_diffrn is not None:
        for result in results:
            diffrn_values = extract_diffrn(result['file_path'])
            result.update(diffrn_values)

    _append_to_csv(csv_path, results)

    # Report progress (main process only, between chunks)
    _report_chunk_progress(chunk_idx, total_chunks, results, verbosity)

    # Propagate: use last successful file's params as next starting values
    last_ok = _last_successful(results)
    if last_ok is not None:
        template = replace(template, initial_params=last_ok['params'])
```

The `'spawn'` context is required because:

- `cryspy` is pure Python — the GIL prevents true thread parallelism.
- `fork` can deadlock with C extensions and is unreliable on macOS.
- `spawn` creates a fresh Python interpreter per worker — singletons
  (`UidMapHandler`, `ConstraintsHandler`) are naturally isolated.

**Progress reporting** happens in the main process, between chunks.
Workers always run silently. After each chunk completes, the main
process prints/updates progress:

| Verbosity | Between-chunk output                                                  |
| --------- | --------------------------------------------------------------------- |
| `full`    | Per-chunk table: chunk N/M, per-file χ² and status (updated in place) |
| `short`   | One-line per chunk: `✅ Chunk 3/500: 10 files, avg χ² = 1.45`         |
| `silent`  | No output                                                             |

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

    Creates a fresh Project, loads the template configuration via CIF,
    replaces data from data_path, applies initial parameters, fits,
    and returns a plain dict of results.
    """
    # 1. Create fresh project (isolated singletons, no shared state)
    project = Project(name='_worker')

    # 2. Load structure from template CIF
    project.structures.add_from_cif_str(template.structure_cif)

    # 3. Create experiment from template CIF (full config + template data)
    project.experiments.add_from_cif_str(template.experiment_cif)
    expt = project.experiments[0]

    # 4. Replace data from new data path
    expt._load_ascii_data_to_experiment(data_path)

    # 5. Override parameter values from propagated starting values
    _apply_param_overrides(project, template.initial_params)

    # 6. Set free flags
    _set_free_params(project, template.free_param_unique_names)

    # 7. Apply constraints (using unique_names, not random UIDs)
    _apply_constraints(project, template.alias_defs, template.constraint_defs)

    # 8. Set calculator and minimizer
    expt.calculator_type = template.calculator_tag
    project.analysis.current_minimizer = template.minimizer_tag

    # 9. Fit
    project.analysis.fit(verbosity='silent')

    # 10. Collect results (fit metrics + parameter values, no diffrn metadata)
    return _collect_results(project, data_path)
```

**Note:** diffrn metadata extraction (`extract_diffrn` callback) is not
called in the worker. The main process calls the callback after
collecting worker results and merges the metadata into each result row
before writing to CSV. This avoids pickling issues with callables.

#### Step 3+4: CIF round-trip then data reload (Approach A)

The template experiment's CIF contains the full configuration:
instrument, peak profile, background points, excluded regions, linked
phases, diffrn conditions, and the template's measured data. Loading
from CIF reconstructs all of this. Then
`_load_ascii_data_to_experiment(data_path)` **replaces** the data
category contents (it reassigns `self._items` to a fresh list — verified
in `PdCwlData._create_items_set_xcoord_and_id`).

**Prerequisite: CIF round-trip must be reliable.** The path is:

```
experiment.as_cif → ExperimentFactory.from_cif_str() → expt_obj
```

This calls `_from_gemmi_block` which:

1. Reads `ExperimentType` from CIF → resolves the concrete class.
2. Creates the experiment (with default categories).
3. Calls `category.from_cif(block)` on each category.

**Known risk:** `category_collection_to_cif` truncates output at
`max_display=20` rows for display purposes. If the template experiment's
background or data has >20 items, the CIF will be incomplete. **Fix:**
serialisation used for the template snapshot must pass
`max_display=None` to emit all rows. This is a prerequisite fix (§ 9.2).

### 6.5 Parameter identification by unique_name

All parameter identification in the sequential fitting system uses
`unique_name` (e.g. `cosio.cell.length_a`), not the random `uid`.

- **CSV columns** are keyed by `unique_name`.
- **Template `initial_params`** is `{unique_name: value}`.
- **`free_param_unique_names`** lists which params to mark as free.
- **Alias definitions** reference `param_unique_name` instead of
  `param_uid`.

The `_apply_param_overrides` helper walks all parameters in the project,
matches by `unique_name`, and sets values:

```python
def _apply_param_overrides(
    project: Project,
    overrides: dict[str, float],
) -> None:
    all_params = project.structures.parameters + project.experiments.parameters
    by_name = {p.unique_name: p for p in all_params}
    for name, value in overrides.items():
        if name in by_name:
            by_name[name].value = value
```

### 6.6 Parameter propagation strategy

After each chunk completes:

1. Take the results from the **last successful file** in the chunk (by
   file sort order).
2. Extract all free parameter values.
3. Use these as `initial_params` for all workers in the next chunk.

**Why the last file?** Assuming files are ordered (by time, temperature,
dose), the last file's parameters are the closest extrapolation for the
next chunk. Within a chunk, all workers start from the same values, so
parameter evolution within a chunk comes only from the fit — not from
propagation.

**Edge case — all fits in a chunk failed:** keep the previous chunk's
parameters and log a warning.

**When `max_workers=1`:** the chunk size is 1, so propagation happens
after every file — identical to the current single-fit mode. This
preserves backward compatibility.

### 6.7 CSV output format

The CSV uses a flat header with metadata columns, diffrn columns, and
two columns per free parameter (value + uncertainty):

```csv
file_path,chi_squared,reduced_chi_squared,fit_success,n_iterations,diffrn.ambient_temperature,diffrn.ambient_pressure,cosio.cell.length_a,cosio.cell.length_a.uncertainty,template.instrument.calib_twotheta_offset,template.instrument.calib_twotheta_offset.uncertainty,...
/data/scan_001.xye,142.3,1.23,True,45,300.0,,10.312,0.001,0.29,0.01,...
/data/scan_002.xye,138.1,1.19,True,32,310.0,,10.315,0.002,0.28,0.01,...
```

| Column group                | Description                                |
| --------------------------- | ------------------------------------------ |
| `file_path`                 | Absolute path to the data file             |
| `chi_squared`               | χ² of the fit                              |
| `reduced_chi_squared`       | Reduced χ²                                 |
| `fit_success`               | Whether the minimizer converged            |
| `n_iterations`              | Number of minimizer iterations             |
| `diffrn.*`                  | Diffrn metadata (temperature, pressure, …) |
| `{unique_name}`             | Fitted value of free parameter             |
| `{unique_name}.uncertainty` | Uncertainty of free parameter              |

**Implementation:** use `csv.DictWriter` (stdlib). Header is written
once on file creation. Rows are appended after each chunk and flushed
immediately (no buffered writes that could be lost on crash).

### 6.8 Crash recovery

On entry, `fit_sequential()` checks for an existing CSV at the project's
`analysis/results.csv`:

1. If the file exists and is non-empty:
   - Read all rows.
   - Build a set of already-fitted `file_path` values.
   - Extract parameter values from the last successful row as starting
     values (overrides template's current values).
   - Log a message: `"Resuming from row N (M files already fitted)."`.
2. If the file does not exist or is empty:
   - Create the file with the header row.
   - Use the template's current parameter values as starting values.

The file path comparison uses absolute paths to avoid mismatches.

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

### 7.6 Unified FitModel abstraction

Every experiment already contains a full list of structural parameters
via `linked_phases` (powder) or `linked_crystal` (single crystal). An
experiment + its linked structures together form a complete model for
computing a diffraction pattern. A `FitModel` class could merge
structure and experiment parameters into a single flat parameter set.

**Assessment:** the current code already merges them at fit time
(`structures.free_parameters + experiments.free_parameters`). A
`FitModel` class would formalise this and could simplify the
`_residual_function` signature (one model instead of structures +
experiments + analysis). However, introducing a new abstraction now
would be premature — the current merging works and the sequential
fitting design does not depend on it. If the fitting internals are
refactored later (issue #7), `FitModel` would be a natural outcome.

---

## 8. Resolved Questions

These were open questions in the previous draft; decisions are recorded
here.

1. **`max_workers='auto'`** → uses `os.cpu_count()` (physical CPU
   count), following the `pytest-xdist` convention.

2. **CIF round-trip reliability** → must be verified and fixed as a
   prerequisite. Known risk: `category_collection_to_cif` truncates at
   20 rows — the template snapshot must bypass this. See § 9.2.

3. **`_load_ascii_data_to_experiment()` on existing data** → **verified:
   it replaces, not appends.** `_create_items_set_xcoord_and_id`
   reassigns `self._items` to a fresh list.

4. **Worker verbosity** → workers run silently. Progress is reported by
   the main process between chunks. See § 6.3.

5. **Constraint parameter identification** → switch from random `uid` to
   deterministic `unique_name`. See § 6.5 and § 9.1.

6. **`plot_param_series` unification** → always read from CSV. One
   method, no `_from_csv` variant. See § 5.5.

7. **Metadata in CSV** → include all diffrn fields (temperature,
   pressure, magnetic field, electric field). Extraction is done via a
   user-provided callback (`extract_diffrn`), not hidden inside
   `fit_sequential`. See § 5.7.

8. **CSV output path** → deterministic:
   `project_dir/analysis/results.csv`. No argument needed. See § 5.4.

9. **`data_paths` argument** → replaced with `data_dir` (path to
   directory). Files are discovered via `extract_data_paths_from_dir`.
   For ZIP sources, extract first. See § 5.1.

10. **Project directory structure** → move `analysis.cif` into
    `analysis/` directory. All analysis artifacts (settings + results)
    live under one directory. See § 5.4 and § 9.6.

11. **Singletons (`UidMapHandler`, `ConstraintsHandler`)** →
    `UidMapHandler` eliminated (aliases use direct references +
    `unique_name`). `ConstraintsHandler` stays singleton but is now
    always synced before use. Fixes notebook rerun issues, resolves
    issue #4. See § 9.5.

---

## 9. Prerequisite Changes

These changes are needed before implementing `fit_sequential()` itself.
Each is a separate, atomic change.

### 9.1 Switch alias `param_uid` to `param_unique_name` ✅

**Done.** Went further than planned: eliminated `UidMapHandler` and
random UIDs entirely. Aliases now store a direct object reference to the
parameter (`Alias._param_ref`, runtime) plus `Alias._param_unique_name`
(`StringDescriptor`, CIF serialisation with tag
`_alias.param_unique_name`). `ConstraintsHandler.apply()` uses the
direct reference — no map lookup needed. `_minimizer_uid` returns
`unique_name.replace('.', '__')` instead of a random string. All
tutorials, tests, and call sites updated.

### 9.2 Fix `category_collection_to_cif` truncation ✅

**Done.** `category_collection_to_cif` default changed to
`max_display=None` (emit all rows). Truncation is opt-in via explicit
`max_display` parameter, used only by display methods.

### 9.3 Verify CIF round-trip for experiments ✅

**Done.** Five integration tests in `test_cif_round_trip.py`:

1. Parameter values survive `as_cif` → `from_cif_str`.
2. Free flags survive the round-trip.
3. Category collections (background, excluded regions, linked phases)
   preserve item count.
4. Data points survive (count, first/last values).
5. Structure round-trip with symmetry constraints.

### 9.4 Add `destination` parameter to `extract_data_paths_from_zip` ✅

**Done.** Optional `destination` parameter added. When provided,
extracts to the given directory. When `None`, uses a temporary directory
(original behaviour).

### 9.5 Replace singletons with instance-owned state (partially done)

#### Problem

`UidMapHandler` and `ConstraintsHandler` are process-global singletons
(`SingletonBase`). This causes three concrete problems:

1. **Notebook reruns.** When a user re-executes cells in a Jupyter
   notebook, the old `Project` is garbage-collected but the singleton
   retains all aliases, constraints, and UID entries from the previous
   run. The new `Project` inherits stale state, leading to ghost
   constraints and spurious errors. Users must restart the kernel to get
   a clean state — a common source of confusion.

2. **Sequential fitting workers.** The `spawn` context used for
   `ProcessPoolExecutor` creates fresh interpreters, so singletons are
   naturally isolated per worker. This is why multiprocessing works
   despite the singletons. However, the main process's singleton still
   accumulates state across chunks and calls — not harmful in the
   current design (workers don't touch the main singleton), but fragile
   if the architecture evolves.

3. **Multiple projects.** If a user creates two `Project` instances in
   the same session (e.g. to compare fits), their constraints and UID
   maps collide in the shared singleton.

#### Current status

**`UidMapHandler`: eliminated entirely.** Random UIDs and the global
UID-to-Parameter map have been removed. Aliases store direct object
references at runtime and deterministic `unique_name` strings for CIF
serialisation. This fully resolves problems 1–3 for the UID map.

**`ConstraintsHandler`: stale-state bug fixed, still a singleton.**
`Analysis._update_categories()` now always syncs the handler from the
current `aliases` and `constraints` before calling `apply()`. This
resolves problem 1 (notebook reruns) and problem 2 (worker isolation is
natural with `spawn`). Problem 3 (multiple projects) remains theoretical
— if multi-project support becomes a real need, moving
`ConstraintsHandler` to instance scope is a standalone follow-up.

#### Remaining work (optional)

Move `ConstraintsHandler` from singleton to per-`Analysis` instance.
This only matters for the multiple-projects edge case. The sequential
fitting design does **not** depend on this change.

#### Relationship to issue #4

Issue #4 ("Refresh constraint state before auto-apply") is **fully
resolved.** `_update_categories()` syncs handler state on every call.
Constraints auto-enable on `create()` and are applied before fitting
starts. The manual `apply_constraints()` method has been removed. Fixing
the singleton issue resolves issue #4 as a side effect.

### 9.6 Move `analysis.cif` into `analysis/` directory ✅

**Done.** `Project.save()` writes to `analysis/analysis.cif`.
`Project.load()` checks `analysis/analysis.cif` first, falls back to
`analysis.cif` at root for backward compatibility. Unit tests verify
both layouts.

---

## 10. Implementation Plan

The plan is structured as a sequence of pull requests. Each PR is
independently mergeable and testable. Foundation issues (#7, #4, #1) are
resolved first because they clean up the fitting internals that
`fit_sequential` builds on top of.

### Foundation PRs (resolve existing issues)

#### PR 1 — Eliminate dummy Experiments wrapper in single-fit mode (issue #7) ✅

> **Title:** `Accept single Experiment in Fitter.fit()`
>
> **Description:** Refactor `Fitter.fit()` and `_residual_function()` to
> accept a plain list of `ExperimentBase` objects instead of requiring
> an `Experiments` collection. Remove the dummy `Experiments` wrapper
> and the `object.__setattr__` hack in `Analysis.fit()` single-mode
> loop. Update `_residual_function` to iterate over the list directly.
> Update all callers (single-fit, joint-fit). Update unit and
> integration tests.

**Done.** `Fitter.fit()` and `_residual_function()` now accept
`experiments: list[ExperimentBase]`. `Analysis.fit()` passes
`experiments_list = [experiment]` in single-fit mode and
`list(experiments.values())` in joint-fit mode. No more dummy
`Experiments` wrapper or `object.__setattr__` hack.

#### PR 2 — Replace UID map with direct references and auto-apply constraints (issue #4 + § 9.5) ✅

> **Title:**
> `Replace UID map with direct references and auto-apply constraints`
>
> **Description:** Eliminated `UidMapHandler` and random UID generation
> entirely. Aliases store direct parameter object references at runtime
> and deterministic `unique_name` strings for CIF. Added
> `enable()`/`disable()` on `Constraints` with auto-enable on
> `create()`, replacing the manual `apply_constraints()` call.
> `Analysis._update_categories()` always syncs handler state when
> constraints are enabled. Also fixes issue #4 (stale constraint state)
> and completes PR 4 (alias `param_unique_name`).

**Why second:** removes the global UID map that made constraint
resolution opaque and fragile. The stale-state bug (issue #4) is fully
fixed. `ConstraintsHandler` remains a singleton but is now always in
sync — moving it to instance scope is an optional follow-up for the
multi-project edge case.

This PR also absorbed PR 4 (§ 9.1) since switching from random UIDs to
`unique_name` was a natural part of the same change.

#### PR 3 — Implement Project.load() (issue #1) ✅

> **Title:** `Implement Project.load() from CIF directory`
>
> **Description:** Implement `Project.load(dir_path)` that reads
> `project.cif`, `structures/*.cif`, `experiments/*.cif`, and
> `analysis/analysis.cif` from the project directory and reconstructs
> the full project state. Handle the old layout (`analysis.cif` at root)
> as a fallback. Add integration test: save → load → compare all
> parameter values.

**Done.** `Project.load()` reads CIF files from the project directory,
reconstructs structures, experiments, and analysis. Resolves alias
`param_unique_name` strings back to live `Parameter` references.
Integration tests verify save → load → parameter comparison and save →
load → fit → χ² comparison.

### Sequential-fitting prerequisite PRs

#### PR 4 — Switch alias param_uid to param_unique_name (§ 9.1) ✅

> Absorbed into PR 2. Aliases now use `param_unique_name` with direct
> object references. All tutorials and tests updated.

#### PR 5 — Fix CIF collection truncation (§ 9.2) ✅

> **Title:** `Remove max_display truncation from CIF serialisation`
>
> **Description:** Remove `max_display=20` from
> `category_collection_to_cif`. Add truncation only in display methods
> (`show_as_cif()`). Ensures experiments with many background/data
> points survive CIF round-trips.

**Done.** `category_collection_to_cif` default changed to
`max_display=None` (emit all rows). Truncation is now opt-in, only used
by display methods.

#### PR 6 — Verify CIF round-trip for experiments (§ 9.3) ✅

> **Title:** `Add CIF round-trip integration test for experiments`
>
> **Description:** Write an integration test that creates a fully
> configured experiment (instrument, peak, background, excluded regions,
> linked phases, data), serialises to CIF, reconstructs from CIF, and
> asserts all parameter values match. Fix any parameters that don't
> survive the round-trip.

**Done.** Five integration tests in `test_cif_round_trip.py`: parameter
values, free flags, categories (background/excluded regions/linked
phases), data points, and structure round-trip.

#### PR 7 — Move analysis.cif into analysis/ directory (§ 9.6) ✅

> **Title:** `Move analysis.cif into analysis/ directory`
>
> **Description:** Update `Project.save()` to write `analysis.cif` to
> `project_dir/analysis/analysis.cif`. Update `Project.load()` to read
> from the new path (with fallback to old path). Update docs
> (`architecture.md`, `project.md`), tests, and console output messages.

**Done.** `Project.save()` writes to `analysis/analysis.cif`.
`Project.load()` checks `analysis/analysis.cif` first, falls back to
`analysis.cif` at root for backward compatibility. Unit tests verify
both layouts.

#### PR 8 — Add destination to extract_data_paths_from_zip (§ 9.4) ✅

> **Title:** `Add destination parameter to extract_data_paths_from_zip`
>
> **Description:** Add optional `destination` keyword to
> `extract_data_paths_from_zip`. When provided, extracts to the given
> directory instead of a temp dir. Enables clean two-step workflow:
> extract ZIP → pass directory to `fit_sequential()`.

**Done.** `extract_data_paths_from_zip` accepts `destination` parameter.
When provided, extracts to the given directory. When `None`, uses a
temporary directory (original behaviour).

### Sequential-fitting core PRs

#### PR 9 — Streaming sequential fit (max_workers=1) ✅

> **Title:** `Add fit_sequential() for streaming single-worker fitting`
>
> **Description:** Add `Analysis.fit_sequential(data_dir, ...)` method.
> Implements: `SequentialFitTemplate` dataclass, `_fit_worker()` plain
> function (called directly, no subprocess), CSV writing with
> `csv.DictWriter`, crash recovery (read CSV + resume), parameter
> propagation (last successful → next iteration). Include
> `extract_diffrn` callback support for metadata columns. Unit tests for
> CSV writing, crash recovery, parameter propagation.

**Done.** Full implementation in `analysis/sequential.py`:
`SequentialFitTemplate` dataclass, `_fit_worker()` module-level
function, CSV helpers (`_build_csv_header`, `_write_csv_header`,
`_append_to_csv`, `_read_csv_for_recovery`), `_build_template()`,
chunk-based processing with parameter propagation, `extract_diffrn`
callback support, progress reporting. Five integration tests in
`test_sequential.py`: CSV production, crash recovery, parameter
propagation, diffrn callback, precondition validation.

#### PR 10 — Update plot_param_series to read from CSV ✅

> **Title:** `Unify plot_param_series to always read from CSV`
>
> **Description:** Refactor `plot_param_series()` to read from
> `project_dir/analysis/results.csv` instead of in-memory
> `_parameter_snapshots`. Works for both `fit_sequential()` (Phase 1+)
> and existing `fit()` single-mode (Phase 4). Remove the old
> `_parameter_snapshots` dict.

**Implemented:** `Plotter.plot_param_series()` reads CSV via pandas.
`Plotter.plot_param_series_from_snapshots()` preserves backward
compatibility for `fit()` single-mode (no CSV yet). `Project.plot_param_series()`
tries CSV first, falls back to snapshots. Axis labels derived from live
descriptor objects.

#### PR 11 — Parallel fitting (max_workers > 1)             ← next

> **Title:** `Add multiprocessing support to fit_sequential`
>
> **Description:** Refactor `_fit_worker()` to be module-level
> picklable. Add `ProcessPoolExecutor` dispatch with `spawn` context.
> Handle worker failures (catch exceptions, mark as failed in CSV). Add
> `max_workers='auto'` support (`os.cpu_count()`). Integration test:
> parallel sequential fit (10 files, 2 workers).

### Post-sequential PRs

#### PR 12 — Dataset replay from CSV

> **Title:** `Add apply_params_from_csv() for dataset replay`
>
> **Description:** Add `Project.apply_params_from_csv(row_index)` that
> loads a CSV row, overrides parameter values in the live project, and
> reloads data from the file path in that row. Enables
> `plot_meas_vs_calc()` for any previously fitted dataset.

#### PR 13 — CSV output for existing single-fit mode

> **Title:** `Write results.csv from existing single-fit mode`
>
> **Description:** Update the existing `Analysis.fit()` single-mode loop
> to write results to `analysis/results.csv` (same CSV format as
> `fit_sequential`). This gives `ed-17.py`-style workflows persistent
> CSV output and unified `plot_param_series()`.

#### PR 14 (optional) — Parallel single-fit for pre-loaded experiments

> **Title:**
> `Add max_workers to Analysis.fit() for pre-loaded experiments`
>
> **Description:** Add `max_workers` parameter to `Analysis.fit()`. When
> `fit_mode == 'single'` and `max_workers > 1`, serialise pre-loaded
> experiments and dispatch to the same worker pool used by
> `fit_sequential`. Reuses the same `_fit_worker` and
> `SequentialFitTemplate` infrastructure.

### Dependency graph

```
PR 1 (issue #7: eliminate dummy Experiments) ✅
  └─► PR 2 (issue #4: UID map + constraints) ✅
        └─► PR 3 (issue #1: Project.load) ✅
              └─► PR 5 (CIF truncation) ✅
                    └─► PR 6 (CIF round-trip test) ✅
                          ├─► PR 7 (analysis.cif → analysis/) ✅
                          │     └─► PR 9 (streaming sequential fit) ✅
                          │           ├─► PR 10 (plot from CSV) ✅
                          │           │     └─► PR 13 (CSV for existing fit)
                          │           └─► PR 11 (parallel fitting)       ← next
                          │                 └─► PR 14 (optional: parallel fit())
                          └─► PR 8 (zip destination) ✅
                                └─► PR 12 (dataset replay)
```

Note: PR 4 was absorbed into PR 2. PRs 5–8 are largely independent of
each other and can be parallelised or reordered as long as PRs 1–3 are
done first and PRs 5–6 are done before PR 9.

---

## 11. Dependencies and Risks

### New dependencies

**None.** `concurrent.futures`, `csv`, `multiprocessing`, `dataclasses`
are all stdlib.

### Risks

| Risk                                             | Mitigation                                                  |
| ------------------------------------------------ | ----------------------------------------------------------- |
| CIF round-trip loses information                 | ✅ PR 3 (load) + PR 6 (round-trip test) verified            |
| CIF collection truncation at 20 rows             | ✅ PR 5 fixed (default `max_display=None`)                  |
| Worker memory leak (large N, long-running pool)  | Use `max_tasks_per_child=100` on the pool (PR 11)           |
| Pickling failures for SequentialFitTemplate      | ✅ Keep it a plain dataclass with only str/dict/list fields |
| crysfml Fortran global state in forked processes | Enforced `spawn` context avoids fork issues (PR 11)         |

### Resolved open issues (now prerequisites) — all done ✅

- **Issue #7 (dummy Experiments wrapper):** resolved in PR 1.
  `Fitter.fit()` and `_residual_function()` accept
  `list[ExperimentBase]`. The worker uses the clean
  `Fitter.fit(structures, [experiment])` API.
- **Issue #4 (constraint refresh) + § 9.1 (alias unique_name) + § 9.5
  (singletons):** resolved in PR 2. `UidMapHandler` eliminated; aliases
  use direct object references and deterministic `unique_name` for CIF;
  `_update_categories()` always syncs handler state; constraints
  auto-enable on `create()`. `ConstraintsHandler` remains a singleton
  but is always in sync — multi-project isolation is an optional
  follow-up.
- **Issue #1 (Project.load):** resolved in PR 3. `Project.load()` reads
  CIF files, reconstructs full project state, resolves alias
  `param_unique_name` strings back to `Parameter` objects via
  `_resolve_alias_references()`. Dataset replay (PR 12) uses `load()`
  directly.

---

## 12. Summary

| Aspect              | Decision                                                                           | Status |
| ------------------- | ---------------------------------------------------------------------------------- | ------ |
| Parallelism backend | `concurrent.futures.ProcessPoolExecutor` with `spawn`                              | PR 11  |
| Worker isolation    | Each worker creates a fresh `Project` — no shared state                            | ✅     |
| Data source         | `data_dir` argument; ZIP → extract first                                           | ✅     |
| Data flow           | Template CIF + data path → worker → result dict → CSV                              | ✅     |
| Parameter IDs       | `unique_name` (deterministic), not `uid` (random)                                  | ✅     |
| Parameter seeding   | Last successful result in chunk → next chunk                                       | ✅     |
| CSV location        | `project_dir/analysis/results.csv` (deterministic)                                 | ✅     |
| CSV contents        | Fit metrics + diffrn metadata + all free param values/uncert                       | ✅     |
| Metadata extraction | User-provided `extract_diffrn` callback, not hidden in lib                         | ✅     |
| Crash recovery      | Read existing CSV, skip fitted files, resume                                       | ✅     |
| Plotting            | Unified `plot_param_series()` always reads from CSV                                | ✅     |
| Configuration       | `max_workers` + `data_dir` on `fit_sequential()`                                   | ✅     |
| Project layout      | `analysis.cif` moves into `analysis/` directory                                    | ✅     |
| Singletons          | `UidMapHandler` eliminated; `ConstraintsHandler` stays singleton but always synced | ✅     |
| New dependencies    | None (stdlib only)                                                                 | ✅     |
| First step          | PRs 1–10 done; PRs 11–14 remaining                                                 | ✅     |
