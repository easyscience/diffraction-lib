# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the ASCII single-cell structure renderer."""

from __future__ import annotations

import re

import numpy as np

from easydiffraction.display.structure.renderers import ascii as MUT
from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer
from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.scene import AdpEllipsoid
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import OccupancyWedge
from easydiffraction.display.structure.scene import OccupancyWedgeSphere
from easydiffraction.display.structure.scene import StructureScene

# ANSI escape sequence matcher used to strip colour tinting from output.
_ANSI = re.compile(r'\x1b\[[0-9;]*m')

# A cubic 5 Angstrom cell basis (rows are the cell vectors).
_CUBIC_BASIS = ((5.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 5.0))

ALL_FEATURES = frozenset({'atoms', 'cell', 'axes'})


def _strip_ansi(text: str) -> str:
    """Remove ANSI colour codes so glyphs can be asserted directly."""
    return _ANSI.sub('', text)


def _atom(centre=(0.0, 0.0, 0.0), radius=1.0, colour=(255, 0, 0), label='Fe'):
    return AtomSphere(centre=centre, radius=radius, colour=colour, label=label)


def _scene(atoms=(), occupancy_spheres=(), ellipsoids=(), basis=_CUBIC_BASIS):
    return StructureScene(
        cell_basis=basis,
        atoms=tuple(atoms),
        occupancy_spheres=tuple(occupancy_spheres),
        ellipsoids=tuple(ellipsoids),
    )


# ----------------------------------------------------------------------
#  Module + class basics
# ----------------------------------------------------------------------


def test_module_import():
    expected_module_name = 'easydiffraction.display.structure.renderers.ascii'
    assert MUT.__name__ == expected_module_name


def test_renderer_is_subclass_of_base():
    assert issubclass(AsciiStructureRenderer, StructureRendererBase)


def test_renderer_instantiates():
    assert AsciiStructureRenderer() is not None


def test_module_constants():
    assert MUT.GLYPH_RAMP == ('·', '•', '●')
    assert MUT.GRID_WIDTH == 56
    assert MUT.PAD == 2
    assert MUT.CHAR_ASPECT == 0.5


# ----------------------------------------------------------------------
#  supported_features
# ----------------------------------------------------------------------


def test_supported_features_value():
    renderer = AsciiStructureRenderer()
    assert renderer.supported_features() == frozenset({'atoms', 'cell', 'axes'})


def test_supported_features_matches_class_attribute():
    renderer = AsciiStructureRenderer()
    assert renderer.supported_features() is AsciiStructureRenderer.SUPPORTED


def test_supported_features_is_frozenset():
    assert isinstance(AsciiStructureRenderer().supported_features(), frozenset)


# ----------------------------------------------------------------------
#  render — feature gating
# ----------------------------------------------------------------------


def test_render_returns_str():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=ALL_FEATURES)
    assert isinstance(out, str)


def test_render_with_no_features_is_blank():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=frozenset())
    # No cell, no atoms, no axes: only whitespace rows remain.
    assert _strip_ansi(out).strip() == ''


def test_render_cell_only_draws_border_not_atoms():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=frozenset({'cell'}))
    plain = _strip_ansi(out)
    # Cell corners present, no legend (atoms feature is off).
    for corner in ('╭', '╮', '╰', '╯'):
        assert corner in plain
    assert 'Legend:' not in plain


def test_render_atoms_only_has_glyph_and_legend_but_no_border():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=frozenset({'atoms'}))
    plain = _strip_ansi(out)
    assert 'Legend:' in plain
    assert any(g in plain for g in MUT.GLYPH_RAMP)
    assert '╭' not in plain


def test_render_axes_only_adds_vertical_label():
    # With an empty body (no cell, no drawn atoms) only the vertical
    # axis header survives; the horizontal label needs a non-blank
    # bottom border row to attach to.
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[]), features=frozenset({'axes'}))
    plain = _strip_ansi(out)
    # Cubic cell: longest axis horizontal, second-longest (b) vertical.
    assert 'b' in plain
    assert '↑' in plain


def test_render_axes_with_atoms_adds_both_labels():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=frozenset({'atoms', 'axes'}))
    plain = _strip_ansi(out)
    assert '↑' in plain
    assert '→' in plain


def test_render_all_features_includes_border_atoms_axes_legend():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=ALL_FEATURES)
    plain = _strip_ansi(out)
    assert '╭' in plain
    assert any(g in plain for g in MUT.GLYPH_RAMP)
    assert '↑' in plain
    assert '→' in plain
    assert 'Legend:' in plain


def test_render_atoms_feature_without_atoms_skips_legend():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[]), features=ALL_FEATURES)
    plain = _strip_ansi(out)
    # Atoms requested but the scene has none: border + axes only.
    assert 'Legend:' not in plain
    assert '╭' in plain


def test_render_output_is_ansi_tinted():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom()]), features=ALL_FEATURES)
    # Coloured glyphs must carry ANSI escape codes.
    assert '\x1b[' in out


# ----------------------------------------------------------------------
#  render — scene primitive coverage
# ----------------------------------------------------------------------


def test_render_includes_atom_label_in_legend():
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(atoms=[_atom(label='Fe1')]), features=ALL_FEATURES)
    plain = _strip_ansi(out)
    # Digits are stripped from the legend element name.
    assert 'Fe' in plain
    assert 'Fe1' not in plain


def test_render_occupancy_sphere_uses_first_wedge_colour():
    sphere = OccupancyWedgeSphere(
        centre=(2.5, 2.5, 2.5),
        radius=1.2,
        wedges=(OccupancyWedge(0.6, (10, 20, 30)), OccupancyWedge(0.4, (40, 50, 60))),
        label='La/Ba',
    )
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(occupancy_spheres=[sphere]), features=ALL_FEATURES)
    plain = _strip_ansi(out)
    # The slash is preserved so a shared site reads 'La/Ba'.
    assert 'La/Ba' in plain
    assert 'Legend:' in plain


def test_render_ellipsoid_uses_mean_semi_axes():
    ellipsoid = AdpEllipsoid(
        centre=(1.0, 1.0, 1.0),
        semi_axes=(0.3, 0.5, 0.7),
        orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        colour=(0, 200, 0),
        label='O',
    )
    renderer = AsciiStructureRenderer()
    out = renderer.render(_scene(ellipsoids=[ellipsoid]), features=ALL_FEATURES)
    plain = _strip_ansi(out)
    assert 'O' in plain
    assert any(g in plain for g in MUT.GLYPH_RAMP)


def test_render_mixed_primitives_all_appear_in_legend():
    atoms = [_atom(centre=(0.0, 0.0, 0.0), label='Fe', colour=(255, 0, 0))]
    spheres = [
        OccupancyWedgeSphere(
            centre=(2.5, 2.5, 2.5),
            radius=1.0,
            wedges=(OccupancyWedge(1.0, (0, 0, 255)),),
            label='Na',
        )
    ]
    ellipsoids = [
        AdpEllipsoid(
            centre=(4.0, 4.0, 4.0),
            semi_axes=(0.4, 0.4, 0.4),
            orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            colour=(0, 255, 0),
            label='O',
        )
    ]
    renderer = AsciiStructureRenderer()
    out = renderer.render(
        _scene(atoms=atoms, occupancy_spheres=spheres, ellipsoids=ellipsoids),
        features=ALL_FEATURES,
    )
    plain = _strip_ansi(out)
    for element in ('Fe', 'Na', 'O'):
        assert element in plain


def test_render_axes_letters_track_axis_lengths():
    # Make c the longest axis and a the shortest; b stays second-longest.
    basis = ((2.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 9.0))
    renderer = AsciiStructureRenderer()
    out = renderer.render(
        _scene(atoms=[_atom()], basis=basis),
        features=frozenset({'atoms', 'axes'}),
    )
    plain = _strip_ansi(out)
    # Longest (c) horizontal, second-longest (b) vertical.
    assert '→ c' in plain
    assert 'b' in plain


# ----------------------------------------------------------------------
#  _collect_atoms
# ----------------------------------------------------------------------


def test_collect_atoms_flattens_every_primitive():
    sphere = OccupancyWedgeSphere(
        centre=(1.0, 1.0, 1.0),
        radius=0.9,
        wedges=(OccupancyWedge(1.0, (1, 2, 3)),),
        label='Na',
    )
    ellipsoid = AdpEllipsoid(
        centre=(2.0, 2.0, 2.0),
        semi_axes=(0.2, 0.4, 0.6),
        orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        colour=(4, 5, 6),
        label='O',
    )
    scene = _scene(atoms=[_atom(label='Fe')], occupancy_spheres=[sphere], ellipsoids=[ellipsoid])

    flattened = MUT._collect_atoms(scene)

    assert len(flattened) == 3
    labels = [item[3] for item in flattened]
    assert labels == ['Fe', 'Na', 'O']
    # Occupancy sphere inherits its first wedge colour.
    assert flattened[1][2] == (1, 2, 3)
    # Ellipsoid radius is the mean of its semi-axes.
    assert flattened[2][1] == np.mean((0.2, 0.4, 0.6))


def test_collect_atoms_ellipsoid_zero_mean_falls_back_to_default_radius():
    ellipsoid = AdpEllipsoid(
        centre=(0.0, 0.0, 0.0),
        semi_axes=(0.0, 0.0, 0.0),
        orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        colour=(7, 8, 9),
        label='X',
    )
    flattened = MUT._collect_atoms(_scene(ellipsoids=[ellipsoid]))
    assert flattened[0][1] == 0.4


def test_collect_atoms_empty_scene_returns_empty_list():
    assert MUT._collect_atoms(_scene()) == []


# ----------------------------------------------------------------------
#  _ansi256 / _tint
# ----------------------------------------------------------------------


def test_ansi256_black_and_white_bounds():
    assert MUT._ansi256((0, 0, 0)) == 16
    assert MUT._ansi256((255, 255, 255)) == 231


def test_ansi256_pure_red():
    # 16 + 36*5 = 196 for full-red, no green, no blue.
    assert MUT._ansi256((255, 0, 0)) == 196


def test_tint_wraps_text_in_escape_codes():
    tinted = MUT._tint((255, 0, 0), 'X')
    assert tinted.startswith('\x1b[38;5;196m')
    assert tinted.endswith('\x1b[0m')
    assert _strip_ansi(tinted) == 'X'


# ----------------------------------------------------------------------
#  _make_grid
# ----------------------------------------------------------------------


def test_make_grid_size_and_placement():
    points = [(0.0, 0.0), (10.0, 4.0)]
    grid, place = MUT._make_grid(points)
    height, width = grid['_size']
    assert width == MUT.GRID_WIDTH
    assert height >= 8
    # The extreme corners land within the padded interior.
    r0, c0 = place((0.0, 0.0))
    r1, c1 = place((10.0, 4.0))
    assert c0 == MUT.PAD
    assert MUT.PAD <= c1 <= width - 1
    # Higher y maps to a smaller row (top of the grid).
    assert r1 < r0


def test_make_grid_handles_empty_points():
    grid, place = MUT._make_grid([])
    height, width = grid['_size']
    assert width == MUT.GRID_WIDTH
    assert height >= 8
    # A degenerate span must not raise and should place at the origin pad.
    assert place((0.0, 0.0)) == (MUT.PAD, MUT.PAD)


def test_make_grid_handles_zero_span():
    # All points identical: span guards prevent division by zero.
    _grid, place = MUT._make_grid([(3.0, 3.0), (3.0, 3.0)])
    assert place((3.0, 3.0)) == (MUT.PAD, MUT.PAD)


# ----------------------------------------------------------------------
#  _draw_cell
# ----------------------------------------------------------------------


def test_draw_cell_writes_closed_rectangle_with_corners():
    corners = [(0.0, 0.0), (10.0, 0.0), (0.0, 4.0), (10.0, 4.0)]
    grid, place = MUT._make_grid(corners)
    MUT._draw_cell(grid, place, corners)
    glyphs = {cell: val[0] for cell, val in grid.items() if cell != '_size'}
    assert '╭' in glyphs.values()
    assert '╮' in glyphs.values()
    assert '╰' in glyphs.values()
    assert '╯' in glyphs.values()
    assert '─' in glyphs.values()
    assert '│' in glyphs.values()


def test_draw_cell_corner_overrides_border():
    corners = [(0.0, 0.0), (10.0, 0.0), (0.0, 4.0), (10.0, 4.0)]
    grid, place = MUT._make_grid(corners)
    MUT._draw_cell(grid, place, corners)
    cells = [place(c) for c in corners]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top_left = (min(rows), min(cols))
    # The shared corner cell is a corner glyph, never a straight edge.
    assert grid[top_left][0] == '╭'


# ----------------------------------------------------------------------
#  _draw_atoms
# ----------------------------------------------------------------------


def test_draw_atoms_places_glyph_by_radius_bucket():
    # Two atoms: the larger radius gets the densest glyph.
    atoms = [
        ((0.0, 0.0, 0.0), 0.2, (255, 0, 0), 'A'),
        ((10.0, 4.0, 0.0), 1.0, (0, 0, 255), 'B'),
    ]
    points = [(0.0, 0.0), (10.0, 4.0)]
    grid, place = MUT._make_grid(points)
    MUT._draw_atoms(grid, place, atoms)
    small = grid[place((0.0, 0.0))]
    large = grid[place((10.0, 4.0))]
    assert large[0] == '●'  # densest bucket for the largest radius
    assert MUT.GLYPH_RAMP.index(small[0]) <= MUT.GLYPH_RAMP.index(large[0])


def test_draw_atoms_skips_same_colour_duplicate_in_adjacent_cell():
    # Two same-colour atoms projecting to the same cell: only one drawn.
    atoms = [
        ((0.0, 0.0, 0.0), 1.0, (255, 0, 0), 'A'),
        ((0.0, 0.0, 0.0), 1.0, (255, 0, 0), 'A'),
    ]
    grid, place = MUT._make_grid([(0.0, 0.0)])
    MUT._draw_atoms(grid, place, atoms)
    drawn = [cell for cell in grid if cell != '_size']
    assert len(drawn) == 1


def test_draw_atoms_keeps_different_colour_in_same_cell():
    # Different colours are not treated as duplicates.
    atoms = [
        ((0.0, 0.0, 0.0), 1.0, (255, 0, 0), 'A'),
        ((0.0, 0.0, 0.0), 1.0, (0, 0, 255), 'B'),
    ]
    grid, place = MUT._make_grid([(0.0, 0.0)])
    MUT._draw_atoms(grid, place, atoms)
    drawn = [cell for cell in grid if cell != '_size']
    # Same cell, different colour: the second overwrites the first, but
    # it is not skipped as a duplicate (one occupied cell, last colour).
    assert len(drawn) == 1
    assert grid[place((0.0, 0.0))][1] == (0, 0, 255)


# ----------------------------------------------------------------------
#  _grid_to_lines
# ----------------------------------------------------------------------


def test_grid_to_lines_dimensions_and_blank_fill():
    grid = {'_size': (3, 6)}
    grid[0, 0] = ('●', (255, 0, 0))
    lines = MUT._grid_to_lines(grid)
    assert len(lines) == 3
    # Empty rows are right-stripped to the empty string.
    assert lines[1] == ''
    assert lines[2] == ''
    # The tinted glyph survives in the first row.
    assert '●' in _strip_ansi(lines[0])


def test_grid_to_lines_rstrips_trailing_blanks():
    grid = {'_size': (1, 10)}
    grid[0, 2] = ('•', (1, 2, 3))
    lines = MUT._grid_to_lines(grid)
    # Trailing blank cells past the glyph are removed.
    assert not lines[0].endswith(' ')


# ----------------------------------------------------------------------
#  _annotate_axes
# ----------------------------------------------------------------------


def test_annotate_axes_adds_vertical_header_and_horizontal_label():
    lines = ['row0', 'row1', 'row2']
    out = MUT._annotate_axes(lines, left_col=3, bottom_row=2, v_letter='b', h_letter='a')
    # Header: blank line, letter, arrow; all indented by left_col.
    assert out[0] == ''
    assert out[1] == '   b'
    assert out[2] == '   ↑'
    # Horizontal label appended to the bottom row.
    assert out[-1].endswith('→ a')


def test_annotate_axes_out_of_range_bottom_row_leaves_body_unchanged():
    lines = ['only']
    out = MUT._annotate_axes(lines, left_col=0, bottom_row=99, v_letter='c', h_letter='a')
    # Header still added, but no horizontal label since row is out of range.
    assert out[:3] == ['', 'c', '↑']
    assert out[3] == 'only'
    assert '→' not in out[3]


# ----------------------------------------------------------------------
#  _legend
# ----------------------------------------------------------------------


def test_legend_strips_digits_keeps_slash():
    atoms = [
        ((0.0, 0.0, 0.0), 1.0, (255, 0, 0), 'Fe1'),
        ((0.0, 0.0, 0.0), 1.0, (0, 0, 255), 'La/Ba'),
    ]
    legend = MUT._legend(atoms)
    plain = _strip_ansi(legend)
    assert plain.startswith('Legend:')
    assert 'Fe' in plain
    assert 'Fe1' not in plain
    assert 'La/Ba' in plain


def test_legend_deduplicates_by_element():
    atoms = [
        ((0.0, 0.0, 0.0), 1.0, (255, 0, 0), 'Fe1'),
        ((1.0, 1.0, 1.0), 1.0, (255, 0, 0), 'Fe2'),
    ]
    legend = MUT._legend(atoms)
    plain = _strip_ansi(legend)
    # Two Fe sites collapse to a single 'Fe' legend entry.
    assert plain.count('Fe') == 1


def test_legend_glyph_scales_with_radius():
    atoms = [
        ((0.0, 0.0, 0.0), 0.2, (255, 0, 0), 'H'),
        ((1.0, 1.0, 1.0), 1.0, (0, 0, 255), 'U'),
    ]
    legend = MUT._legend(atoms)
    plain = _strip_ansi(legend)
    # Largest radius element uses the densest glyph.
    assert '● U' in plain
    assert '· H' in plain or '• H' in plain


def test_legend_all_zero_radius_does_not_divide_by_zero():
    atoms = [((0.0, 0.0, 0.0), 0.0, (1, 2, 3), 'X')]
    legend = MUT._legend(atoms)
    plain = _strip_ansi(legend)
    assert 'X' in plain


def test_legend_label_with_no_alpha_falls_back_to_label():
    # A purely numeric label keeps the raw label (the 'or label' branch).
    atoms = [((0.0, 0.0, 0.0), 1.0, (1, 2, 3), '123')]
    legend = MUT._legend(atoms)
    plain = _strip_ansi(legend)
    assert '123' in plain
