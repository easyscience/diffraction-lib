# 16. Add Serial Pattern-Generation Benchmarks

**Priority:** `[priority] low`

**Type:** Performance

The dev environment previously installed `pytest-benchmark`, but the
repository does not currently define any benchmark tests. At the same
time, the integration, script, and notebook pytest tasks all run with
`pytest-xdist`, so benchmark plugins only add warning noise and do not
provide reliable performance regression coverage.

Performance regressions are still worth tracking, especially for single
diffraction-pattern calculation where backend or profile changes can
quietly slow interactive workflows.

**Fix:** add a dedicated serial benchmark task outside the normal
parallel pytest suite. Benchmark representative single-pattern
calculations on fixed datasets and calculators, run without `-n auto`,
and define regression thresholds only after measurements are stable on a
controlled runner.

**Depends on:** nothing.
