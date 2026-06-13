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
