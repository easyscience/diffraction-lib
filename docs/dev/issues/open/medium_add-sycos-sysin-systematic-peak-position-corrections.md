# 131. Add SyCos/SySin Systematic Peak-Position Corrections

**Priority:** `[priority] medium`

**Type:** Feature / Experiment model

FullProf models systematic peak-position aberrations with `SyCos`
(sample displacement) and `SySin` (transparency), shifting peaks as a
function of angle on top of the `Zero` offset. EasyDiffraction has no
category for these, so it cannot reproduce datasets that use them. The
cryspy side is implemented in
[cryspy PR #46](https://github.com/ikibalin/cryspy/pull/46) (see
[issue #38](https://github.com/ikibalin/cryspy/issues/38)); the
EasyDiffraction side — an instrument-category parameter pair plus the
calculator wiring — is still to do.

A prepared verification page,
`docs/docs/verification/pd-neut-cwl_lab6_sycos-sysin.py`, uses the issue
#38 LaB6 dataset and is marked `known_discrepancy=True`. Finishing it
also needs a custom ¹¹B scattering length, the Thompson–Cox–Hastings
profile, and a FullProf-style polynomial background, which that dataset
relies on.

**Fix:** add `SyCos`/`SySin` to the CWL instrument category, pass them
to the calculators, then re-gate the LaB6 page.

**Depends on:** nothing.
