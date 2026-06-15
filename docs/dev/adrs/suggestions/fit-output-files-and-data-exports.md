# ADR: Fit Output Files and Data Exports

**Status:** Proposed **Date:** 2026-05-18

## Status Note

The current branch already adopts two pieces of this naming scheme:

- sequential deterministic results stay in `analysis/results.csv`
- Bayesian arrays and plot caches use `analysis/mcmc.h5`

Those decisions now live in
[Analysis CIF Fit State](../accepted/analysis-cif-fit-state.md). This
proposal is therefore narrowed to the still-open roles for
`analysis/data.h5`, `analysis/exports/`, and any extra deterministic
convenience exports.

## Context

Different fit modes still produce different kinds of reusable output:

- sequential deterministic fits produce a rectangular parameter
  evolution table, already saved as `analysis/results.csv`
- Bayesian fits produce posterior samples, diagnostics, predictive
  arrays, and plot caches, which are too large and structured for CIF or
  CSV
- deterministic single and joint fits produce fitted model state,
  calculated data, reflection tables, residuals, and optional
  covariance/correlation summaries

The accepted fit-state ADR already standardizes the canonical saved fit
projection in `analysis/analysis.cif` plus `analysis/mcmc.h5` for
Bayesian sidecars. What remains open here is whether project save should
also produce optional archives or user-facing export files beyond that
accepted baseline.

The project should keep naming consistent and avoid making users extract
ordinary plotting data from CIF when a clearer CSV export is possible.
At the same time, CIF remains the canonical model/configuration format,
and large numerical arrays should not be embedded in
`analysis/analysis.cif`.

## Decision

### 1. Keep the implemented results baseline

The accepted baseline is:

- `analysis/results.csv` for sequential deterministic fit tables
- `analysis/mcmc.h5` for large Bayesian arrays and result-derived caches

Any future change to those canonical filenames would need a follow-up
ADR.

### 2. Reserve separate roles for archives and exports

If extra persisted files are added under `analysis/`, keep their roles
separate:

- `analysis/data.h5` for optional archived input or measured data.
- `analysis/exports/` for optional user-facing CSV files intended for
  external plotting and inspection.

The fit type and saved fit-state manifests stay recorded in
`analysis/analysis.cif`, principally through `_fit_result.result_kind`
and the related fit-state categories.

### 3. Sequential deterministic results stay CSV

Sequential deterministic fitting should keep `analysis/results.csv` as
the canonical table for parameter evolution and extracted metadata.

This file is intentionally CSV because:

- each row naturally corresponds to one sequential fit step
- users often inspect, filter, and plot it outside EasyDiffraction
- it should remain easy to diff, copy, and load in spreadsheets

Sequential measured input data may optionally be archived in
`analysis/data.h5`, but that archive is data, not results. It must not
replace `analysis/results.csv`.

### 4. Bayesian arrays use `analysis/mcmc.h5`

Single Bayesian fits should store posterior samples, log posterior
arrays, predictive arrays, and prepared plot caches in
`analysis/mcmc.h5`.

The previous candidate name `analysis/bayesian_data.h5` remains rejected
because it mixes fit type with file role and blurs result arrays with
input data. Bayesian-specific meaning belongs in the CIF manifest and
HDF5 groups, not the sidecar filename.

### 5. Deterministic single and joint fits may gain CSV exports

For single, joint, and sequential deterministic fits, EasyDiffraction
should consider optional CSV exports for ordinary plotting data:

- measured data
- calculated data
- residuals
- reflection tables / `refln` categories

These exports are not canonical persistence. They are convenience files
for users who want to plot or analyze results in external software
without parsing CIF.

Suggested first layout:

```text
analysis/
  analysis.cif
  results.csv        # sequential deterministic only, when applicable
  mcmc.h5         # Bayesian and other structured result arrays
  data.h5            # optional archived measured/input data
  exports/
    <experiment>_measured.csv
    <experiment>_calculated.csv
    <experiment>_residual.csv
    <experiment>_reflections.csv
```

## Fit-Type Mapping

| Fit type                 | Canonical fit state                              | Tabular results              | Large arrays / caches | Optional data archive | Optional exports                |
| ------------------------ | ------------------------------------------------ | ---------------------------- | --------------------- | --------------------- | ------------------------------- |
| single deterministic     | `analysis/analysis.cif`                          | open question                | none initially        | none initially        | `analysis/exports/*.csv`        |
| joint deterministic      | `analysis/analysis.cif`                          | open question                | none initially        | none initially        | `analysis/exports/*.csv`        |
| sequential deterministic | `analysis/analysis.cif` + `analysis/results.csv` | `analysis/results.csv`       | none initially        | `analysis/data.h5`    | `analysis/exports/*.csv`        |
| single Bayesian          | `analysis/analysis.cif` + `analysis/mcmc.h5`     | optional summary export only | `analysis/mcmc.h5`    | none initially        | optional summary/predictive CSV |

## Open Questions

- Should single and joint deterministic fits write a one-row
  `analysis/results.csv`, or is their result projection in
  `analysis/analysis.cif` enough?
- Should CSV exports be written automatically after fit/save, or only by
  an explicit export command?
- What exact CSV column schemas should be used for measured, calculated,
  residual, and reflection exports?
- Should exported `refln` CSVs mirror CIF tag names exactly, or use
  shorter user-facing column names?
- Should sequential measured data archival in `analysis/data.h5` be
  opt-in, automatic below a size threshold, or always disabled unless
  requested?
- What size threshold and compression policy should control the optional
  `analysis/data.h5`, and does `analysis/mcmc.h5` need a matching
  convention?
- Should external CSV exports be regenerated from canonical CIF/HDF5 on
  demand rather than stored persistently?

## Consequences

### Positive

- Fit output filenames become role-based and consistent across fit
  types.
- Sequential parameter evolution keeps its simple CSV workflow.
- Bayesian arrays get a generic result sidecar name that can also serve
  future structured result types.
- External plotting data can be exposed as plain CSV without weakening
  CIF as the canonical model format.

### Trade-offs

- The project gains more output-file roles under `analysis/`, so save
  and cleanup behavior must be explicit.
- Export CSVs are derived data and must be invalidated or regenerated
  when the project changes.
- HDF5 archives introduce size and compression choices that should be
  resolved before implementation.
