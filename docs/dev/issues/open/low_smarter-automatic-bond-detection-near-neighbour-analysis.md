# 108. Smarter Automatic Bond Detection (Near-Neighbour Analysis)

**Priority:** `[priority] low`

**Type:** UX / Visualization

crysview generates bonds with the cif_core distance rule
(`min_bond_distance_cutoff ≤ d ≤ r_bond(A) + r_bond(B) + bond_distance_incr`),
then prunes to the first coordination shell — a contact survives only if
it is within `1.3×` the nearer atom's nearest-neighbour distance
(`COORDINATION_SHELL_FACTOR` in `display/structure/builder.py`). This
stop-gap handles the common cases (e.g. LBCO renders just the Co–O
octahedron) without a new dependency, but the fixed factor is still a
heuristic: it can over-prune strongly distorted shells (e.g. elongated
Jahn–Teller octahedra) or under-prune others, and it is not yet
user-configurable.

**Fix:** consider a robust, configurable near-neighbour algorithm for
automatic "reasonable" bonding — e.g. a Voronoi / solid-angle method
such as pymatgen's `CrystalNN` or `VoronoiNN`, which weights neighbours
by solid angle instead of a single relative cutoff. The Voronoi route is
the most robust across arbitrary structures but introduces a heavyweight
dependency (pymatgen), so it needs a dependency decision; an
ASE/Jmol-style multiplicative covalent tolerance is lighter but, like
the current factor, cannot separate shells when ionic-cation covalent
radii are large.

**Depends on:** dependency decision for pymatgen (if the Voronoi route
is chosen).
