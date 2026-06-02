# Review 16: Automatic Wyckoff Position Detection

**No findings. Ready to commit.**

The review-15 compatibility finding is addressed: explicit letters remain
respected and reload verbatim, while the only called-out constraint change
is the intentional nearest-representative fix for coordinates that were
previously snapped through the first table representative.

Checks skipped per `AGENTS.md` review-shortcut rules: static ADR/source
review only; no tests, `pixi run fix`, `pixi run check`, or other
verification commands were run.
