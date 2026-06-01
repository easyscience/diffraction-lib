# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for renderer-neutral structure scene primitives."""

from __future__ import annotations

import dataclasses

import pytest

import easydiffraction.display.structure.scene as scene_module
from easydiffraction.display.structure.scene import AdpEllipsoid
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import AxisArrow
from easydiffraction.display.structure.scene import AxisTriad
from easydiffraction.display.structure.scene import Bond
from easydiffraction.display.structure.scene import CellEdge
from easydiffraction.display.structure.scene import CellEdges
from easydiffraction.display.structure.scene import LegendEntry
from easydiffraction.display.structure.scene import MomentArrow
from easydiffraction.display.structure.scene import OccupancyWedge
from easydiffraction.display.structure.scene import OccupancyWedgeSphere
from easydiffraction.display.structure.scene import StructureScene
from easydiffraction.display.structure.scene import TextLabel

# ------------------------------------------------------------------
#  Shared minimal building blocks (no engine, no domain types)
# ------------------------------------------------------------------

ORIGIN = (0.0, 0.0, 0.0)
IDENTITY_BASIS = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Every primitive dataclass declared in the module, used by the
# cross-cutting structural tests below.
ALL_PRIMITIVES = (
    AtomSphere,
    OccupancyWedge,
    OccupancyWedgeSphere,
    AdpEllipsoid,
    Bond,
    MomentArrow,
    CellEdge,
    CellEdges,
    AxisArrow,
    AxisTriad,
    TextLabel,
    LegendEntry,
    StructureScene,
)


# ------------------------------------------------------------------
#  Module identity and import surface
# ------------------------------------------------------------------


def test_module_import():
    expected_module_name = 'easydiffraction.display.structure.scene'
    actual_module_name = scene_module.__name__
    assert expected_module_name == actual_module_name


def test_type_aliases_present():
    # The plain coordinate/colour aliases are part of the public surface
    # and must stay free of numpy/domain types (they are plain tuples).
    assert scene_module.Vec3 == tuple[float, float, float]
    assert scene_module.Rgb == tuple[int, int, int]
    assert scene_module.Mat3 == tuple[scene_module.Vec3, scene_module.Vec3, scene_module.Vec3]


# ------------------------------------------------------------------
#  Cross-cutting dataclass contract: frozen + slots
# ------------------------------------------------------------------


class TestDataclassContract:
    """Every primitive is a frozen, slotted dataclass."""

    @pytest.mark.parametrize('cls', ALL_PRIMITIVES)
    def test_is_dataclass(self, cls):
        assert dataclasses.is_dataclass(cls)

    @pytest.mark.parametrize('cls', ALL_PRIMITIVES)
    def test_is_frozen(self, cls):
        params = cls.__dataclass_params__
        assert params.frozen is True

    @pytest.mark.parametrize('cls', ALL_PRIMITIVES)
    def test_uses_slots(self, cls):
        # slots=True classes have a __slots__ and no per-instance __dict__.
        assert hasattr(cls, '__slots__')
        assert '__dict__' not in cls.__slots__


# ------------------------------------------------------------------
#  AtomSphere
# ------------------------------------------------------------------


class TestAtomSphere:
    def test_construction_and_fields(self):
        atom = AtomSphere(centre=(1.0, 2.0, 3.0), radius=0.5, colour=RED, label='Fe')
        assert atom.centre == (1.0, 2.0, 3.0)
        assert atom.radius == 0.5
        assert atom.colour == RED
        assert atom.label == 'Fe'

    def test_asymmetric_defaults_false(self):
        atom = AtomSphere(centre=ORIGIN, radius=1.0, colour=BLUE, label='O')
        assert atom.asymmetric is False

    def test_asymmetric_can_be_set(self):
        atom = AtomSphere(centre=ORIGIN, radius=1.0, colour=BLUE, label='O', asymmetric=True)
        assert atom.asymmetric is True

    def test_frozen_rejects_mutation(self):
        atom = AtomSphere(centre=ORIGIN, radius=1.0, colour=RED, label='Fe')
        with pytest.raises(dataclasses.FrozenInstanceError):
            atom.radius = 2.0

    def test_equality_by_value(self):
        a = AtomSphere(centre=ORIGIN, radius=1.0, colour=RED, label='Fe')
        b = AtomSphere(centre=ORIGIN, radius=1.0, colour=RED, label='Fe')
        assert a == b


# ------------------------------------------------------------------
#  OccupancyWedge
# ------------------------------------------------------------------


class TestOccupancyWedge:
    def test_construction_and_fields(self):
        wedge = OccupancyWedge(fraction=0.25, colour=GREEN)
        assert wedge.fraction == 0.25
        assert wedge.colour == GREEN

    def test_frozen_rejects_mutation(self):
        wedge = OccupancyWedge(fraction=0.25, colour=GREEN)
        with pytest.raises(dataclasses.FrozenInstanceError):
            wedge.fraction = 0.5


# ------------------------------------------------------------------
#  OccupancyWedgeSphere
# ------------------------------------------------------------------


class TestOccupancyWedgeSphere:
    def test_construction_and_fields(self):
        wedges = (
            OccupancyWedge(fraction=0.7, colour=RED),
            OccupancyWedge(fraction=0.3, colour=BLUE),
        )
        sphere = OccupancyWedgeSphere(
            centre=(0.5, 0.5, 0.5),
            radius=0.8,
            wedges=wedges,
            label='Fe/Mn',
        )
        assert sphere.centre == (0.5, 0.5, 0.5)
        assert sphere.radius == 0.8
        assert sphere.wedges == wedges
        assert sphere.label == 'Fe/Mn'

    def test_asymmetric_defaults_false(self):
        sphere = OccupancyWedgeSphere(centre=ORIGIN, radius=1.0, wedges=(), label='X')
        assert sphere.asymmetric is False

    def test_asymmetric_can_be_set(self):
        sphere = OccupancyWedgeSphere(
            centre=ORIGIN,
            radius=1.0,
            wedges=(),
            label='X',
            asymmetric=True,
        )
        assert sphere.asymmetric is True

    def test_frozen_rejects_mutation(self):
        sphere = OccupancyWedgeSphere(centre=ORIGIN, radius=1.0, wedges=(), label='X')
        with pytest.raises(dataclasses.FrozenInstanceError):
            sphere.radius = 2.0


# ------------------------------------------------------------------
#  AdpEllipsoid
# ------------------------------------------------------------------


class TestAdpEllipsoid:
    def test_construction_and_fields(self):
        ellipsoid = AdpEllipsoid(
            centre=(0.1, 0.2, 0.3),
            semi_axes=(0.4, 0.5, 0.6),
            orientation=IDENTITY_BASIS,
            colour=RED,
            label='Fe',
        )
        assert ellipsoid.centre == (0.1, 0.2, 0.3)
        assert ellipsoid.semi_axes == (0.4, 0.5, 0.6)
        assert ellipsoid.orientation == IDENTITY_BASIS
        assert ellipsoid.colour == RED
        assert ellipsoid.label == 'Fe'

    def test_wedges_default_empty(self):
        ellipsoid = AdpEllipsoid(
            centre=ORIGIN,
            semi_axes=(1.0, 1.0, 1.0),
            orientation=IDENTITY_BASIS,
            colour=RED,
            label='Fe',
        )
        assert ellipsoid.wedges == ()

    def test_asymmetric_defaults_false(self):
        ellipsoid = AdpEllipsoid(
            centre=ORIGIN,
            semi_axes=(1.0, 1.0, 1.0),
            orientation=IDENTITY_BASIS,
            colour=RED,
            label='Fe',
        )
        assert ellipsoid.asymmetric is False

    def test_optional_fields_can_be_set(self):
        wedges = (OccupancyWedge(fraction=0.5, colour=RED),)
        ellipsoid = AdpEllipsoid(
            centre=ORIGIN,
            semi_axes=(1.0, 1.0, 1.0),
            orientation=IDENTITY_BASIS,
            colour=RED,
            label='Fe',
            wedges=wedges,
            asymmetric=True,
        )
        assert ellipsoid.wedges == wedges
        assert ellipsoid.asymmetric is True

    def test_frozen_rejects_mutation(self):
        ellipsoid = AdpEllipsoid(
            centre=ORIGIN,
            semi_axes=(1.0, 1.0, 1.0),
            orientation=IDENTITY_BASIS,
            colour=RED,
            label='Fe',
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            ellipsoid.colour = BLUE


# ------------------------------------------------------------------
#  Bond
# ------------------------------------------------------------------


class TestBond:
    def test_construction_and_fields(self):
        bond = Bond(
            start=ORIGIN,
            end=(1.0, 1.0, 1.0),
            start_colour=RED,
            end_colour=BLUE,
        )
        assert bond.start == ORIGIN
        assert bond.end == (1.0, 1.0, 1.0)
        assert bond.start_colour == RED
        assert bond.end_colour == BLUE

    def test_element_fields_default_empty(self):
        bond = Bond(start=ORIGIN, end=(1.0, 0.0, 0.0), start_colour=RED, end_colour=BLUE)
        assert bond.start_element == ''
        assert bond.end_element == ''

    def test_element_fields_can_be_set(self):
        bond = Bond(
            start=ORIGIN,
            end=(1.0, 0.0, 0.0),
            start_colour=RED,
            end_colour=BLUE,
            start_element='Fe',
            end_element='O',
        )
        assert bond.start_element == 'Fe'
        assert bond.end_element == 'O'

    def test_frozen_rejects_mutation(self):
        bond = Bond(start=ORIGIN, end=(1.0, 0.0, 0.0), start_colour=RED, end_colour=BLUE)
        with pytest.raises(dataclasses.FrozenInstanceError):
            bond.start_colour = GREEN


# ------------------------------------------------------------------
#  MomentArrow
# ------------------------------------------------------------------


class TestMomentArrow:
    def test_construction_and_fields(self):
        moment = MomentArrow(origin=ORIGIN, vector=(0.0, 0.0, 1.0), colour=RED)
        assert moment.origin == ORIGIN
        assert moment.vector == (0.0, 0.0, 1.0)
        assert moment.colour == RED

    def test_frozen_rejects_mutation(self):
        moment = MomentArrow(origin=ORIGIN, vector=(0.0, 0.0, 1.0), colour=RED)
        with pytest.raises(dataclasses.FrozenInstanceError):
            moment.vector = (1.0, 0.0, 0.0)


# ------------------------------------------------------------------
#  CellEdge / CellEdges
# ------------------------------------------------------------------


class TestCellEdge:
    def test_construction_and_fields(self):
        edge = CellEdge(start=ORIGIN, end=(1.0, 0.0, 0.0))
        assert edge.start == ORIGIN
        assert edge.end == (1.0, 0.0, 0.0)

    def test_frozen_rejects_mutation(self):
        edge = CellEdge(start=ORIGIN, end=(1.0, 0.0, 0.0))
        with pytest.raises(dataclasses.FrozenInstanceError):
            edge.end = (2.0, 0.0, 0.0)


class TestCellEdges:
    def test_construction_and_fields(self):
        edges = (
            CellEdge(start=ORIGIN, end=(1.0, 0.0, 0.0)),
            CellEdge(start=ORIGIN, end=(0.0, 1.0, 0.0)),
        )
        cell_edges = CellEdges(edges=edges)
        assert cell_edges.edges == edges
        assert len(cell_edges.edges) == 2

    def test_frozen_rejects_mutation(self):
        cell_edges = CellEdges(edges=())
        with pytest.raises(dataclasses.FrozenInstanceError):
            cell_edges.edges = (CellEdge(start=ORIGIN, end=ORIGIN),)


# ------------------------------------------------------------------
#  AxisArrow / AxisTriad
# ------------------------------------------------------------------


class TestAxisArrow:
    def test_construction_and_fields(self):
        arrow = AxisArrow(vector=(1.0, 0.0, 0.0), colour=RED, letter='a')
        assert arrow.vector == (1.0, 0.0, 0.0)
        assert arrow.colour == RED
        assert arrow.letter == 'a'

    def test_frozen_rejects_mutation(self):
        arrow = AxisArrow(vector=(1.0, 0.0, 0.0), colour=RED, letter='a')
        with pytest.raises(dataclasses.FrozenInstanceError):
            arrow.letter = 'b'


class TestAxisTriad:
    def _triad(self):
        return AxisTriad(
            origin=ORIGIN,
            axes=(
                AxisArrow(vector=(1.0, 0.0, 0.0), colour=RED, letter='a'),
                AxisArrow(vector=(0.0, 1.0, 0.0), colour=GREEN, letter='b'),
                AxisArrow(vector=(0.0, 0.0, 1.0), colour=BLUE, letter='c'),
            ),
        )

    def test_construction_and_fields(self):
        triad = self._triad()
        assert triad.origin == ORIGIN
        assert len(triad.axes) == 3
        assert [arrow.letter for arrow in triad.axes] == ['a', 'b', 'c']

    def test_frozen_rejects_mutation(self):
        triad = self._triad()
        with pytest.raises(dataclasses.FrozenInstanceError):
            triad.origin = (1.0, 1.0, 1.0)


# ------------------------------------------------------------------
#  TextLabel
# ------------------------------------------------------------------


class TestTextLabel:
    def test_construction_and_fields(self):
        label = TextLabel(anchor=(0.5, 0.5, 0.5), text='Fe1')
        assert label.anchor == (0.5, 0.5, 0.5)
        assert label.text == 'Fe1'

    def test_frozen_rejects_mutation(self):
        label = TextLabel(anchor=ORIGIN, text='Fe1')
        with pytest.raises(dataclasses.FrozenInstanceError):
            label.text = 'O1'


# ------------------------------------------------------------------
#  LegendEntry
# ------------------------------------------------------------------


class TestLegendEntry:
    def test_construction_and_fields(self):
        entry = LegendEntry(symbol='Fe', colour=RED)
        assert entry.symbol == 'Fe'
        assert entry.colour == RED

    def test_frozen_rejects_mutation(self):
        entry = LegendEntry(symbol='Fe', colour=RED)
        with pytest.raises(dataclasses.FrozenInstanceError):
            entry.symbol = 'O'


# ------------------------------------------------------------------
#  StructureScene (the aggregate root)
# ------------------------------------------------------------------


class TestStructureScene:
    def test_minimal_construction_only_basis(self):
        scene = StructureScene(cell_basis=IDENTITY_BASIS)
        assert scene.cell_basis == IDENTITY_BASIS

    def test_collection_fields_default_empty(self):
        scene = StructureScene(cell_basis=IDENTITY_BASIS)
        assert scene.atoms == ()
        assert scene.occupancy_spheres == ()
        assert scene.ellipsoids == ()
        assert scene.bonds == ()
        assert scene.moments == ()
        assert scene.labels == ()
        assert scene.legend == ()

    def test_optional_singletons_default_none(self):
        scene = StructureScene(cell_basis=IDENTITY_BASIS)
        assert scene.cell_edges is None
        assert scene.axes is None

    def test_fully_populated_scene(self):
        atom = AtomSphere(centre=ORIGIN, radius=0.5, colour=RED, label='Fe')
        occ = OccupancyWedgeSphere(
            centre=(0.5, 0.5, 0.5),
            radius=0.6,
            wedges=(OccupancyWedge(fraction=1.0, colour=BLUE),),
            label='Mn',
        )
        ellipsoid = AdpEllipsoid(
            centre=(0.25, 0.25, 0.25),
            semi_axes=(0.1, 0.2, 0.3),
            orientation=IDENTITY_BASIS,
            colour=GREEN,
            label='O',
        )
        bond = Bond(start=ORIGIN, end=(0.5, 0.5, 0.5), start_colour=RED, end_colour=BLUE)
        moment = MomentArrow(origin=ORIGIN, vector=(0.0, 0.0, 1.0), colour=RED)
        cell_edges = CellEdges(edges=(CellEdge(start=ORIGIN, end=(1.0, 0.0, 0.0)),))
        axes = AxisTriad(
            origin=ORIGIN,
            axes=(
                AxisArrow(vector=(1.0, 0.0, 0.0), colour=RED, letter='a'),
                AxisArrow(vector=(0.0, 1.0, 0.0), colour=GREEN, letter='b'),
                AxisArrow(vector=(0.0, 0.0, 1.0), colour=BLUE, letter='c'),
            ),
        )
        label = TextLabel(anchor=ORIGIN, text='Fe1')
        legend = (LegendEntry(symbol='Fe', colour=RED),)

        scene = StructureScene(
            cell_basis=IDENTITY_BASIS,
            atoms=(atom,),
            occupancy_spheres=(occ,),
            ellipsoids=(ellipsoid,),
            bonds=(bond,),
            moments=(moment,),
            cell_edges=cell_edges,
            axes=axes,
            labels=(label,),
            legend=legend,
        )

        assert scene.atoms == (atom,)
        assert scene.occupancy_spheres == (occ,)
        assert scene.ellipsoids == (ellipsoid,)
        assert scene.bonds == (bond,)
        assert scene.moments == (moment,)
        assert scene.cell_edges is cell_edges
        assert scene.axes is axes
        assert scene.labels == (label,)
        assert scene.legend == legend

    def test_frozen_rejects_mutation(self):
        scene = StructureScene(cell_basis=IDENTITY_BASIS)
        with pytest.raises(dataclasses.FrozenInstanceError):
            scene.atoms = (AtomSphere(centre=ORIGIN, radius=1.0, colour=RED, label='Fe'),)

    def test_equality_by_value(self):
        a = StructureScene(cell_basis=IDENTITY_BASIS)
        b = StructureScene(cell_basis=IDENTITY_BASIS)
        assert a == b
