# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/structure/builder.py (scene builder)."""

from __future__ import annotations

import numpy as np
import pytest

from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.display.structure import builder as MUT
from easydiffraction.display.structure.builder import ALL_FEATURES
from easydiffraction.display.structure.builder import FeatureAvailability
from easydiffraction.display.structure.builder import build_scene
from easydiffraction.display.structure.builder import structure_feature_availability
from easydiffraction.display.structure.enums import AtomViewEnum
from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.display.structure.scene import AdpEllipsoid
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import AxisTriad
from easydiffraction.display.structure.scene import Bond
from easydiffraction.display.structure.scene import CellEdges
from easydiffraction.display.structure.scene import LegendEntry
from easydiffraction.display.structure.scene import OccupancyWedgeSphere
from easydiffraction.display.structure.scene import StructureScene
from easydiffraction.display.structure.scene import TextLabel
from easydiffraction.project.categories.structure_style.default import StructureStyle

# A view range covering only the asymmetric unit (no lattice images),
# keeping P 1 scene-atom counts deterministic and equal to the number
# of in-range sites.
ASYMMETRIC_UNIT = ((0.0, 0.5), (0.0, 0.5), (0.0, 0.5))
# The full conventional cell; in P 1 the cell-corner lattice images of a
# site at the origin are deduplicated, so counts grow predictably.
FULL_CELL = ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0))


def _make_structure(name='test', *, space_group='P 1'):
    """Build a minimal cubic P 1 structure (no calculation engine)."""
    structure = Structure(name=name)
    structure.cell.length_a = 5.0
    structure.cell.length_b = 5.0
    structure.cell.length_c = 5.0
    structure.space_group.name_h_m = space_group
    return structure


def _add_atom(
    structure,
    *,
    label,
    type_symbol,
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    occupancy=1.0,
    adp_type='Biso',
    adp_iso=0.5,
):
    structure.atom_sites.create(
        label=label,
        type_symbol=type_symbol,
        fract_x=fract_x,
        fract_y=fract_y,
        fract_z=fract_z,
        occupancy=occupancy,
        adp_type=adp_type,
        adp_iso=adp_iso,
    )


def _two_atom_structure(name='two', *, view_positions=True):
    """Two distinct in-range sites (Fe + O) for bond/atom tests."""
    structure = _make_structure(name)
    offset = (0.1, 0.1, 0.1) if view_positions else (0.0, 0.0, 0.0)
    _add_atom(
        structure,
        label='Fe1',
        type_symbol='Fe',
        fract_x=offset[0],
        fract_y=offset[1],
        fract_z=offset[2],
    )
    _add_atom(
        structure,
        label='O1',
        type_symbol='O',
        fract_x=offset[0] + 0.2,
        fract_y=offset[1],
        fract_z=offset[2],
    )
    structure._sync_atom_site_aniso()
    return structure


def _anisotropic_structure(name='aniso'):
    """One anisotropic (Uani) Fe site with a non-spherical U tensor.

    Created isotropic first, then flipped to ``Uani`` on the existing
    site (the supported edit path) before the aniso components are set.
    """
    structure = _make_structure(name)
    _add_atom(
        structure,
        label='Fe1',
        type_symbol='Fe',
        fract_x=0.1,
        fract_y=0.1,
        fract_z=0.1,
        adp_type='Uiso',
        adp_iso=0.01,
    )
    structure.atom_sites['Fe1'].adp_type = 'Uani'
    structure._sync_atom_site_aniso()
    aniso = structure.atom_site_aniso['Fe1']
    aniso.adp_11 = 0.01
    aniso.adp_22 = 0.02
    aniso.adp_33 = 0.03
    return structure


# ======================================================================
#  Module import + public surface
# ======================================================================


class TestModule:
    def test_module_import(self):
        assert MUT.__name__ == 'easydiffraction.display.structure.builder'

    def test_all_features_constant(self):
        # The resolved feature names the facade can ask the builder for.
        assert set(ALL_FEATURES) == {'atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'}

    def test_all_features_is_tuple(self):
        # A stable, immutable ordering for UI listings.
        assert isinstance(ALL_FEATURES, tuple)


# ======================================================================
#  FeatureAvailability dataclass
# ======================================================================


class TestFeatureAvailability:
    def test_construction_and_fields(self):
        availability = FeatureAvailability(
            available=frozenset({'atoms', 'cell'}),
            radius_substitutions=('H', 'He'),
        )
        assert availability.available == frozenset({'atoms', 'cell'})
        assert availability.radius_substitutions == ('H', 'He')

    def test_is_frozen(self):
        availability = FeatureAvailability(available=frozenset(), radius_substitutions=())
        with pytest.raises((AttributeError, TypeError)):
            availability.available = frozenset({'atoms'})


# ======================================================================
#  structure_feature_availability
# ======================================================================


class TestStructureFeatureAvailability:
    def test_returns_feature_availability(self):
        structure = _two_atom_structure()
        result = structure_feature_availability(structure, style=StructureStyle())
        assert isinstance(result, FeatureAvailability)

    def test_populated_structure_supports_all_features(self):
        structure = _two_atom_structure()
        result = structure_feature_availability(structure, style=StructureStyle())
        assert result.available == frozenset({'atoms', 'bonds', 'cell', 'axes', 'labels'})

    def test_empty_structure_supports_only_cell_and_axes(self):
        # With no atom sites, only the cell box and axis triad are drawable.
        structure = _make_structure('empty')
        result = structure_feature_availability(structure, style=StructureStyle())
        assert result.available == frozenset({'cell', 'axes'})

    def test_no_substitutions_for_well_covered_elements(self):
        structure = _two_atom_structure()
        result = structure_feature_availability(structure, style=StructureStyle())
        assert result.radius_substitutions == ()

    def test_reports_ionic_substitution_for_hydrogen(self):
        # H has no ionic radius, so the ionic view falls back to covalent
        # and reports the substitution.
        structure = _make_structure('hydride')
        _add_atom(structure, label='H1', type_symbol='H', fract_x=0.1, fract_y=0.1, fract_z=0.1)
        structure._sync_atom_site_aniso()
        style = StructureStyle()
        style.atom_view = 'ionic'
        result = structure_feature_availability(structure, style=style)
        assert result.radius_substitutions == ('H',)

    def test_substitutions_sorted_and_deduplicated(self):
        # Two H atoms and one He atom under the ionic view -> one entry per
        # element, alphabetically sorted.
        structure = _make_structure('light')
        _add_atom(structure, label='H1', type_symbol='H', fract_x=0.1, fract_y=0.1, fract_z=0.1)
        _add_atom(structure, label='H2', type_symbol='H', fract_x=0.2, fract_y=0.2, fract_z=0.2)
        _add_atom(structure, label='He1', type_symbol='He', fract_x=0.3, fract_y=0.3, fract_z=0.3)
        structure._sync_atom_site_aniso()
        style = StructureStyle()
        style.atom_view = 'ionic'
        result = structure_feature_availability(structure, style=style)
        assert result.radius_substitutions == ('H', 'He')


# ======================================================================
#  build_scene — return type and cell basis
# ======================================================================


class TestBuildSceneBasics:
    def test_returns_structure_scene(self):
        scene = build_scene(
            _two_atom_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset(ALL_FEATURES),
        )
        assert isinstance(scene, StructureScene)

    def test_cell_basis_matches_cubic_cell(self):
        scene = build_scene(
            _two_atom_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset(),
        )
        # Cubic 5 angstrom cell -> orthogonal basis with 5 on the diagonal.
        basis = np.array(scene.cell_basis)
        assert np.allclose(basis, np.diag([5.0, 5.0, 5.0]), atol=1e-6)


# ======================================================================
#  build_scene — feature gating
# ======================================================================


class TestBuildSceneFeatureGating:
    def _scene(self, features):
        return build_scene(
            _two_atom_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset(features),
        )

    def test_empty_features_emits_nothing_drawable(self):
        scene = self._scene(frozenset())
        assert scene.atoms == ()
        assert scene.occupancy_spheres == ()
        assert scene.ellipsoids == ()
        assert scene.bonds == ()
        assert scene.labels == ()
        assert scene.legend == ()
        assert scene.cell_edges is None
        assert scene.axes is None
        # cell_basis is always present regardless of features.
        assert scene.cell_basis is not None

    def test_atoms_feature_emits_atoms_and_legend(self):
        scene = self._scene({'atoms'})
        assert len(scene.atoms) == 2
        assert len(scene.legend) == 2
        # No other features requested.
        assert scene.bonds == ()
        assert scene.cell_edges is None
        assert scene.axes is None
        assert scene.labels == ()

    def test_legend_omitted_without_atoms_feature(self):
        scene = self._scene({'cell'})
        assert scene.legend == ()

    def test_bonds_feature_emits_bonds(self):
        scene = self._scene({'atoms', 'bonds'})
        assert len(scene.bonds) == 1

    def test_bonds_omitted_without_bonds_feature(self):
        scene = self._scene({'atoms'})
        assert scene.bonds == ()

    def test_cell_feature_emits_twelve_edges(self):
        scene = self._scene({'cell'})
        assert isinstance(scene.cell_edges, CellEdges)
        assert len(scene.cell_edges.edges) == 12

    def test_axes_feature_emits_triad(self):
        scene = self._scene({'axes'})
        assert isinstance(scene.axes, AxisTriad)
        assert len(scene.axes.axes) == 3

    def test_labels_feature_emits_one_label_per_atom(self):
        scene = self._scene({'labels'})
        assert len(scene.labels) == 2
        assert all(isinstance(label, TextLabel) for label in scene.labels)

    def test_full_features_emit_every_section(self):
        scene = self._scene(ALL_FEATURES)
        assert len(scene.atoms) == 2
        assert len(scene.bonds) == 1
        assert len(scene.labels) == 2
        assert len(scene.legend) == 2
        assert scene.cell_edges is not None
        assert scene.axes is not None


# ======================================================================
#  build_scene — atom primitives
# ======================================================================


class TestBuildSceneAtomPrimitives:
    def test_ball_view_emits_atom_spheres(self):
        style = StructureStyle()
        style.atom_view = 'vdw'
        scene = build_scene(
            _two_atom_structure(),
            style=style,
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        assert all(isinstance(atom, AtomSphere) for atom in scene.atoms)
        assert all(atom.radius > 0.0 for atom in scene.atoms)
        assert scene.ellipsoids == ()

    def test_atom_scale_grows_ball_radius(self):
        small = StructureStyle()
        small.atom_view = 'vdw'
        small.atom_scale = 0.2
        large = StructureStyle()
        large.atom_view = 'vdw'
        large.atom_scale = 0.8
        structure = _two_atom_structure()
        scene_small = build_scene(
            structure, style=small, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        scene_large = build_scene(
            structure, style=large, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        assert scene_large.atoms[0].radius > scene_small.atoms[0].radius

    def test_adp_view_anisotropic_atom_emits_ellipsoid(self):
        structure = _anisotropic_structure()
        style = StructureStyle()
        style.atom_view = 'adp'
        scene = build_scene(
            structure, style=style, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        assert len(scene.ellipsoids) == 1
        assert scene.atoms == ()
        ellipsoid = scene.ellipsoids[0]
        assert isinstance(ellipsoid, AdpEllipsoid)
        assert all(axis > 0.0 for axis in ellipsoid.semi_axes)

    def test_adp_probability_scales_ellipsoid_size(self):
        structure = _anisotropic_structure()
        low = StructureStyle()
        low.atom_view = 'adp'
        low.adp_probability = 0.5
        high = StructureStyle()
        high.atom_view = 'adp'
        high.adp_probability = 0.99
        scene_low = build_scene(
            structure, style=low, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        scene_high = build_scene(
            structure, style=high, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        # Higher probability -> larger principal semi-axes.
        assert scene_high.ellipsoids[0].semi_axes[0] > scene_low.ellipsoids[0].semi_axes[0]

    def test_reference_atom_marked_asymmetric(self):
        # The atom at the asymmetric-unit reference position is flagged so
        # renderers can offer an asymmetric-unit-only toggle.
        structure = _two_atom_structure()
        scene = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        assert any(atom.asymmetric for atom in scene.atoms)


# ======================================================================
#  build_scene — mixed-occupancy (wedge) sites
# ======================================================================


class TestBuildSceneOccupancyWedges:
    def _shared_site_structure(self):
        structure = _make_structure('mixed')
        _add_atom(
            structure,
            label='Fe1',
            type_symbol='Fe',
            fract_x=0.1,
            fract_y=0.1,
            fract_z=0.1,
            occupancy=0.6,
        )
        _add_atom(
            structure,
            label='Mn1',
            type_symbol='Mn',
            fract_x=0.1,
            fract_y=0.1,
            fract_z=0.1,
            occupancy=0.4,
        )
        structure._sync_atom_site_aniso()
        return structure

    def test_shared_site_emits_occupancy_wedge_sphere(self):
        style = StructureStyle()
        style.atom_view = 'vdw'
        scene = build_scene(
            self._shared_site_structure(),
            style=style,
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        assert scene.atoms == ()
        assert len(scene.occupancy_spheres) == 1
        assert isinstance(scene.occupancy_spheres[0], OccupancyWedgeSphere)

    def test_wedge_label_joins_member_labels(self):
        scene = build_scene(
            self._shared_site_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        sphere = scene.occupancy_spheres[0]
        assert sphere.label == 'Fe1/Mn1'

    def test_wedges_use_relative_proportions(self):
        scene = build_scene(
            self._shared_site_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        fractions = [wedge.fraction for wedge in scene.occupancy_spheres[0].wedges]
        assert pytest.approx(sum(fractions), abs=1e-9) == 1.0
        assert pytest.approx(fractions[0], abs=1e-9) == 0.6
        assert pytest.approx(fractions[1], abs=1e-9) == 0.4


# ======================================================================
#  build_scene — bonds
# ======================================================================


class TestBuildSceneBonds:
    def test_single_atom_has_no_bonds(self):
        structure = _make_structure('single')
        _add_atom(structure, label='Fe1', type_symbol='Fe', fract_x=0.1, fract_y=0.1, fract_z=0.1)
        structure._sync_atom_site_aniso()
        scene = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'bonds'}),
        )
        assert scene.bonds == ()

    def test_close_atoms_bond(self):
        scene = build_scene(
            _two_atom_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'bonds'}),
        )
        assert len(scene.bonds) == 1
        bond = scene.bonds[0]
        assert isinstance(bond, Bond)
        assert {bond.start_element, bond.end_element} == {'Fe', 'O'}

    def test_min_distance_cutoff_suppresses_bond(self):
        # Raising the minimum bonded distance above the actual Fe-O
        # distance removes the bond.
        structure = _two_atom_structure()
        structure.geom.min_bond_distance_cutoff = 5.0
        scene = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'bonds'}),
        )
        assert scene.bonds == ()

    def test_bond_distance_incr_enables_distant_bond(self):
        # Two atoms 2.5 angstrom apart (beyond summed covalent radii)
        # bond only once the increment is generous enough.
        structure = _make_structure('stretch')
        _add_atom(structure, label='Fe1', type_symbol='Fe', fract_x=0.0, fract_y=0.0, fract_z=0.0)
        _add_atom(structure, label='Fe2', type_symbol='Fe', fract_x=0.5, fract_y=0.0, fract_z=0.0)
        structure._sync_atom_site_aniso()

        structure.geom.bond_distance_incr = 0.0
        scene_tight = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'bonds'}),
        )

        structure.geom.bond_distance_incr = 5.0
        scene_loose = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'bonds'}),
        )

        assert len(scene_loose.bonds) >= len(scene_tight.bonds)
        assert len(scene_loose.bonds) >= 1


# ======================================================================
#  build_scene — colour scheme + legend
# ======================================================================


class TestBuildSceneColours:
    def test_legend_has_one_entry_per_element(self):
        scene = build_scene(
            _two_atom_structure(),
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        symbols = [entry.symbol for entry in scene.legend]
        assert symbols == ['Fe', 'O']
        assert all(isinstance(entry, LegendEntry) for entry in scene.legend)

    def test_colour_scheme_changes_atom_colour(self):
        structure = _two_atom_structure()
        jmol = StructureStyle()
        jmol.atom_view = 'vdw'
        jmol.color_scheme = 'jmol'
        vesta = StructureStyle()
        vesta.atom_view = 'vdw'
        vesta.color_scheme = 'vesta'
        scene_jmol = build_scene(
            structure, style=jmol, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        scene_vesta = build_scene(
            structure, style=vesta, view_range=ASYMMETRIC_UNIT, features=frozenset({'atoms'})
        )
        jmol_colours = {atom.label: atom.colour for atom in scene_jmol.atoms}
        vesta_colours = {atom.label: atom.colour for atom in scene_vesta.atoms}
        # At least one element is coloured differently between schemes.
        assert jmol_colours != vesta_colours


# ======================================================================
#  build_scene — symmetry expansion
# ======================================================================


class TestBuildSceneSymmetry:
    def test_higher_symmetry_generates_more_atoms(self):
        # The same single site expands to more scene atoms under a
        # higher-symmetry space group than under P 1.
        p1 = _make_structure('p1', space_group='P 1')
        _add_atom(p1, label='Fe1', type_symbol='Fe', fract_x=0.3, fract_y=0.1, fract_z=0.2)
        p1._sync_atom_site_aniso()
        scene_p1 = build_scene(
            p1, style=StructureStyle(), view_range=FULL_CELL, features=frozenset({'atoms'})
        )

        cubic = _make_structure('cubic', space_group='P m -3 m')
        _add_atom(cubic, label='Fe1', type_symbol='Fe', fract_x=0.3, fract_y=0.1, fract_z=0.2)
        cubic._sync_atom_site_aniso()
        scene_cubic = build_scene(
            cubic, style=StructureStyle(), view_range=FULL_CELL, features=frozenset({'atoms'})
        )

        n_cubic = (
            len(scene_cubic.atoms)
            + len(scene_cubic.occupancy_spheres)
            + len(scene_cubic.ellipsoids)
        )
        n_p1 = len(scene_p1.atoms) + len(scene_p1.occupancy_spheres) + len(scene_p1.ellipsoids)
        assert n_cubic > n_p1

    def test_p1_emits_one_atom_per_in_range_site(self):
        # In P 1 the only operator is the identity, so within the
        # asymmetric-unit range each site yields exactly one scene atom.
        structure = _make_structure('p1', space_group='P 1')
        _add_atom(structure, label='Fe1', type_symbol='Fe', fract_x=0.1, fract_y=0.1, fract_z=0.1)
        _add_atom(structure, label='O1', type_symbol='O', fract_x=0.3, fract_y=0.2, fract_z=0.2)
        structure._sync_atom_site_aniso()
        scene = build_scene(
            structure,
            style=StructureStyle(),
            view_range=ASYMMETRIC_UNIT,
            features=frozenset({'atoms'}),
        )
        assert len(scene.atoms) == 2


# ======================================================================
#  Value selectors (EnumDescriptor.show_supported) driving the builder
# ======================================================================


class TestValueSelectors:
    def test_atom_view_show_supported_lists_all_values(self, capsys):
        StructureStyle().atom_view.show_supported()
        out = capsys.readouterr().out
        for member in AtomViewEnum:
            assert member.value in out

    def test_color_scheme_show_supported_lists_all_values(self, capsys):
        StructureStyle().color_scheme.show_supported()
        out = capsys.readouterr().out
        for member in ColorSchemeEnum:
            assert member.value in out

    def test_atom_view_enum_backing(self):
        # The selector is bound to the closed AtomViewEnum value set.
        assert StructureStyle().atom_view.enum is AtomViewEnum

    def test_color_scheme_enum_backing(self):
        assert StructureStyle().color_scheme.enum is ColorSchemeEnum


# ======================================================================
#  StructureStyle wiring (the style object the builder reads)
# ======================================================================


class TestStructureStyleInputs:
    def test_default_atom_view_is_covalent(self):
        assert StructureStyle().atom_view.value == AtomViewEnum.COVALENT.value

    def test_default_color_scheme_is_jmol(self):
        assert StructureStyle().color_scheme.value == ColorSchemeEnum.JMOL.value

    def test_atom_view_cif_handler_name(self):
        assert StructureStyle().atom_view._cif_handler.names == ['_structure_style.atom_view']

    def test_color_scheme_cif_handler_name(self):
        assert StructureStyle().color_scheme._cif_handler.names == [
            '_structure_style.color_scheme'
        ]

    def test_invalid_atom_view_rejected(self):
        with pytest.raises(ValueError, match='not a valid AtomViewEnum'):
            StructureStyle().atom_view = 'not-a-view'

    def test_invalid_color_scheme_rejected(self):
        with pytest.raises(ValueError, match='not a valid ColorSchemeEnum'):
            StructureStyle().color_scheme = 'not-a-scheme'


# ======================================================================
#  Pure helper functions (load-bearing for element/colour mapping)
# ======================================================================


class TestHelpers:
    @pytest.mark.parametrize(
        ('type_symbol', 'expected'),
        [
            ('Fe', 'Fe'),
            ('Fe3+', 'Fe'),
            ('O2-', 'O'),
            ('Cl', 'Cl'),
            ('  Na+ ', 'Na'),
        ],
    )
    def test_element_symbol_extraction(self, type_symbol, expected):
        assert MUT._element_symbol(type_symbol) == expected

    def test_vec3_casts_to_float_tuple(self):
        result = MUT._vec3(np.array([1, 2, 3]))
        assert result == (1.0, 2.0, 3.0)
        assert all(isinstance(component, float) for component in result)


def test_reciprocal_lengths_matches_shared_crystallography_helper():
    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    structure = Structure(name='test')
    structure.cell.length_a = 5.0
    structure.cell.length_b = 6.0
    structure.cell.length_c = 8.0

    got = MUT._reciprocal_lengths(structure.cell)
    expected = reciprocal_cell_lengths(5.0, 6.0, 8.0, 90.0, 90.0, 90.0)

    assert np.allclose(got, expected)
    assert np.isclose(got[0], 1.0 / 5.0)
