# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Scene builder: crystal structure to renderer-neutral scene.

The easydiffraction-specific adapter. It reads the structure categories,
performs symmetry expansion, fractional-to-Cartesian conversion, ADP
eigendecomposition, radius/colour lookup, occupancy splitting, and bond
detection, and emits a :class:`StructureScene`. All crystallographic
computation lives here so renderers stay thin.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.stats import chi

from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.atom_sites.enums import AdpTypeEnum
from easydiffraction.display.structure.assets.colors import AXIS_COLORS
from easydiffraction.display.structure.assets.colors import color_for
from easydiffraction.display.structure.assets.radii import radius_for
from easydiffraction.display.structure.enums import AtomViewEnum
from easydiffraction.display.structure.scene import AdpEllipsoid
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import AxisArrow
from easydiffraction.display.structure.scene import AxisTriad
from easydiffraction.display.structure.scene import Bond
from easydiffraction.display.structure.scene import CellEdge
from easydiffraction.display.structure.scene import CellEdges
from easydiffraction.display.structure.scene import LegendEntry
from easydiffraction.display.structure.scene import OccupancyWedge
from easydiffraction.display.structure.scene import OccupancyWedgeSphere
from easydiffraction.display.structure.scene import StructureScene
from easydiffraction.display.structure.scene import TextLabel

# Tolerance (fractional units) for scene-atom identity and occupancy grouping.
IDENTITY_TOL = 1e-4
EIGHT_PI_SQ = 8.0 * np.pi**2
DEFAULT_BOND_INCR = 0.25
# Prune bonds to the first coordination shell: keep a contact only if it is
# within this multiple of the nearer atom's nearest-neighbour distance. Stops
# large ionic-cation covalent radii (e.g. La/Ba) from bonding to every anion
# (see open issue #108 for the full near-neighbour approach).
COORDINATION_SHELL_FACTOR = 1.3
ALL_FEATURES = ('atoms', 'bonds', 'cell', 'axes', 'moments', 'labels')


@dataclass(frozen=True)
class FeatureAvailability:
    """What a structure's data supports, for 'auto' resolution + options."""

    available: frozenset[str]
    radius_substitutions: tuple[str, ...]


@dataclass(frozen=True)
class _SceneAtom:
    """An emitted atom primitive plus data needed for bonds and labels."""

    primitive: object
    centre: np.ndarray
    element: str
    colour: tuple[int, int, int]
    label: str


def _element_symbol(type_symbol: str) -> str:
    """Extract the bare element symbol from a CIF type symbol."""
    match = re.match(r'[A-Z][a-z]?', type_symbol.strip())
    return match.group() if match else type_symbol.strip()


def _vec3(values) -> tuple[float, float, float]:
    return (float(values[0]), float(values[1]), float(values[2]))


def _cell_lengths_angles(cell) -> tuple[float, float, float, float, float, float]:
    return (
        cell.length_a.value, cell.length_b.value, cell.length_c.value,
        cell.angle_alpha.value, cell.angle_beta.value, cell.angle_gamma.value,
    )


def _reciprocal_lengths(cell) -> np.ndarray:
    a, b, c, alpha, beta, gamma = _cell_lengths_angles(cell)
    al, be, ga = np.radians([alpha, beta, gamma])
    ca, cb, cg = np.cos([al, be, ga])
    omega = np.sqrt(1.0 - ca * ca - cb * cb - cg * cg + 2.0 * ca * cb * cg)
    return np.array([np.sin(al) / (a * omega), np.sin(be) / (b * omega), np.sin(ga) / (c * omega)])


def _lattice_shifts(pos: np.ndarray, view_range):
    axis_ranges = []
    for i in range(3):
        lo, hi = view_range[i]
        n_lo = int(np.ceil(lo - pos[i] - IDENTITY_TOL))
        n_hi = int(np.floor(hi - pos[i] + IDENTITY_TOL))
        axis_ranges.append(range(n_lo, n_hi + 1))
    for shift in product(*axis_ranges):
        yield np.array(shift, dtype=float)


def _pos_key(pos: np.ndarray) -> tuple[int, int, int]:
    return tuple(int(round(v / IDENTITY_TOL)) for v in pos)


def _expand_positions(sites, ops, view_range):
    """Generate (row_index, fractional position, rotation) for each in-range copy.

    The symmetry rotation is kept so an anisotropic ADP tensor can be rotated
    onto each equivalent site (otherwise every copy reuses one orientation).
    """
    generated = []
    identity = np.eye(3)
    for idx, atom in enumerate(sites):
        base = np.array([atom.fract_x.value, atom.fract_y.value, atom.fract_z.value], dtype=float)
        for rot, trans in ops:
            image = rot @ base + trans
            reference_op = bool(np.allclose(rot, identity) and np.allclose(trans, 0.0))
            for shift in _lattice_shifts(image, view_range):
                is_au = reference_op and bool(np.allclose(shift, 0.0))
                generated.append((idx, image + shift, rot, is_au))
    return generated


def _group_by_position(generated):
    """Dedup scene atoms (row + position) and cluster coincident positions."""
    seen: dict = {}
    for idx, pos, rot, is_au in generated:
        seen.setdefault((idx, _pos_key(pos)), (idx, pos, rot, is_au))
    clusters: dict = {}
    for idx, pos, rot, is_au in seen.values():
        clusters.setdefault(_pos_key(pos), []).append((idx, pos, rot, is_au))
    return clusters


def _cartesian_u(atom, aniso, matrix: np.ndarray, cell, rot: np.ndarray) -> np.ndarray:
    """Cartesian U tensor for an anisotropic atom (CIF U^ij convention).

    ``rot`` is the fractional symmetry rotation that placed this copy; the
    tensor is rotated onto the copy in Cartesian space so each equivalent
    site shows the correctly oriented ellipsoid.
    """
    comps = np.array([
        [aniso.adp_11.value, aniso.adp_12.value, aniso.adp_13.value],
        [aniso.adp_12.value, aniso.adp_22.value, aniso.adp_23.value],
        [aniso.adp_13.value, aniso.adp_23.value, aniso.adp_33.value],
    ], dtype=float)
    if AdpTypeEnum(atom.adp_type.value) is AdpTypeEnum.BANI:
        comps = comps / EIGHT_PI_SQ
    mn = matrix @ np.diag(_reciprocal_lengths(cell))
    u_cart = mn @ comps @ mn.T
    r_cart = matrix @ rot @ np.linalg.inv(matrix)
    return r_cart @ u_cart @ r_cart.T


def _display_radius(model_radius: float, style) -> float:
    """Square-root-compressed ball radius (narrows the heavy/light spread)."""
    return style.atom_scale.value * float(np.sqrt(model_radius))


def _atom_shape(atom, *, style, matrix, cell, aniso_collection, rot):
    """Return an atom's ADP-driven shape and the radius-substitution flag.

    The shape is ``('ellipsoid', semi_axes, orientation)`` for an anisotropic
    atom in the ADP view, otherwise ``('sphere', radius)``. ``rot`` is the
    symmetry rotation placing this copy (identity for the reference atom).
    """
    element = _element_symbol(atom.type_symbol.value)
    view = AtomViewEnum(style.atom_view.value)
    radius, substituted = radius_for(element, view.radius_model())
    ball_radius = _display_radius(radius, style)
    label = atom.label.value
    adp_type = AdpTypeEnum(atom.adp_type.value)
    scale = float(chi.ppf(style.adp_probability.value, 3))
    if view.is_adp and adp_type in {AdpTypeEnum.UANI, AdpTypeEnum.BANI} \
            and label in aniso_collection:
        u_cart = _cartesian_u(atom, aniso_collection[label], matrix, cell, rot)
        semi, orient = ecr.adp_principal_axes(u_cart)
        shape = ('ellipsoid', _vec3(semi * scale),
                 tuple(_vec3(orient[:, i]) for i in range(3)))
    elif view.is_adp and adp_type in {AdpTypeEnum.UISO, AdpTypeEnum.BISO}:
        u_iso = atom.adp_iso.value
        if adp_type is AdpTypeEnum.BISO:
            u_iso = u_iso / EIGHT_PI_SQ
        iso_radius = float(np.sqrt(max(u_iso, 0.0))) * scale
        shape = ('sphere', iso_radius or ball_radius)
    else:
        shape = ('sphere', ball_radius)
    return shape, substituted


def _atom_primitive(atom, centre, *, style, matrix, cell, aniso_collection, rot, asymmetric):
    """Build a solid sphere/ellipsoid primitive for a single atom."""
    element = _element_symbol(atom.type_symbol.value)
    colour = color_for(element, style.color_scheme.value)
    shape, substituted = _atom_shape(
        atom, style=style, matrix=matrix, cell=cell, aniso_collection=aniso_collection, rot=rot,
    )
    if shape[0] == 'ellipsoid':
        primitive = AdpEllipsoid(_vec3(centre), shape[1], shape[2], colour,
                                 atom.label.value, asymmetric=asymmetric)
    else:
        primitive = AtomSphere(_vec3(centre), shape[1], colour, atom.label.value,
                               asymmetric=asymmetric)
    return _SceneAtom(primitive, centre, element, colour, atom.label.value), substituted


def _wedge_atom(rows, centre, *, style, matrix, cell, aniso_collection, asymmetric):
    """Build a shared-site primitive: the major atom's ADP shape split into
    relative-proportion colour wedges (absolute occupancy ignored)."""
    total = sum(occ for _, occ, _, _, _, _ in rows) or 1.0
    wedges = tuple(OccupancyWedge(occ / total, colour) for _, occ, _, colour, _, _ in rows)
    major_atom, _occ, major_element, major_colour, _radius, major_rot = max(rows, key=lambda r: r[1])
    label = '/'.join(r[0].label.value for r in rows)
    shape, _ = _atom_shape(
        major_atom, style=style, matrix=matrix, cell=cell,
        aniso_collection=aniso_collection, rot=major_rot,
    )
    if shape[0] == 'ellipsoid':
        primitive = AdpEllipsoid(_vec3(centre), shape[1], shape[2], major_colour,
                                 label, wedges, asymmetric)
    else:
        primitive = OccupancyWedgeSphere(_vec3(centre), shape[1], wedges, label, asymmetric)
    return _SceneAtom(primitive, centre, major_element, major_colour, label)


def _build_atoms(sites, clusters, *, style, matrix, cell, aniso_collection):
    """Return the scene atoms (one per position cluster) and substitutions."""
    scene_atoms = []
    substitutions: set = set()
    radius_model = AtomViewEnum(style.atom_view.value).radius_model()
    for members in clusters.values():
        centre = ecr.fractional_to_cartesian(members[0][1], matrix)
        cluster_au = any(member[3] for member in members)
        if len(members) == 1:
            idx, _pos, rot, _au = members[0]
            atom = sites[idx]
            scene_atom, substituted = _atom_primitive(
                atom, centre, style=style, matrix=matrix, cell=cell,
                aniso_collection=aniso_collection, rot=rot, asymmetric=cluster_au,
            )
            scene_atoms.append(scene_atom)
            if substituted:
                substitutions.add(_element_symbol(atom.type_symbol.value))
            continue
        rows = []
        for idx, _pos, rot, _au in members:
            atom = sites[idx]
            element = _element_symbol(atom.type_symbol.value)
            colour = color_for(element, style.color_scheme.value)
            radius, substituted = radius_for(element, radius_model)
            rows.append((atom, atom.occupancy.value, element, colour, radius, rot))
            if substituted:
                substitutions.add(element)
        scene_atoms.append(_wedge_atom(
            rows, centre, style=style, matrix=matrix, cell=cell,
            aniso_collection=aniso_collection, asymmetric=cluster_au,
        ))
    return scene_atoms, substitutions


def _build_bonds(scene_atoms, geom_min: float, geom_incr: float):
    """Detect bonds via the cif_core _geom rule, pruned to the first shell."""
    bonds = []
    count = len(scene_atoms)
    if count < 2:
        return bonds
    radii = [radius_for(a.element, 'covalent')[0] for a in scene_atoms]
    centres = np.array([a.centre for a in scene_atoms], dtype=float)
    distances = np.linalg.norm(centres[:, None, :] - centres[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    nearest = distances.min(axis=1)
    for i, atom_i in enumerate(scene_atoms):
        for j in range(i + 1, count):
            atom_j = scene_atoms[j]
            distance = float(distances[i, j])
            shell = min(nearest[i], nearest[j]) * COORDINATION_SHELL_FACTOR
            covalent_cutoff = radii[i] + radii[j] + geom_incr
            if geom_min <= distance <= min(covalent_cutoff, shell):
                bonds.append(Bond(_vec3(atom_i.centre), _vec3(atom_j.centre),
                                  atom_i.colour, atom_j.colour,
                                  atom_i.element, atom_j.element))
    return bonds


def _cell_edges(matrix: np.ndarray) -> CellEdges:
    corners = {tuple(c): _vec3(matrix @ np.array(c, dtype=float))
               for c in product((0, 1), repeat=3)}
    edges = []
    for c in corners:
        for axis in range(3):
            if c[axis] == 0:
                neighbour = tuple(1 if k == axis else c[k] for k in range(3))
                edges.append(CellEdge(corners[c], corners[neighbour]))
    return CellEdges(tuple(edges))


def _axis_triad(matrix: np.ndarray) -> AxisTriad:
    lengths = [float(np.linalg.norm(matrix[:, i])) for i in range(3)]
    extra = 0.3 * max(lengths)
    arrows = []
    for i, letter in enumerate('abc'):
        direction = matrix[:, i] / lengths[i]
        arrows.append(
            AxisArrow(_vec3(direction * (lengths[i] + extra)), AXIS_COLORS[letter], letter)
        )
    return AxisTriad((0.0, 0.0, 0.0), (arrows[0], arrows[1], arrows[2]))


def _legend(sites, style) -> tuple[LegendEntry, ...]:
    """Return one colour swatch per distinct element, in first-seen order."""
    entries: dict[str, tuple[int, int, int]] = {}
    for atom in sites:
        element = _element_symbol(atom.type_symbol.value)
        if element not in entries:
            entries[element] = color_for(element, style.color_scheme.value)
    return tuple(LegendEntry(symbol, colour) for symbol, colour in entries.items())


def build_scene(structure, *, style, view_range, features) -> StructureScene:
    """
    Build a renderer-neutral scene from a structure and resolved features.

    Parameters
    ----------
    structure : object
        A structure datablock with ``cell``, ``atom_sites``,
        ``atom_site_aniso``, ``space_group`` and ``geom`` categories.
    style : object
        The ``project.style`` category (atom shape, radius model, colour
        scheme, ADP probability).
    view_range : tuple
        Per-axis ``((min, max), (min, max), (min, max))`` fractional range.
    features : frozenset[str]
        The already-resolved set of primitives to emit (never ``'auto'``);
        the builder never re-implements visibility precedence.

    Returns
    -------
    StructureScene
        The flat Cartesian primitive set for the renderers.
    """
    cell = structure.cell
    matrix = ecr.orthogonalization_matrix(*_cell_lengths_angles(cell))
    sg = structure.space_group
    ops = ecr.symmetry_operators(sg.name_h_m.value, sg.it_coordinate_system_code.value)
    sites = list(structure.atom_sites)

    clusters = _group_by_position(_expand_positions(sites, ops, view_range))
    scene_atoms, _ = _build_atoms(
        sites, clusters, style=style, matrix=matrix, cell=cell,
        aniso_collection=structure.atom_site_aniso,
    )

    bonds: tuple = ()
    if 'bonds' in features:
        geom = getattr(structure, 'geom', None)
        geom_min = geom.min_bond_distance_cutoff.value if geom is not None else 0.0
        geom_incr = geom.bond_distance_incr.value if geom is not None else DEFAULT_BOND_INCR
        bonds = tuple(_build_bonds(scene_atoms, geom_min, geom_incr))

    show_atoms = 'atoms' in features
    return StructureScene(
        cell_basis=tuple(_vec3(matrix[:, i]) for i in range(3)),
        atoms=tuple(a.primitive for a in scene_atoms
                    if show_atoms and isinstance(a.primitive, AtomSphere)),
        occupancy_spheres=tuple(a.primitive for a in scene_atoms
                                if show_atoms and isinstance(a.primitive, OccupancyWedgeSphere)),
        ellipsoids=tuple(a.primitive for a in scene_atoms
                         if show_atoms and isinstance(a.primitive, AdpEllipsoid)),
        bonds=bonds,
        moments=(),
        cell_edges=_cell_edges(matrix) if 'cell' in features else None,
        axes=_axis_triad(matrix) if 'axes' in features else None,
        labels=tuple(TextLabel(_vec3(a.centre), a.label) for a in scene_atoms)
        if 'labels' in features else (),
        legend=_legend(sites, style) if 'atoms' in features else (),
    )


def structure_feature_availability(structure, *, style) -> FeatureAvailability:
    """
    Report which features a structure supports, without building a scene.

    Used by the display facade for ``include='auto'`` resolution and by
    ``show_structure_options()``; the builder is the only reader of the
    structure, so availability is computed once here.

    Parameters
    ----------
    structure : object
        A structure datablock.
    style : object
        The ``project.style`` category (its radius model drives the
        covalent-substitution report).

    Returns
    -------
    FeatureAvailability
        Available feature names and the elements whose radius fell back to
        covalent under the selected model.
    """
    sites = list(structure.atom_sites)
    available = {'cell', 'axes'}
    if sites:
        available |= {'atoms', 'bonds', 'labels'}
    substitutions = set()
    radius_model = AtomViewEnum(style.atom_view.value).radius_model()
    for atom in sites:
        element = _element_symbol(atom.type_symbol.value)
        _, substituted = radius_for(element, radius_model)
        if substituted:
            substitutions.add(element)
    return FeatureAvailability(frozenset(available), tuple(sorted(substitutions)))
