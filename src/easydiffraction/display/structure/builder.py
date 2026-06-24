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
from itertools import starmap
from operator import itemgetter
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from collections.abc import Iterator

# Tolerance (fractional units) for scene-atom identity and
# occupancy grouping.
IDENTITY_TOL = 1e-4
EIGHT_PI_SQ = 8.0 * np.pi**2
DEFAULT_BOND_INCR = 0.25
# Prune bonds to the first coordination shell: keep a contact only
# if it is within this multiple of the nearer atom's nearest-neighbour
# distance. Stops large ionic-cation covalent radii (e.g. La/Ba) from
# bonding to every anion (see open issue #108 for the full
# near-neighbour approach).
COORDINATION_SHELL_FACTOR = 1.3
# Smallest atom count that can form a bond.
MIN_BONDABLE_ATOMS = 2
ALL_FEATURES = ('atoms', 'bonds', 'cell', 'axes', 'moments', 'labels')

# Per-axis ``((min, max), (min, max), (min, max))`` fractional range.
ViewRange = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
# One expanded copy: ``(row_index, position, rotation, is_au)``.
GeneratedCopy = tuple[int, np.ndarray, np.ndarray, bool]
# Atom-shape descriptor: ``('sphere', radius)`` or
# ``('ellipsoid', semi_axes, orientation)``.
AtomShape = tuple[object, ...]
# One shared-site row:
# ``(atom, occupancy, element, colour, radius, rotation)``.
WedgeRow = tuple[object, float, str, tuple[int, int, int], float, np.ndarray]


@dataclass(frozen=True)
class FeatureAvailability:
    """
    What a structure's data supports, for 'auto' resolution + options.
    """

    available: frozenset[str]
    radius_substitutions: tuple[str, ...]


@dataclass(frozen=True)
class _RenderContext:
    """
    Scene-wide inputs shared by every atom in one ``build_scene`` call.

    Bundles the values that do not vary per atom or per symmetry copy so
    the atom-building helpers thread a single context instead of four
    parallel arguments.
    """

    style: object
    matrix: np.ndarray
    cell: object
    aniso_collection: object


@dataclass(frozen=True)
class _SceneAtom:
    """
    An emitted atom primitive plus data needed for bonds and labels.
    """

    primitive: object
    centre: np.ndarray
    element: str
    colour: tuple[int, int, int]
    label: str


def _element_symbol(type_symbol: str) -> str:
    """Extract the bare element symbol from a CIF type symbol."""
    match = re.match(r'[A-Z][a-z]?', type_symbol.strip())
    return match.group() if match else type_symbol.strip()


def _vec3(values: np.ndarray | tuple[float, ...]) -> tuple[float, float, float]:
    """Return the first three values as a float 3-tuple."""
    return (float(values[0]), float(values[1]), float(values[2]))


def _cell_lengths_angles(
    cell: object,
) -> tuple[float, float, float, float, float, float]:
    """Return the cell lengths and angles as a 6-tuple."""
    return (
        cell.length_a.value,
        cell.length_b.value,
        cell.length_c.value,
        cell.angle_alpha.value,
        cell.angle_beta.value,
        cell.angle_gamma.value,
    )


def _reciprocal_lengths(cell: object) -> np.ndarray:
    """Return the reciprocal-cell axis lengths a*, b*, c*."""
    a, b, c, alpha, beta, gamma = _cell_lengths_angles(cell)
    return np.array(ecr.reciprocal_cell_lengths(a, b, c, alpha, beta, gamma))


def _lattice_shifts(
    pos: np.ndarray,
    view_range: ViewRange,
) -> Iterator[np.ndarray]:
    """Yield integer lattice shifts placing pos within the view."""
    axis_ranges = []
    for i in range(3):
        lo, hi = view_range[i]
        n_lo = int(np.ceil(lo - pos[i] - IDENTITY_TOL))
        n_hi = int(np.floor(hi - pos[i] + IDENTITY_TOL))
        axis_ranges.append(range(n_lo, n_hi + 1))
    for shift in product(*axis_ranges):
        yield np.array(shift, dtype=float)


def _pos_key(pos: np.ndarray) -> tuple[int, int, int]:
    """Return a tolerance-quantised key for position identity."""
    return tuple(round(v / IDENTITY_TOL) for v in pos)


def _expand_positions(
    sites: list[object],
    ops: list[tuple[np.ndarray, np.ndarray]],
    view_range: ViewRange,
) -> list[GeneratedCopy]:
    """
    Generate per-copy placement data for each in-range image.

    Yields ``(row_index, fractional position, rotation,
    is_asymmetric_unit)`` for each in-range copy.

    The symmetry rotation is kept so an anisotropic ADP tensor can be
    rotated onto each equivalent site (otherwise every copy reuses one
    orientation).
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


def _group_by_position(
    generated: list[GeneratedCopy],
) -> dict[tuple[int, int, int], list[GeneratedCopy]]:
    """
    Dedup scene atoms and cluster coincident positions.

    Deduplicates by ``(row, position)`` and groups copies that share a
    position.
    """
    seen: dict[tuple[int, tuple[int, int, int]], GeneratedCopy] = {}
    for idx, pos, rot, is_au in generated:
        seen.setdefault((idx, _pos_key(pos)), (idx, pos, rot, is_au))
    clusters: dict[tuple[int, int, int], list[GeneratedCopy]] = {}
    for idx, pos, rot, is_au in seen.values():
        clusters.setdefault(_pos_key(pos), []).append((idx, pos, rot, is_au))
    return clusters


def _cartesian_u(
    atom: object,
    aniso: object,
    matrix: np.ndarray,
    cell: object,
    rot: np.ndarray,
) -> np.ndarray:
    """
    Cartesian U tensor for an anisotropic atom (CIF U^ij convention).

    ``rot`` is the fractional symmetry rotation that placed this copy;
    the tensor is rotated onto the copy in Cartesian space so each
    equivalent site shows the correctly oriented ellipsoid.
    """
    comps = np.array(
        [
            [aniso.adp_11.value, aniso.adp_12.value, aniso.adp_13.value],
            [aniso.adp_12.value, aniso.adp_22.value, aniso.adp_23.value],
            [aniso.adp_13.value, aniso.adp_23.value, aniso.adp_33.value],
        ],
        dtype=float,
    )
    if AdpTypeEnum(atom.adp_type.value) is AdpTypeEnum.BANI:
        comps /= EIGHT_PI_SQ
    mn = matrix @ np.diag(_reciprocal_lengths(cell))
    u_cart = mn @ comps @ mn.T
    r_cart = matrix @ rot @ np.linalg.inv(matrix)
    return r_cart @ u_cart @ r_cart.T


def _display_radius(model_radius: float, style: object) -> float:
    """
    Square-root-compressed ball radius (narrows heavy/light spread).
    """
    return style.atom_scale.value * float(np.sqrt(model_radius))


def _atom_shape(
    atom: object,
    ctx: _RenderContext,
    rot: np.ndarray,
) -> tuple[AtomShape, bool]:
    """
    Return an atom's ADP-driven shape and the substitution flag.

    The shape is ``('ellipsoid', semi_axes, orientation)`` for an
    anisotropic atom in the ADP view, otherwise ``('sphere', radius)``.
    ``rot`` is the symmetry rotation placing this copy (identity for the
    reference atom).
    """
    style = ctx.style
    element = _element_symbol(atom.type_symbol.value)
    view = AtomViewEnum(style.atom_view.value)
    radius, substituted = radius_for(element, view.radius_model())
    ball_radius = _display_radius(radius, style)
    label = atom.id.value
    adp_type = AdpTypeEnum(atom.adp_type.value)
    scale = float(chi.ppf(style.adp_probability.value, 3))
    if (
        view.is_adp
        and adp_type in {AdpTypeEnum.UANI, AdpTypeEnum.BANI}
        and label in ctx.aniso_collection
    ):
        u_cart = _cartesian_u(atom, ctx.aniso_collection[label], ctx.matrix, ctx.cell, rot)
        semi, orient = ecr.adp_principal_axes(u_cart)
        shape = (
            'ellipsoid',
            _vec3(semi * scale),
            tuple(_vec3(orient[:, i]) for i in range(3)),
        )
    elif view.is_adp and adp_type in {AdpTypeEnum.UISO, AdpTypeEnum.BISO}:
        u_iso = atom.adp_iso.value
        if adp_type is AdpTypeEnum.BISO:
            u_iso /= EIGHT_PI_SQ
        iso_radius = float(np.sqrt(max(u_iso, 0.0))) * scale
        shape = ('sphere', iso_radius or ball_radius)
    else:
        shape = ('sphere', ball_radius)
    return shape, substituted


def _atom_primitive(
    atom: object,
    centre: np.ndarray,
    ctx: _RenderContext,
    rot: np.ndarray,
    *,
    asymmetric: bool,
) -> tuple[_SceneAtom, bool]:
    """Build a solid sphere/ellipsoid primitive for a single atom."""
    element = _element_symbol(atom.type_symbol.value)
    colour = color_for(element, ctx.style.color_scheme.value)
    shape, substituted = _atom_shape(atom, ctx, rot)
    if shape[0] == 'ellipsoid':
        primitive = AdpEllipsoid(
            _vec3(centre),
            shape[1],
            shape[2],
            colour,
            atom.id.value,
            asymmetric=asymmetric,
        )
    else:
        primitive = AtomSphere(
            _vec3(centre),
            shape[1],
            colour,
            atom.id.value,
            asymmetric=asymmetric,
        )
    return (
        _SceneAtom(primitive, centre, element, colour, atom.id.value),
        substituted,
    )


def _wedge_atom(
    rows: list[WedgeRow],
    centre: np.ndarray,
    ctx: _RenderContext,
    *,
    asymmetric: bool,
) -> _SceneAtom:
    """
    Build a shared-site primitive split into colour wedges.

    The major atom's ADP shape is split into relative-proportion colour
    wedges (absolute occupancy is ignored).
    """
    total = sum(occ for _, occ, _, _, _, _ in rows) or 1.0
    wedges = tuple(OccupancyWedge(occ / total, colour) for _, occ, _, colour, _, _ in rows)
    major_atom, _occ, major_element, major_colour, _radius, major_rot = max(
        rows, key=itemgetter(1)
    )
    label = '/'.join(r[0].id.value for r in rows)
    shape, _ = _atom_shape(major_atom, ctx, major_rot)
    if shape[0] == 'ellipsoid':
        primitive = AdpEllipsoid(
            _vec3(centre), shape[1], shape[2], major_colour, label, wedges, asymmetric
        )
    else:
        primitive = OccupancyWedgeSphere(_vec3(centre), shape[1], wedges, label, asymmetric)
    return _SceneAtom(primitive, centre, major_element, major_colour, label)


def _build_atoms(
    sites: list[object],
    clusters: dict[tuple[int, int, int], list[GeneratedCopy]],
    ctx: _RenderContext,
) -> tuple[list[_SceneAtom], set[str]]:
    """
    Return the scene atoms (one per cluster) and substitutions.
    """
    scene_atoms: list[_SceneAtom] = []
    substitutions: set[str] = set()
    radius_model = AtomViewEnum(ctx.style.atom_view.value).radius_model()
    for members in clusters.values():
        centre = ecr.fractional_to_cartesian(members[0][1], ctx.matrix)
        cluster_au = any(member[3] for member in members)
        if len(members) == 1:
            idx, _pos, rot, _au = members[0]
            atom = sites[idx]
            scene_atom, substituted = _atom_primitive(
                atom, centre, ctx, rot, asymmetric=cluster_au
            )
            scene_atoms.append(scene_atom)
            if substituted:
                substitutions.add(_element_symbol(atom.type_symbol.value))
            continue
        rows: list[WedgeRow] = []
        for idx, _pos, rot, _au in members:
            atom = sites[idx]
            element = _element_symbol(atom.type_symbol.value)
            colour = color_for(element, ctx.style.color_scheme.value)
            radius, substituted = radius_for(element, radius_model)
            rows.append((atom, atom.occupancy.value, element, colour, radius, rot))
            if substituted:
                substitutions.add(element)
        scene_atoms.append(_wedge_atom(rows, centre, ctx, asymmetric=cluster_au))
    return scene_atoms, substitutions


def _build_bonds(
    scene_atoms: list[_SceneAtom],
    geom_min: float,
    geom_incr: float,
) -> list[Bond]:
    """
    Detect bonds via the cif_core _geom rule, pruned to first shell.
    """
    bonds: list[Bond] = []
    count = len(scene_atoms)
    if count < MIN_BONDABLE_ATOMS:
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
                bonds.append(
                    Bond(
                        _vec3(atom_i.centre),
                        _vec3(atom_j.centre),
                        atom_i.colour,
                        atom_j.colour,
                        atom_i.element,
                        atom_j.element,
                    )
                )
    return bonds


def _cell_edges(matrix: np.ndarray) -> CellEdges:
    """Return the twelve Cartesian edges of the unit cell."""
    corners = {
        tuple(c): _vec3(matrix @ np.array(c, dtype=float)) for c in product((0, 1), repeat=3)
    }
    edges = []
    for c, corner in corners.items():
        for axis in range(3):
            if c[axis] == 0:
                neighbour = tuple(1 if k == axis else c[k] for k in range(3))
                edges.append(CellEdge(corner, corners[neighbour]))
    return CellEdges(tuple(edges))


def _axis_triad(matrix: np.ndarray) -> AxisTriad:
    """Return the a/b/c axis arrows anchored at the origin."""
    lengths = [float(np.linalg.norm(matrix[:, i])) for i in range(3)]
    extra = 0.3 * max(lengths)
    arrows = []
    for i, letter in enumerate('abc'):
        direction = matrix[:, i] / lengths[i]
        arrows.append(
            AxisArrow(_vec3(direction * (lengths[i] + extra)), AXIS_COLORS[letter], letter)
        )
    return AxisTriad((0.0, 0.0, 0.0), (arrows[0], arrows[1], arrows[2]))


def _legend(sites: list[object], style: object) -> tuple[LegendEntry, ...]:
    """
    Return one colour swatch per element, in first-seen order.
    """
    entries: dict[str, tuple[int, int, int]] = {}
    for atom in sites:
        element = _element_symbol(atom.type_symbol.value)
        if element not in entries:
            entries[element] = color_for(element, style.color_scheme.value)
    return tuple(starmap(LegendEntry, entries.items()))


def build_scene(
    structure: object,
    *,
    style: object,
    view_range: ViewRange,
    features: frozenset[str],
) -> StructureScene:
    """
    Build a renderer-neutral scene from a structure.

    Builds the scene from the structure and the already-resolved
    features.

    Parameters
    ----------
    structure : object
        A structure datablock with ``cell``, ``atom_sites``,
        ``atom_site_aniso``, ``space_group`` and ``geom`` categories.
    style : object
        The ``project.structure_style`` category (atom view, colour
        scheme, ADP probability, atom scale).
    view_range : ViewRange
        Per-axis ``((min, max), (min, max), (min, max))`` fractional
        range.
    features : frozenset[str]
        The already-resolved set of primitives to emit (never
        ``'auto'``); the builder never re-implements visibility
        precedence.

    Returns
    -------
    StructureScene
        The flat Cartesian primitive set for the renderers.
    """
    cell = structure.cell
    matrix = ecr.orthogonalization_matrix(*_cell_lengths_angles(cell))
    sg = structure.space_group
    ops = ecr.symmetry_operators(sg.name_h_m.value, sg.coord_system_code.value)
    sites = list(structure.atom_sites)

    ctx = _RenderContext(
        style=style,
        matrix=matrix,
        cell=cell,
        aniso_collection=structure.atom_site_aniso,
    )
    clusters = _group_by_position(_expand_positions(sites, ops, view_range))
    scene_atoms, _ = _build_atoms(sites, clusters, ctx)

    bonds: tuple[Bond, ...] = ()
    if 'bonds' in features:
        geom = getattr(structure, 'geom', None)
        geom_min = geom.min_bond_distance_cutoff.value if geom is not None else 0.0
        geom_incr = geom.bond_distance_inc.value if geom is not None else DEFAULT_BOND_INCR
        bonds = tuple(_build_bonds(scene_atoms, geom_min, geom_incr))

    show_atoms = 'atoms' in features
    return StructureScene(
        cell_basis=tuple(_vec3(matrix[:, i]) for i in range(3)),
        atoms=tuple(
            a.primitive for a in scene_atoms if show_atoms and isinstance(a.primitive, AtomSphere)
        ),
        occupancy_spheres=tuple(
            a.primitive
            for a in scene_atoms
            if show_atoms and isinstance(a.primitive, OccupancyWedgeSphere)
        ),
        ellipsoids=tuple(
            a.primitive
            for a in scene_atoms
            if show_atoms and isinstance(a.primitive, AdpEllipsoid)
        ),
        bonds=bonds,
        moments=(),
        cell_edges=_cell_edges(matrix) if 'cell' in features else None,
        axes=_axis_triad(matrix) if 'axes' in features else None,
        labels=tuple(TextLabel(_vec3(a.centre), a.label) for a in scene_atoms)
        if 'labels' in features
        else (),
        legend=_legend(sites, style) if 'atoms' in features else (),
    )


def structure_feature_availability(
    structure: object,
    *,
    style: object,
) -> FeatureAvailability:
    """
    Report which features a structure supports.

    Computes availability without building a scene. Used by the display
    facade for ``include='auto'`` resolution and by
    ``show_structure_options()``; the builder is the only reader of the
    structure, so availability is computed once here.

    Parameters
    ----------
    structure : object
        A structure datablock.
    style : object
        The ``project.structure_style`` category (its atom view drives
        the covalent-substitution report).

    Returns
    -------
    FeatureAvailability
        Available feature names and the elements whose radius fell back
        to covalent under the selected model.
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
