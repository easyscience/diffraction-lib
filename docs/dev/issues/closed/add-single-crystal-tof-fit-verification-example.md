# 190. Add a Single-Crystal TOF Fit Verification Example

**Closed:** added the single-crystal time-of-flight verification example
`docs/docs/verification/sc-neut-tof_taurine_basic.py` (and generated
`.ipynb`), built from a FullProf reference for Taurine (P 2₁/c, neutron
TOF single-crystal data, SENJU @ J-PARC).

The FullProf model has extinction set to zero (Ext1 = 0, unrefined) so
the comparison focuses on the structure-factor physics shared by cryspy
and FullProf. After refining the overall scale only, edi-cryspy matches
the FullProf F²cal to ~0.01% (profile diff and max deviation), with area
ratio 1.0000 and shape correlation 1.0000.

Reference files live in
`docs/docs/verification/fullprof/sc-neut-tof_taurine_basic/`; the
example is listed under the **Single Crystal** section of
`docs/docs/verification/index.md` and linked from the features page
(§2.2 single-crystal Time-of-Flight row).
