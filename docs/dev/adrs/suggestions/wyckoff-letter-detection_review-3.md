# Review 3: Automatic Wyckoff Position Detection

**No findings. Ready to commit.**

The review-2 findings were addressed: the auto/provided marker is now
distinct from the stored detected value, and project CIF writes now have
a concrete columnar rule for mixed auto/explicit atom-site loops.

Checks skipped per `AGENTS.md` review-shortcut rules: static ADR/source
review only; no tests, `pixi run fix`, `pixi run check`, or other
verification commands were run.
