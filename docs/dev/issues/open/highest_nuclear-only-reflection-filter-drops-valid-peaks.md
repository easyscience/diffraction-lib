# 180. Nuclear-Only Reflection Filter Drops Valid Peaks (Breaks HS HRPT)

**Priority:** `[priority] highest`

**Type:** Correctness / External backend

The powder calculator unconditionally sets `flag_only_nuclear = True` on
every crystal before calling cryspy
([`src/easydiffraction/analysis/calculators/cryspy.py`](../../../../src/easydiffraction/analysis/calculators/cryspy.py),
in `_calculate_powder_pattern_from_dict`). In cryspy 0.12.1 this flag
activates the reflection-extinction filter added in cryspy
[PR #48](https://github.com/ikibalin/cryspy/pull/48)
(`calc_extinction_rule_by_symmetry_elements` in
`A_functions_base/structure_factor.py`). That filter is over-aggressive:
it marks a reflection extinct if it is invariant under _any single_
symmetry operation carrying a non-integer phase
(`extinct |= invariant & non_integer_phase`), instead of summing the
phase contributions over _all_ invariant operations and checking whether
they actually cancel. For symmetric space groups (e.g. `R -3 m`,
hexagonal setting) it removes reflections that have a **non-zero**
nuclear structure factor — real Bragg peaks disappear from the
calculated pattern. cryspy PR #48 itself notes this over-filtering for
screw-axis groups and claims a grouped-sum fix, but the shipped 0.12.1
still uses the broken per-operation `OR`.

**Example of broken behaviour** — the HS/HRPT tutorial
([`docs/docs/tutorials/refine-hs-hrpt`](../../../docs/tutorials/refine-hs-hrpt.py),
herbertsmithite ZnCu₃(OD)₆Cl₂, space group `R -3 m`). The calculated
pattern is missing peaks the data clearly shows (e.g. around 2θ ≈
98.3°). The four-stage refinement then compensates with over-broad
peaks, a wrong scale, and an unphysical **negative** Zn ADP, stalling at
a poor fit. Disabling the cryspy filter restores the peaks and the fit:

| Four-stage fit                          | Reduced χ² | Zn `adp_iso` |
| --------------------------------------- | ---------- | ------------ |
| As shipped (`flag_only_nuclear = True`) | **18.98**  | **−1.43**    |
| Filter disabled (`= False`)             | **1.93**   | **+0.16**    |

(Reproduced with the tutorial's own inputs; neutralising
`calc_extinction_rule_by_symmetry_elements` to return all-`False` is
enough to recover χ² ≈ 1.9 with all-positive ADPs.) The 0.18.0 release
rendered this tutorial correctly because its cryspy predated PR #48.

**Fix:** stop force-enabling the filter in the powder path — set
`flag_only_nuclear = False` in `_calculate_powder_pattern_from_dict`,
matching the sibling `calculate_structure_factors`, which already sets
it `False` with the in-code comment _"= True fails for hs-hrpt example
with R -3 m"_. The flag only controls reflection-list filtering (not
magnetic computation), and genuine lattice-centering absences are still
removed by the separate `calc_pr3` check, so disabling it is safe and
only adds back zero-cost reflections. Also report the over-filtering
upstream to cryspy, since the root bug is in their PR #48; re-enable the
flag only once a cryspy release filters correctly.

**Visible on:** the HS/HRPT tutorial page (`refine-hs-hrpt`); affects
any powder refinement whose space group triggers the cryspy over-filter.

**Depends on:** an upstream cryspy fix for a correct
(non-over-filtering) `flag_only_nuclear` implementation, if the
pre-filter is ever to be re-enabled.

**Recommended-priority note:** silent correctness failure — refinements
of symmetric space groups drop real peaks and converge to wrong
parameters (negative ADPs) with no error. Known one-line mitigation.
**Tier 1 (do first).**
