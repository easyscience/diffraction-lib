# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the Three.js structure renderer."""

from __future__ import annotations

import json

import pytest

from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.display.structure.renderers import threejs as MUT
from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.renderers.threejs import ThreeJsStructureRenderer
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

# A representative theme palette returned by the patched ``theme_colors``.
_PATCHED_THEME = {'background': (10, 20, 30), 'foreground': (240, 240, 240)}

# Identity cell basis shared by the lightweight scenes below.
_IDENTITY_BASIS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _identity_scene() -> StructureScene:
    """Return the minimal valid scene (only a cell basis)."""
    return StructureScene(cell_basis=_IDENTITY_BASIS)


def _rich_scene() -> StructureScene:
    """Return a scene exercising every primitive the payload reads."""
    atom = AtomSphere(
        centre=(0.0, 0.0, 0.0),
        radius=0.5,
        colour=(255, 0, 0),
        label='Fe',
        asymmetric=True,
    )
    wedge_sphere = OccupancyWedgeSphere(
        centre=(0.5, 0.5, 0.5),
        radius=0.4,
        wedges=(
            OccupancyWedge(fraction=0.6, colour=(0, 0, 255)),
            OccupancyWedge(fraction=0.4, colour=(210, 210, 210)),
        ),
        label='La/Ba',
    )
    ellipsoid = AdpEllipsoid(
        centre=(0.25, 0.25, 0.25),
        semi_axes=(0.3, 0.2, 0.1),
        orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        colour=(0, 255, 0),
        label='O',
        wedges=(OccupancyWedge(fraction=1.0, colour=(0, 255, 0)),),
        asymmetric=True,
    )
    bond = Bond(
        start=(0.0, 0.0, 0.0),
        end=(0.5, 0.5, 0.5),
        start_colour=(255, 0, 0),
        end_colour=(0, 0, 255),
        start_element='Fe',
        end_element='O',
    )
    edges = CellEdges(
        edges=(
            CellEdge(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
            CellEdge(start=(0.0, 0.0, 0.0), end=(0.0, 1.0, 0.0)),
        ),
    )
    axes = AxisTriad(
        origin=(0.0, 0.0, 0.0),
        axes=(
            AxisArrow(vector=(1.0, 0.0, 0.0), colour=(220, 40, 40), letter='a'),
            AxisArrow(vector=(0.0, 1.0, 0.0), colour=(40, 180, 40), letter='b'),
            AxisArrow(vector=(0.0, 0.0, 1.0), colour=(40, 80, 220), letter='c'),
        ),
    )
    return StructureScene(
        cell_basis=_IDENTITY_BASIS,
        atoms=(atom,),
        occupancy_spheres=(wedge_sphere,),
        ellipsoids=(ellipsoid,),
        bonds=(bond,),
        cell_edges=edges,
        axes=axes,
        labels=(TextLabel(anchor=(0.1, 0.2, 0.3), text='Fe1'),),
        legend=(
            LegendEntry(symbol='Fe', colour=(255, 0, 0)),
            LegendEntry(symbol='O', colour=(0, 255, 0)),
        ),
    )


@pytest.fixture
def patched_theme(monkeypatch):
    """Patch the module-level ``theme_colors`` to a fixed test palette.

    Isolates the renderer's own templating logic from the concrete
    ``LIGHT_THEME``/``DARK_THEME`` values so the happy-path assertions
    below depend only on the renderer. The un-patched integration with
    the real ``theme_colors`` is covered by
    :class:`TestRenderUnpatchedIntegration`.
    """
    monkeypatch.setattr(MUT, 'theme_colors', lambda *, dark: dict(_PATCHED_THEME))


def test_module_import():
    import easydiffraction.display.structure.renderers.threejs as imported

    expected_module_name = 'easydiffraction.display.structure.renderers.threejs'
    assert imported.__name__ == expected_module_name


# ------------------------------------------------------------------
#  Module-level constants
# ------------------------------------------------------------------


class TestModuleConstants:
    def test_cdn_pins_three_version(self):
        assert MUT._CDN == 'https://cdn.jsdelivr.net/npm/three@0.160.0'

    def test_addon_specifiers(self):
        assert MUT._ADDON_CONTROLS == 'three/addons/controls/OrbitControls.js'
        assert MUT._ADDON_CSS2D == 'three/addons/renderers/CSS2DRenderer.js'

    def test_vendor_dir_points_at_threejs_assets(self):
        assert MUT._VENDOR.name == 'threejs'
        assert MUT._VENDOR.parent.name == 'vendor'

    def test_vendor_dir_holds_pinned_assets(self):
        # The offline import map inlines these three vendored files.
        names = {p.name for p in MUT._VENDOR.iterdir()}
        assert {'three.module.js', 'OrbitControls.js', 'CSS2DRenderer.js'} <= names


# ------------------------------------------------------------------
#  _environment
# ------------------------------------------------------------------


class TestEnvironment:
    def test_returns_jinja_environment(self):
        from jinja2 import Environment

        assert isinstance(MUT._environment(), Environment)

    def test_autoescape_disabled_for_html_payload(self):
        # The payload is pre-escaped JSON; Jinja must not re-escape it.
        env = MUT._environment()
        assert env.trim_blocks is True
        assert env.lstrip_blocks is True

    def test_can_load_structure_template(self):
        env = MUT._environment()
        template = env.get_template(ThreeJsStructureRenderer.TEMPLATE_NAME)
        assert template is not None


# ------------------------------------------------------------------
#  _data_url
# ------------------------------------------------------------------


class TestDataUrl:
    def test_encodes_file_as_base64_javascript_data_url(self, tmp_path):
        import base64

        source = tmp_path / 'snippet.js'
        payload = b'console.log("hi");'
        source.write_bytes(payload)

        url = MUT._data_url(source)

        prefix = 'data:text/javascript;base64,'
        assert url.startswith(prefix)
        decoded = base64.b64decode(url[len(prefix) :])
        assert decoded == payload

    def test_roundtrips_arbitrary_bytes(self, tmp_path):
        import base64

        source = tmp_path / 'bytes.js'
        payload = bytes(range(256))
        source.write_bytes(payload)

        url = MUT._data_url(source)
        decoded = base64.b64decode(url.split('base64,', 1)[1])
        assert decoded == payload


# ------------------------------------------------------------------
#  _import_map
# ------------------------------------------------------------------


class TestImportMap:
    def test_online_uses_cdn_urls(self):
        mapping = MUT._import_map(offline=False)

        assert mapping['three'] == f'{MUT._CDN}/build/three.module.js'
        assert mapping[MUT._ADDON_CONTROLS].startswith(MUT._CDN)
        assert mapping[MUT._ADDON_CSS2D].startswith(MUT._CDN)
        assert mapping[MUT._ADDON_CONTROLS].endswith('OrbitControls.js')
        assert mapping[MUT._ADDON_CSS2D].endswith('CSS2DRenderer.js')

    def test_offline_inlines_data_urls(self):
        mapping = MUT._import_map(offline=True)

        prefix = 'data:text/javascript;base64,'
        assert mapping['three'].startswith(prefix)
        assert mapping[MUT._ADDON_CONTROLS].startswith(prefix)
        assert mapping[MUT._ADDON_CSS2D].startswith(prefix)

    def test_both_modes_share_the_same_keys(self):
        online = MUT._import_map(offline=False)
        offline = MUT._import_map(offline=True)

        expected_keys = {'three', MUT._ADDON_CONTROLS, MUT._ADDON_CSS2D}
        assert set(online) == expected_keys
        assert set(offline) == expected_keys


# ------------------------------------------------------------------
#  _rgb_css
# ------------------------------------------------------------------


class TestRgbCss:
    def test_formats_triple_as_css_rgb(self):
        assert MUT._rgb_css((1, 2, 3)) == 'rgb(1, 2, 3)'

    def test_handles_channel_bounds(self):
        assert MUT._rgb_css((0, 0, 0)) == 'rgb(0, 0, 0)'
        assert MUT._rgb_css((255, 255, 255)) == 'rgb(255, 255, 255)'


# ------------------------------------------------------------------
#  _scene_payload
# ------------------------------------------------------------------


class TestScenePayloadKeys:
    def test_payload_exposes_documented_keys(self):
        payload = MUT._scene_payload(_rich_scene())

        expected_keys = {
            'atoms',
            'wedgeSpheres',
            'ellipsoids',
            'bonds',
            'cellEdges',
            'axes',
            'labels',
            'legend',
            'palettes',
        }
        assert set(payload) == expected_keys

    def test_payload_is_json_serialisable(self):
        # The renderer embeds this dict via json.dumps; it must round-trip.
        payload = MUT._scene_payload(_rich_scene())
        assert json.loads(json.dumps(payload)) is not None


class TestScenePayloadPrimitives:
    def test_atoms_carry_geometry_colour_and_flags(self):
        payload = MUT._scene_payload(_rich_scene())

        atom = payload['atoms'][0]
        assert atom['centre'] == (0.0, 0.0, 0.0)
        assert atom['radius'] == 0.5
        assert atom['colour'] == (255, 0, 0)
        assert atom['label'] == 'Fe'
        assert atom['asymmetric'] is True

    def test_wedge_spheres_expand_fraction_colour_wedges(self):
        payload = MUT._scene_payload(_rich_scene())

        sphere = payload['wedgeSpheres'][0]
        assert sphere['centre'] == (0.5, 0.5, 0.5)
        assert sphere['radius'] == 0.4
        assert sphere['label'] == 'La/Ba'
        assert sphere['asymmetric'] is False
        assert sphere['wedges'] == [
            {'fraction': 0.6, 'colour': (0, 0, 255)},
            {'fraction': 0.4, 'colour': (210, 210, 210)},
        ]

    def test_ellipsoids_use_camelcase_semi_axes_and_row_lists(self):
        payload = MUT._scene_payload(_rich_scene())

        ellipsoid = payload['ellipsoids'][0]
        assert ellipsoid['centre'] == (0.25, 0.25, 0.25)
        assert ellipsoid['semiAxes'] == (0.3, 0.2, 0.1)
        # Orientation rows are converted to plain lists for JSON.
        assert ellipsoid['orientation'] == [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        assert ellipsoid['colour'] == (0, 255, 0)
        assert ellipsoid['label'] == 'O'
        assert ellipsoid['asymmetric'] is True
        assert ellipsoid['wedges'] == [{'fraction': 1.0, 'colour': (0, 255, 0)}]

    def test_bonds_split_colour_and_element_at_both_ends(self):
        payload = MUT._scene_payload(_rich_scene())

        bond = payload['bonds'][0]
        assert bond['start'] == (0.0, 0.0, 0.0)
        assert bond['end'] == (0.5, 0.5, 0.5)
        assert bond['startColour'] == (255, 0, 0)
        assert bond['endColour'] == (0, 0, 255)
        assert bond['startElement'] == 'Fe'
        assert bond['endElement'] == 'O'

    def test_cell_edges_expand_to_start_end_segments(self):
        payload = MUT._scene_payload(_rich_scene())

        assert payload['cellEdges'] == [
            {'start': (0.0, 0.0, 0.0), 'end': (1.0, 0.0, 0.0)},
            {'start': (0.0, 0.0, 0.0), 'end': (0.0, 1.0, 0.0)},
        ]

    def test_axes_expose_origin_and_lettered_arrows(self):
        payload = MUT._scene_payload(_rich_scene())

        axes = payload['axes']
        assert axes['origin'] == (0.0, 0.0, 0.0)
        letters = [arrow['letter'] for arrow in axes['arrows']]
        assert letters == ['a', 'b', 'c']
        assert axes['arrows'][0]['vector'] == (1.0, 0.0, 0.0)
        assert axes['arrows'][0]['colour'] == (220, 40, 40)

    def test_labels_expose_anchor_and_text(self):
        payload = MUT._scene_payload(_rich_scene())

        assert payload['labels'] == [{'anchor': (0.1, 0.2, 0.3), 'text': 'Fe1'}]

    def test_labels_fallback_to_atom_primitives(self):
        scene = StructureScene(
            cell_basis=_IDENTITY_BASIS,
            atoms=(
                AtomSphere(
                    centre=(0.0, 0.0, 0.0),
                    radius=0.5,
                    colour=(255, 0, 0),
                    label='Fe',
                ),
            ),
            occupancy_spheres=(
                OccupancyWedgeSphere(
                    centre=(0.5, 0.5, 0.5),
                    radius=0.4,
                    wedges=(OccupancyWedge(fraction=1.0, colour=(0, 0, 255)),),
                    label='La/Ba',
                ),
            ),
            ellipsoids=(
                AdpEllipsoid(
                    centre=(0.25, 0.25, 0.25),
                    semi_axes=(0.3, 0.2, 0.1),
                    orientation=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    colour=(0, 255, 0),
                    label='O',
                ),
            ),
        )

        payload = MUT._scene_payload(scene)

        assert payload['labels'] == [
            {'anchor': (0.0, 0.0, 0.0), 'text': 'Fe'},
            {'anchor': (0.5, 0.5, 0.5), 'text': 'La/Ba'},
            {'anchor': (0.25, 0.25, 0.25), 'text': 'O'},
        ]

    def test_legend_exposes_symbol_and_colour(self):
        payload = MUT._scene_payload(_rich_scene())

        assert payload['legend'] == [
            {'symbol': 'Fe', 'colour': (255, 0, 0)},
            {'symbol': 'O', 'colour': (0, 255, 0)},
        ]


class TestScenePayloadPalettes:
    def test_palettes_cover_every_colour_scheme(self):
        payload = MUT._scene_payload(_rich_scene())

        expected_schemes = {scheme.value for scheme in ColorSchemeEnum}
        assert set(payload['palettes']) == expected_schemes

    def test_each_palette_maps_every_legend_symbol(self):
        payload = MUT._scene_payload(_rich_scene())

        for scheme in ColorSchemeEnum:
            palette = payload['palettes'][scheme.value]
            assert set(palette) == {'Fe', 'O'}
            for rgb in palette.values():
                assert len(rgb) == 3

    def test_palette_uses_color_for_lookup(self):
        from easydiffraction.display.structure.assets.colors import color_for

        payload = MUT._scene_payload(_rich_scene())
        for scheme in ColorSchemeEnum:
            palette = payload['palettes'][scheme.value]
            assert palette['Fe'] == color_for('Fe', scheme.value)


class TestScenePayloadEmptyScene:
    def test_empty_scene_yields_empty_collections(self):
        payload = MUT._scene_payload(_identity_scene())

        assert payload['atoms'] == []
        assert payload['wedgeSpheres'] == []
        assert payload['ellipsoids'] == []
        assert payload['bonds'] == []
        assert payload['cellEdges'] == []
        assert payload['labels'] == []
        assert payload['legend'] == []

    def test_empty_scene_has_no_axes(self):
        payload = MUT._scene_payload(_identity_scene())
        assert payload['axes'] is None

    def test_empty_scene_palettes_are_empty_per_scheme(self):
        payload = MUT._scene_payload(_identity_scene())

        for scheme in ColorSchemeEnum:
            assert payload['palettes'][scheme.value] == {}


# ------------------------------------------------------------------
#  ThreeJsStructureRenderer — class surface
# ------------------------------------------------------------------


class TestRendererClass:
    def test_is_structure_renderer_subclass(self):
        assert issubclass(ThreeJsStructureRenderer, StructureRendererBase)

    def test_instantiation(self):
        assert ThreeJsStructureRenderer() is not None

    def test_supported_features_returns_frozenset(self):
        renderer = ThreeJsStructureRenderer()
        features = renderer.supported_features()
        assert isinstance(features, frozenset)

    def test_supported_features_match_class_constant(self):
        renderer = ThreeJsStructureRenderer()
        assert renderer.supported_features() == ThreeJsStructureRenderer.SUPPORTED

    def test_supported_feature_names(self):
        expected = frozenset({'atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'})
        assert expected == ThreeJsStructureRenderer.SUPPORTED

    def test_template_name(self):
        assert ThreeJsStructureRenderer.TEMPLATE_NAME == 'structure.html.j2'


# ------------------------------------------------------------------
#  ThreeJsStructureRenderer.render — happy path (theme_colors patched)
# ------------------------------------------------------------------


class TestRenderHtmlDocument:
    def test_returns_complete_html_document(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _rich_scene(),
            features=frozenset({'atoms', 'bonds'}),
            offline=True,
            dark=False,
        )
        assert isinstance(html, str)
        assert '<' in html
        assert '>' in html
        assert len(html) > 0

    def test_embeds_unique_container_id(self, patched_theme):
        renderer = ThreeJsStructureRenderer()
        scene = _rich_scene()
        first = renderer.render(scene, features=frozenset({'atoms'}), offline=True, dark=False)
        second = renderer.render(scene, features=frozenset({'atoms'}), offline=True, dark=False)

        assert 'crysview-' in first
        assert 'crysview-' in second
        # Each render mints a fresh uuid4-based container id.
        assert first != second

    def test_light_theme_marks_document_light(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )
        assert 'light' in html

    def test_dark_theme_marks_document_dark(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=True,
        )
        assert 'dark' in html
        assert '--cv-panel-bg: rgba(37, 37, 43, 0.95);' in html
        assert "stroke='%23ebebeb'" in html

    def test_offline_embeds_inlined_module(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )
        # Offline mode inlines the vendored module as a data URL.
        assert 'data:text/javascript;base64,' in html

    def test_online_links_cdn(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=False,
            dark=False,
        )
        assert MUT._CDN in html

    def test_offline_defaults_to_true(self, patched_theme):
        # Omitting ``offline`` must inline assets, not link the CDN.
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            dark=False,
        )
        assert 'data:text/javascript;base64,' in html

    def test_dark_none_autodetects_via_is_dark(self, patched_theme, monkeypatch):
        calls = []

        def fake_is_dark():
            calls.append(True)
            return True

        monkeypatch.setattr(MUT, 'is_dark', fake_is_dark)
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
        )
        assert calls == [True]
        assert 'dark' in html

    def test_features_are_embedded_sorted(self, patched_theme, monkeypatch):
        captured = {}

        real_dumps = json.dumps

        def spy_dumps(obj, *args, **kwargs):
            if isinstance(obj, list):
                captured['features'] = obj
            return real_dumps(obj, *args, **kwargs)

        monkeypatch.setattr(MUT.json, 'dumps', spy_dumps)
        ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset({'bonds', 'atoms', 'cell'}),
            offline=True,
            dark=False,
        )
        assert captured['features'] == ['atoms', 'bonds', 'cell']

    def test_download_button_is_bottom_right_overlay(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )

        assert '<div class="cv-download"></div>' in html
        assert 'right: 10px; bottom: 8px;' in html
        assert "iconButton(downloadHost, ICONS.camera, 'Download PNG')" in html

    def test_viewer_is_isolated_from_page_header_stacking(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )

        assert 'overflow:hidden;isolation:isolate;z-index:0;' in html
        assert 'position: absolute; z-index: 2; background: var(--cv-panel-bg);' in html

    def test_perspective_projection_uses_reduced_field_of_view(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )

        assert 'const PERSPECTIVE_FOV_DEG = 30;' in html
        assert 'new THREE.PerspectiveCamera(PERSPECTIVE_FOV_DEG,' in html

    def test_colour_scheme_select_matches_button_height(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _rich_scene(),
            features=frozenset({'atoms'}),
            offline=True,
            dark=False,
        )

        assert 'height: calc(var(--cv-control-h) + 2px);' in html
        assert 'min-height: calc(var(--cv-control-h) + 2px);' in html
        assert 'max-height: calc(var(--cv-control-h) + 2px);' in html
        assert 'display: inline-flex; align-items: center;' in html
        assert 'vertical-align: top;' in html
        assert 'font-family: inherit;' in html
        assert '--cv-axis-letter-size: 18px;\n  }\n  #' in html

    def test_exposes_host_theme_sync_hook(self, patched_theme):
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )

        assert 'root.__crysviewApplyTheme = applyTheme;' in html
        assert "data-md-color-scheme" in html
        assert "data-jp-theme-light" in html
        assert "document.body.getAttribute('data-md-color-scheme')" in html


# ------------------------------------------------------------------
#  ThreeJsStructureRenderer.render — invalid inputs
# ------------------------------------------------------------------


class TestRenderInvalidInputs:
    def test_non_iterable_features_raises_type_error(self, patched_theme):
        # ``render`` sorts ``features``; a non-iterable cannot be sorted.
        with pytest.raises(TypeError):
            ThreeJsStructureRenderer().render(
                _identity_scene(),
                features=None,  # type: ignore[arg-type]
                offline=True,
                dark=False,
            )


# ------------------------------------------------------------------
#  ThreeJsStructureRenderer.render — un-patched theme_colors integration
# ------------------------------------------------------------------


class TestRenderUnpatchedIntegration:
    """Exercise ``render`` against the real ``theme_colors`` collaborator.

    These tests deliberately omit the ``patched_theme`` fixture so the
    production ``theme_colors(dark=dark)`` call runs for real, proving the
    keyword-only signature is invoked correctly and its light/dark canvas
    colours reach the document.
    """

    def test_render_returns_html_document(self):
        # No ``patched_theme``: the real, keyword-only ``theme_colors``
        # must accept the call and yield a complete HTML document.
        html = ThreeJsStructureRenderer().render(
            _rich_scene(),
            features=frozenset({'atoms', 'bonds'}),
            offline=True,
            dark=False,
        )
        assert isinstance(html, str)
        assert '<' in html
        assert '>' in html
        assert 'crysview-' in html

    def test_light_theme_embeds_real_canvas_colours(self):
        # ``theme_colors(dark=False)`` returns LIGHT_THEME; its background
        # and foreground must be wired into the document.
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=False,
        )
        assert 'rgb(255, 255, 255)' in html  # LIGHT_THEME background
        assert 'rgb(33, 33, 33)' in html  # LIGHT_THEME foreground
        assert 'light' in html

    def test_dark_theme_embeds_real_canvas_colours(self):
        # ``theme_colors(dark=True)`` returns DARK_THEME instead.
        html = ThreeJsStructureRenderer().render(
            _identity_scene(),
            features=frozenset(),
            offline=True,
            dark=True,
        )
        assert 'rgb(33, 33, 33)' in html  # DARK_THEME background
        assert 'rgb(235, 235, 235)' in html  # DARK_THEME foreground
        assert 'dark' in html
