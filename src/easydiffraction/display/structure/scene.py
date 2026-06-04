# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Renderer-neutral structure scene primitives.

A :class:`StructureScene` is a flat set of typed primitives expressed in
Cartesian space, carrying no rendering-library or easydiffraction-domain
types. The scene builder produces it; renderers consume it. Keeping this
module free of domain imports lets the scene model be extracted into a
standalone ``crysview`` package later.
"""

from __future__ import annotations

from dataclasses import dataclass

# Plain, serialisable coordinate/colour aliases (no numpy, no domain).
Vec3 = tuple[float, float, float]
Rgb = tuple[int, int, int]
Mat3 = tuple[Vec3, Vec3, Vec3]


@dataclass(frozen=True, slots=True)
class AtomSphere:
    """A single-occupancy atom drawn as a coloured sphere."""

    centre: Vec3
    radius: float
    colour: Rgb
    label: str
    asymmetric: bool = False


@dataclass(frozen=True, slots=True)
class OccupancyWedge:
    """One occupancy share (or vacancy) of a mixed site."""

    fraction: float
    colour: Rgb


@dataclass(frozen=True, slots=True)
class OccupancyWedgeSphere:
    """A mixed-occupancy site drawn as a sphere split into wedges."""

    centre: Vec3
    radius: float
    wedges: tuple[OccupancyWedge, ...]
    label: str
    asymmetric: bool = False


@dataclass(frozen=True, slots=True)
class AdpEllipsoid:
    """
    An anisotropic ADP probability ellipsoid for one atom.

    ``wedges`` splits a shared site into relative-proportion colour
    wedges (empty for a single atom, which uses ``colour``).
    """

    centre: Vec3
    semi_axes: Vec3
    orientation: Mat3
    colour: Rgb
    label: str
    wedges: tuple[OccupancyWedge, ...] = ()
    asymmetric: bool = False


@dataclass(frozen=True, slots=True)
class Bond:
    """A bond between two atoms, split-coloured at its midpoint."""

    start: Vec3
    end: Vec3
    start_colour: Rgb
    end_colour: Rgb
    start_element: str = ''
    end_element: str = ''


@dataclass(frozen=True, slots=True)
class MomentArrow:
    """A magnetic-moment arrow (defined but unused in version 1)."""

    origin: Vec3
    vector: Vec3
    colour: Rgb


@dataclass(frozen=True, slots=True)
class CellEdge:
    """One unit-cell edge as a Cartesian segment."""

    start: Vec3
    end: Vec3


@dataclass(frozen=True, slots=True)
class CellEdges:
    """The twelve unit-cell edges as Cartesian segments."""

    edges: tuple[CellEdge, ...]


@dataclass(frozen=True, slots=True)
class AxisArrow:
    """One crystallographic axis arrow (a, b, or c)."""

    vector: Vec3
    colour: Rgb
    letter: str


@dataclass(frozen=True, slots=True)
class AxisTriad:
    """The a/b/c axis triad drawn from the cell origin."""

    origin: Vec3
    axes: tuple[AxisArrow, AxisArrow, AxisArrow]


@dataclass(frozen=True, slots=True)
class TextLabel:
    """A text label anchored at a Cartesian point."""

    anchor: Vec3
    text: str


@dataclass(frozen=True, slots=True)
class LegendEntry:
    """
    One element's colour swatch and symbol for the structure legend.
    """

    symbol: str
    colour: Rgb


@dataclass(frozen=True, slots=True)
class StructureScene:
    """Renderer-neutral Cartesian primitives for one structure."""

    cell_basis: Mat3
    atoms: tuple[AtomSphere, ...] = ()
    occupancy_spheres: tuple[OccupancyWedgeSphere, ...] = ()
    ellipsoids: tuple[AdpEllipsoid, ...] = ()
    bonds: tuple[Bond, ...] = ()
    moments: tuple[MomentArrow, ...] = ()
    cell_edges: CellEdges | None = None
    axes: AxisTriad | None = None
    labels: tuple[TextLabel, ...] = ()
    legend: tuple[LegendEntry, ...] = ()
