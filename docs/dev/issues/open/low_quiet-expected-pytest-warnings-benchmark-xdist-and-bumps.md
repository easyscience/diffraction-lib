# 189. Quiet Expected pytest Warnings (benchmark/xdist and BUMPS)

**Priority:** `[priority] low`

**Type:** Test hygiene / CI noise

Two recurring, expected warnings clutter the integration-test output but
are not defects:

- **`PytestBenchmarkWarning: Benchmarks are automatically disabled because xdist plugin is active`**
  — `integration-tests` runs with `-n auto` (`pixi.toml:108`), and
  `pytest-benchmark` is installed, so the plugin warns on every worker
  that benchmarking is disabled. There are **no benchmarks under
  `tests/integration/`**, so this is pure noise from loading the plugin
  during a parallel run (benchmarks are a separate nightly concern).
- **`bumps/fitproblem.py: UserWarning: Need more data points (currently: N) than fitting parameters (N)`**
  — emitted by intentionally minimal plumbing fixtures in
  `tests/integration/fitting/test_bumps_dream_support.py` (`n_points=2`,
  and `n_points=0` for the mapper-pickle test) and the DREAM resume
  tests. The under-determined problem is deliberate (these tests
  exercise mapper/pickle/resume, not a real fit), so the warning is
  expected.

Neither indicates a bug; both just make CI logs noisier and can mask new
warnings.

**Fix:** quiet the two expected warnings at their source — e.g. disable
the `pytest-benchmark` plugin for the parallel `integration-tests` run
(`-p no:benchmark`), and add scoped `filterwarnings` entries (or
`pytest.warns`/`recwarn` assertions) for the BUMPS under-determined
warning in the specific plumbing tests — so the suite stays quiet and
any new warning stands out.

**Depends on:** nothing.
