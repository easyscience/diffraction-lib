# 113. Cross-Repository Validation Harness (nightly)

**Priority:** `[priority] medium`

**Type:** Test infrastructure

Deferred cross-repository work for the
[Test Suite and Validation Strategy](../../adrs/accepted/test-suite-and-validation.md)
ADR (§7, §8). The harness code lives in `diffraction-lib`; the corpus,
results database, and benchmark/reference history live in the
`diffraction` data repository, fetched at runtime and written back by a
nightly job that installs easydiffraction from PyPI (acceptance-style).

**Items:**

- **COD corpus check.** Download ~100–200 CIF files from the
  Crystallography Open Database, load each, and record per-file status
  (`ok` / `partial` + missing fields / `fail`) in a git-diffable CSV
  keyed and ordered by COD id. Add a `--recheck-failed` flag to re-run
  only the failed/partial entries after fixes (instead of new random
  files). Extend with per-engine calculation results on the corpus.
- **Generative fuzzing.** Randomly generate ~100–200 structures (random
  space group, cell, 1–10 atoms with random coordinates/ADP/occupancy),
  compute patterns across engines, and record disagreements in the same
  database.
- **Benchmark history + gate.** Commit `pytest-benchmark` baseline JSON
  to the data repository and add a regression threshold once timing
  variance is characterised on a controlled runner. (The serial
  benchmark task itself now exists — see issue 16 — this is the
  history/gating remainder.)
- **External-software comparison.** Add FullProf (then GSAS-II/TOPAS)
  pre-calculated profiles as zipped projects in the data repository so
  the Verification pages can overlay them against easydiffraction.

**Depends on:** the `diffraction` data repository; cross-repo
coordination.
