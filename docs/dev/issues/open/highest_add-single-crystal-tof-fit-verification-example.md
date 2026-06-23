# 190. Add a Single-Crystal TOF Fit Verification Example

**Priority:** `[priority] highest`

**Type:** Verification / Correctness

There is no verification example for **single-crystal time-of-flight
(TOF) fitting**. The features page advertises single-crystal TOF support
(`docs/docs/features/index.md`, §2.2 → Instrument — Time-of-Flight:
`cryspy` individual wavelength per reflection), but no
`docs/docs/verification/` page cross-checks a single-crystal TOF
calculation/fit against an independent reference. Every other shipped
calculation path has (or is getting) a verification example; this one is
a gap, so a regression or a wrong result on the single-crystal TOF path
would go unnoticed.

**Fix:** add a single-crystal TOF verification example following the
[`verification-example-lifecycle`](../../adrs/accepted/verification-example-lifecycle.md)
conventions — a `*.py` source under `docs/docs/verification/` (with its
generated `*.ipynb`), an independent reference (e.g. a FullProf
`fullprof/<example>/` dataset), and a `verify.assert_patterns_agree`
check. List it in `docs/docs/verification/index.md` and link it from the
relevant features-page row.

**Depends on:** nothing.
