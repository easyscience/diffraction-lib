# 162. Untrack Generated Tutorial-Benchmark CSVs

**Priority:** `[priority] medium`

**Type:** Hygiene

Six `*_tutorial-benchmarks.csv` files are tracked under
`docs/dev/benchmarking/`, but `AGENTS.md` (§Workflow) states these are
"generated verification artifacts, not source changes" that should be
left untracked. They are machine/date/Python-specific snapshots that
accrue indefinitely and create noisy diffs.

**Fix:** `git rm --cached` the generated CSVs and add
`docs/dev/benchmarking/*.csv` to `.gitignore`, or document an explicit
exception if a curated benchmark history is intentional.

**Depends on:** related to issues 16, 113 (benchmark history/gating).
