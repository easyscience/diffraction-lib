# 171. Add External References for Missing TOF Profile Verification

**Priority:** `[priority] medium`

## Problem

The verification notebook audit found that every supported constant-
wavelength Bragg peak profile has at least one verification page, but
two supported time-of-flight peak profiles do not yet have meaningful
external-reference notebooks:

- `tof-pseudo-voigt`
- `tof-double-jorgensen-von-dreele`

The current bundled FullProf reference set covers TOF Jorgensen and TOF
Jorgensen-Von Dreele examples, but does not include references for these
two profiles. The double-Jorgensen-Von Dreele profile maps to the
CrysPy/Z-Rietveld `type0m` shape, so a FullProf reference may not be the
right source.

## Desired Outcome

Add one verification notebook for each missing TOF profile using the
simplest structure and experiment that isolates that profile choice.
Each notebook should compare EasyDiffraction with an external reference
calculation, or explicitly document why no suitable external reference
program exists and what substitute reference is being used.

## Notes

Do not add self-comparisons that only compare EasyDiffraction with
itself. The verification pages should either use a real external
reference or stay absent until a useful reference can be generated.
