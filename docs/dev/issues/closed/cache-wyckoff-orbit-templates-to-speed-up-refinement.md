# 172. Cache Wyckoff Orbit Templates to Speed Up Refinement

Closed by caching the resolved Wyckoff orbit-representative template per
atom and reusing it on minimizer iterations.

Previously every fit iteration re-resolved each atom's orbit through
`crystallography.wyckoff_position_info` → `_nearest_orbit_template` →
`_orbit_template_residual`, which runs `numpy.linalg.lstsq` over all 27
integer lattice shifts for every candidate template, for every atom —
even though the Wyckoff letter and space group are fixed during a fit.
Profiling put this at ~45 % of a minimizer iteration.

`AtomSite` now stores `_wyckoff_template_cache`, populated whenever
detection runs. In `_detect_and_snap_atom`, when `called_by_minimizer`
is true and a cached template exists, the atom is snapped directly from
the cached template (the cheap single-axis `snap_to_wyckoff_template`
projection), skipping the per-template `lstsq` orbit search. The cache
is refreshed on re-detection and cleared when a site resolves to no
template, so non-minimizer edits (coordinate or space-group changes)
still re-detect correctly.

Validated: the cached fast path produces bit-identical snapped
coordinates, constraint flags, multiplicity, and calculated pattern as
the full path (max difference 0.0), and the per-iteration structure
update is ~2.3× faster (≈117 ms → ≈52 ms on the NCAF case). Regression
tests in
`tests/unit/easydiffraction/datablocks/structure/categories/test_atom_sites.py`
(`TestAtomSiteWyckoffTemplateCache`) cover cache population,
fast-vs-full snap equivalence, and cache refresh on re-detection. The
FullProf verification suite (including special-position structures LBCO,
Y2O3, and the Pr2NiO4 single crystal) is unchanged.

Independent of the peak-profile cutoff work
([`peak-profile-cutoff` ADR](../../adrs/accepted/peak-profile-cutoff.md)),
which speeds the backend profile rather than the symmetry snap.
