# 150. Bragg Powder ASCII Loader Returns Zero Points Instead of Raising

**Priority:** `[priority] medium`

**Type:** Robustness

When a data file has fewer than two columns, the Bragg powder loader
calls `log.error(..., exc_type=ValueError); return 0`. If the Logger is
in WARN reaction mode (it can be, per the `AGENTS.md` leaked-mode note),
this silently returns a zero-point experiment instead of raising —
whereas the total-scattering loader unconditionally `raise ValueError`.
Boundary input (a bad file) should fail consistently and loudly across
families.

**Fix:** make the Bragg loader raise directly, like the total_pd loader.

**TODOs / locations:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/item/bragg_pd.py#L138)
- [total_pd.py](src/easydiffraction/datablocks/experiment/item/total_pd.py#L85)
  — the consistent (raising) reference

**Depends on:** related to issue 66 (`log.error` vs `raise` strategy).

**Audit note (2026-06-23):** the same loader has a second boundary bug.
`io/ascii.py:270` returns `np.loadtxt(...)`, which is **1-D** for a
single-row file, so the caller's `data.shape[1]` (`bragg_pd.py:141`)
raises an opaque `IndexError: tuple index out of range` instead of the
clear "needs ≥2 columns" message. Fix both together — normalise with
`np.atleast_2d(...)` in the loader, and raise (not `return 0`) on
too-few columns.
