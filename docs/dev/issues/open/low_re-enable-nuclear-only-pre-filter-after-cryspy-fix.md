# 180. Re-enable `flag_only_nuclear` Pre-Filter After Upstream cryspy Fix

**Priority:** `[priority] low`

**Type:** Correctness / External backend (upstream tracking +
performance)

**Status:** The user-facing correctness symptom is **already mitigated**
in EasyDiffraction. Both the powder path and the structure-factor path
set `flag_only_nuclear = False`
([`cryspy.py:295`](../../../../src/easydiffraction/analysis/calculators/cryspy.py)
and `:187`), so the over-aggressive cryspy reflection-extinction filter
is no longer triggered and real Bragg peaks are no longer dropped.
HS/HRPT refines correctly again (reduced χ² ≈ 1.9 with all-positive
ADPs, vs χ² ≈ 19 and a negative Zn ADP when the filter was active). This
issue now tracks only the upstream bug and the eventual re-enable.

## Background (resolved locally)

The powder calculator used to unconditionally set
`flag_only_nuclear = True` before calling cryspy. In cryspy 0.12.1 this
activates the reflection-extinction filter from cryspy
[PR #48](https://github.com/ikibalin/cryspy/pull/48)
(`calc_extinction_rule_by_symmetry_elements` in
`A_functions_base/structure_factor.py`). That filter is over-aggressive:
it marks a reflection extinct if it is invariant under _any single_
symmetry operation carrying a non-integer phase
(`extinct |= invariant & non_integer_phase`), instead of summing the
phase contributions over _all_ invariant operations and checking whether
they actually cancel. For symmetric space groups (e.g. `R -3 m`,
hexagonal setting — the HS/HRPT herbertsmithite tutorial) it removed
reflections with a non-zero nuclear structure factor, so real Bragg
peaks (e.g. 2θ ≈ 98.3°) disappeared and the refinement compensated with
a wrong scale and an unphysical negative Zn ADP.

The local mitigation (set `flag_only_nuclear = False`) matches the
sibling `calculate_structure_factors`, which already carried the in-code
comment _"= True fails for hs-hrpt example with R -3 m"_. The flag only
controls reflection-list filtering (not magnetic computation), and
genuine lattice-centering absences are still removed by the separate
`calc_pr3` check, so disabling it is safe and only adds back zero-cost
reflections.

## Remaining work

- **Report the over-filtering upstream to cryspy.** The root bug is in
  cryspy PR #48; the shipped 0.12.1 still uses the broken per-operation
  `OR` rather than the grouped-sum cancellation that PR #48 itself
  describes.
- **Re-enable the pre-filter once cryspy filters correctly.** Restoring
  `flag_only_nuclear = True` is a performance optimization — it lets
  cryspy skip computing reflections that are then discarded — so it is
  worth doing only after a cryspy release filters correctly. Until then
  the `False` setting is the correct behaviour.

**Depends on:** an upstream cryspy fix for a correct
(non-over-filtering) `flag_only_nuclear` implementation.

**Priority note:** downgraded from `highest` to `low` on 2026-06-23 —
the silent-wrong-science symptom is fixed locally (see Status); what
remains is upstream tracking plus an optional performance re-enable,
neither urgent.
