# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the z-buffered raster structure renderer."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from easydiffraction.display.structure.renderers.raster import RasterStructureRenderer
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

# The 8-byte PNG file signature.
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'

# A simple orthogonal 5x5x5 cell shared by most scenes.
CUBIC_BASIS = ((5.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 5.0))


def _open(png: bytes) -> Image.Image:
    """Decode rendered PNG bytes into a Pillow image."""
    return Image.open(io.BytesIO(png))


def _pixels(png: bytes) -> np.ndarray:
    """Return the rendered image as an (H, W, 3) uint8 array."""
    return np.asarray(_open(png))


def _has_drawn_pixels(png: bytes) -> bool:
    """True when any pixel departs from the white background."""
    return bool((_pixels(png) != 255).any())


def _atom_scene() -> StructureScene:
    """A single red atom centred in the cubic cell."""
    return StructureScene(
        cell_basis=CUBIC_BASIS,
        atoms=(AtomSphere(centre=(0.0, 0.0, 0.0), radius=1.0, colour=(255, 0, 0), label='Fe'),),
    )


def _axis_triad() -> AxisTriad:
    """An a/b/c axis triad along the cubic cell edges."""
    return AxisTriad(
        origin=(0.0, 0.0, 0.0),
        axes=(
            AxisArrow(vector=(5.0, 0.0, 0.0), colour=(255, 0, 0), letter='a'),
            AxisArrow(vector=(0.0, 5.0, 0.0), colour=(0, 255, 0), letter='b'),
            AxisArrow(vector=(0.0, 0.0, 5.0), colour=(0, 0, 255), letter='c'),
        ),
    )


def _full_scene() -> StructureScene:
    """A scene exercising every supported primitive plus a legend."""
    return StructureScene(
        cell_basis=CUBIC_BASIS,
        atoms=(
            AtomSphere(centre=(0.0, 0.0, 0.0), radius=0.8, colour=(255, 0, 0), label='Fe'),
            AtomSphere(centre=(5.0, 5.0, 5.0), radius=0.8, colour=(0, 0, 255), label='O'),
        ),
        occupancy_spheres=(
            OccupancyWedgeSphere(
                centre=(2.5, 2.5, 2.5),
                radius=0.7,
                wedges=(
                    OccupancyWedge(fraction=0.5, colour=(255, 0, 0)),
                    OccupancyWedge(fraction=0.5, colour=(0, 255, 0)),
                ),
                label='Mix',
            ),
        ),
        ellipsoids=(
            AdpEllipsoid(
                centre=(1.0, 1.0, 1.0),
                semi_axes=(0.5, 0.4, 0.3),
                orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                colour=(0, 200, 0),
                label='Ell',
            ),
        ),
        bonds=(
            Bond(
                start=(0.0, 0.0, 0.0),
                end=(5.0, 5.0, 5.0),
                start_colour=(255, 0, 0),
                end_colour=(0, 0, 255),
            ),
        ),
        cell_edges=CellEdges(
            edges=(
                CellEdge(start=(0.0, 0.0, 0.0), end=(5.0, 0.0, 0.0)),
                CellEdge(start=(0.0, 0.0, 0.0), end=(0.0, 5.0, 0.0)),
                CellEdge(start=(0.0, 0.0, 0.0), end=(0.0, 0.0, 5.0)),
            )
        ),
        axes=_axis_triad(),
        legend=(
            LegendEntry(symbol='Fe', colour=(255, 0, 0)),
            LegendEntry(symbol='O', colour=(0, 0, 255)),
        ),
    )


def test_module_import():
    import easydiffraction.display.structure.renderers.raster as MUT

    expected_module_name = 'easydiffraction.display.structure.renderers.raster'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestSupported:
    def test_supported_is_frozenset(self):
        assert isinstance(RasterStructureRenderer.SUPPORTED, frozenset)

    def test_supported_members(self):
        assert frozenset({'atoms', 'bonds', 'cell', 'axes'}) == RasterStructureRenderer.SUPPORTED

    def test_supported_shared_across_instances(self):
        # SUPPORTED is a class-level constant, not rebuilt per instance.
        assert RasterStructureRenderer().SUPPORTED is RasterStructureRenderer.SUPPORTED


class TestConstruction:
    def test_instantiation(self):
        renderer = RasterStructureRenderer()
        assert renderer is not None

    def test_render_png_is_callable(self):
        assert callable(RasterStructureRenderer().render_png)


class TestRenderPngOutput:
    def test_returns_bytes(self):
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert isinstance(png, bytes)

    def test_has_png_signature(self):
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert png[:8] == PNG_MAGIC

    def test_decodes_as_png(self):
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert _open(png).format == 'PNG'

    def test_canvas_dimensions(self):
        # The supersampled buffer is downsampled to a fixed 1800x1800 frame.
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert _open(png).size == (1800, 1800)

    def test_rgb_mode(self):
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert _open(png).mode == 'RGB'

    def test_deterministic_for_same_scene(self):
        scene = _atom_scene()
        first = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        second = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        assert first == second


class TestRenderPngFeatures:
    def test_atom_is_drawn(self):
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert _has_drawn_pixels(png)

    def test_empty_scene_is_blank(self):
        # No primitives and no features -> a pristine white canvas.
        scene = StructureScene(cell_basis=CUBIC_BASIS)
        png = RasterStructureRenderer().render_png(scene, features=frozenset())
        assert bool((_pixels(png) == 255).all())

    def test_feature_gating_skips_unrequested_atoms(self):
        # The scene has an atom, but 'atoms' is absent from the feature
        # set, so nothing is drawn.
        scene = _atom_scene()
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'cell'}))
        assert bool((_pixels(png) == 255).all())

    def test_unknown_feature_names_are_ignored(self):
        # Feature names outside SUPPORTED never trigger a draw and never
        # raise; only 'atoms' here does any work.
        scene = _atom_scene()
        png = RasterStructureRenderer().render_png(
            scene, features=frozenset({'atoms', 'bogus', 'labels', 'moments'})
        )
        assert _has_drawn_pixels(png)

    def test_cell_only_is_drawn(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            cell_edges=CellEdges(edges=(CellEdge(start=(0.0, 0.0, 0.0), end=(5.0, 0.0, 0.0)),)),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'cell'}))
        assert _has_drawn_pixels(png)

    def test_bonds_only_is_drawn(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            bonds=(
                Bond(
                    start=(0.0, 0.0, 0.0),
                    end=(5.0, 5.0, 5.0),
                    start_colour=(255, 0, 0),
                    end_colour=(0, 0, 255),
                ),
            ),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'bonds'}))
        assert _has_drawn_pixels(png)

    def test_axes_only_is_drawn(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            atoms=(AtomSphere(centre=(0.0, 0.0, 0.0), radius=1.0, colour=(0, 0, 0), label='X'),),
            axes=_axis_triad(),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'axes'}))
        assert _has_drawn_pixels(png)

    def test_axes_feature_without_triad_is_blank(self):
        # 'axes' requested but scene.axes is None -> no crash, blank.
        scene = StructureScene(cell_basis=CUBIC_BASIS)
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'axes'}))
        assert bool((_pixels(png) == 255).all())

    def test_cell_feature_without_edges_is_blank(self):
        # 'cell' requested but scene.cell_edges is None -> no crash.
        scene = StructureScene(cell_basis=CUBIC_BASIS)
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'cell'}))
        assert bool((_pixels(png) == 255).all())

    def test_full_scene_renders(self):
        png = RasterStructureRenderer().render_png(
            _full_scene(), features=RasterStructureRenderer.SUPPORTED
        )
        assert png[:8] == PNG_MAGIC
        assert _open(png).size == (1800, 1800)
        assert _has_drawn_pixels(png)


class TestRenderPngPrimitives:
    def test_occupancy_wedge_sphere_renders(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            occupancy_spheres=(
                OccupancyWedgeSphere(
                    centre=(2.5, 2.5, 2.5),
                    radius=1.0,
                    wedges=(
                        OccupancyWedge(fraction=0.6, colour=(255, 0, 0)),
                        OccupancyWedge(fraction=0.4, colour=(0, 0, 255)),
                    ),
                    label='Mix',
                ),
            ),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        assert _has_drawn_pixels(png)

    def test_ellipsoid_renders(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            ellipsoids=(
                AdpEllipsoid(
                    centre=(2.5, 2.5, 2.5),
                    semi_axes=(1.0, 0.6, 0.4),
                    orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    colour=(0, 200, 0),
                    label='Ell',
                ),
            ),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        assert _has_drawn_pixels(png)

    def test_ellipsoid_with_wedges_renders(self):
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            ellipsoids=(
                AdpEllipsoid(
                    centre=(2.5, 2.5, 2.5),
                    semi_axes=(1.0, 1.0, 1.0),
                    orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    colour=(0, 200, 0),
                    label='Ell',
                    wedges=(
                        OccupancyWedge(fraction=0.5, colour=(255, 0, 0)),
                        OccupancyWedge(fraction=0.5, colour=(0, 0, 255)),
                    ),
                ),
            ),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        assert _has_drawn_pixels(png)

    def test_tiny_atom_is_skipped_without_error(self):
        # A sub-pixel radius atom is dropped by the minimum-size guard;
        # the larger atom still renders and the call succeeds.
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            atoms=(
                AtomSphere(centre=(0.0, 0.0, 0.0), radius=1.0, colour=(255, 0, 0), label='Fe'),
                AtomSphere(centre=(5.0, 5.0, 5.0), radius=1e-6, colour=(0, 0, 255), label='O'),
            ),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset({'atoms'}))
        assert png[:8] == PNG_MAGIC
        assert _has_drawn_pixels(png)


class TestLegend:
    def test_legend_is_drawn_independent_of_features(self):
        # The legend panel is composited regardless of the feature set
        # (it is not gated by 'atoms'/'bonds'/...).
        scene = StructureScene(
            cell_basis=CUBIC_BASIS,
            legend=(LegendEntry(symbol='Fe', colour=(255, 0, 0)),),
        )
        png = RasterStructureRenderer().render_png(scene, features=frozenset())
        assert _has_drawn_pixels(png)

    def test_no_legend_leaves_top_left_white(self):
        # Without a legend, the empty scene stays fully white.
        scene = StructureScene(cell_basis=CUBIC_BASIS)
        png = RasterStructureRenderer().render_png(scene, features=frozenset())
        assert bool((_pixels(png) == 255).all())


class TestViewBasis:
    def test_anisotropic_cell_renders(self):
        # An 8x5x3 cell drives the longest/middle/shortest axis ordering
        # in the default-view basis selection.
        scene = StructureScene(
            cell_basis=((8.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 3.0)),
            atoms=(
                AtomSphere(centre=(4.0, 2.5, 1.5), radius=1.0, colour=(10, 20, 30), label='X'),
            ),
            axes=AxisTriad(
                origin=(0.0, 0.0, 0.0),
                axes=(
                    AxisArrow(vector=(8.0, 0.0, 0.0), colour=(255, 0, 0), letter='a'),
                    AxisArrow(vector=(0.0, 5.0, 0.0), colour=(0, 255, 0), letter='b'),
                    AxisArrow(vector=(0.0, 0.0, 3.0), colour=(0, 0, 255), letter='c'),
                ),
            ),
        )
        png = RasterStructureRenderer().render_png(
            scene, features=RasterStructureRenderer.SUPPORTED
        )
        assert png[:8] == PNG_MAGIC
        assert _has_drawn_pixels(png)

    def test_scene_without_axes_uses_default_basis(self):
        # No axis triad -> the fixed fallback camera basis is used; the
        # atom still renders.
        png = RasterStructureRenderer().render_png(_atom_scene(), features=frozenset({'atoms'}))
        assert _has_drawn_pixels(png)


class TestRenderPngSignature:
    def test_features_is_keyword_only(self):
        # render_png(scene, *, features=...) — passing features
        # positionally is a TypeError.
        with pytest.raises(TypeError):
            RasterStructureRenderer().render_png(
                StructureScene(cell_basis=CUBIC_BASIS), frozenset()
            )

    def test_features_is_required(self):
        # Omitting the keyword-only 'features' argument is a TypeError.
        with pytest.raises(TypeError):
            RasterStructureRenderer().render_png(StructureScene(cell_basis=CUBIC_BASIS))
