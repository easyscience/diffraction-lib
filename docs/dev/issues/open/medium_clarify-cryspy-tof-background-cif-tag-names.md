# 21. Clarify CrysPy TOF Background CIF Tag Names

**Priority:** `[priority] medium`

**Type:** Correctness / Naming

The CrysPy calculator uses TOF background CIF tags
(`_tof_backgroundpoint_time`, `_tof_backgroundpoint_intensity`) and
hardcoded `0.0` intensity values marked with `TODO: !!!!????`. The
mapping and the hardcoded defaults need verification.

**TODOs:**

- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L734)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L735)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L738)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L739)

**Depends on:** nothing.

**Audit note (2026-06-23):** `_cif_background_section`
(`cryspy.py:1718-1725`) writes, for both CWL and TOF, two background
points at `twotheta_min`/`twotheta_max` with hardcoded `0.0` intensity;
for TOF the tag is `_tof_backgroundpoint_time` but the values are 2θ, not
TOF times. This is **not** a wrong-science risk: the user's real
background is added at the model layer — `data/bragg_pd.py:578` writes
`calc + self.intensity_bkg` — so this dummy CIF section is dead/cosmetic.
Fix = remove it (or populate it correctly, with TOF times for TOF) and
drop the mislabeled tags.
