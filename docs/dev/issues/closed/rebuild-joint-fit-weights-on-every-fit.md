# 3. Rebuild Joint-Fit Weights on Every Fit

Closed: `Analysis._prepare_joint_fit()` (`analysis.py:1547`) now runs at
the start of every joint fit via `_run_fit_mode` (`analysis.py:1429`).
It validates `joint_fit` against the project experiments — raising
`ValueError` if a row references an experiment absent from the project
(removed/renamed), auto-creating rows for new experiments, and
re-asserting every experiment has a row — so stale weights can no longer
reach the minimiser. (Validating weight _values_ — negatives / all-zero
— remains tracked separately by issue #15.)
