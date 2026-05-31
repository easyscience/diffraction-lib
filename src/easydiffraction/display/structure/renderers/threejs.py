# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Three.js renderer: an interactive, self-contained HTML structure view.
"""

from __future__ import annotations

import base64
import json
import pathlib
import uuid

from jinja2 import Environment
from jinja2 import PackageLoader

from easydiffraction.display.structure.assets.colors import color_for
from easydiffraction.display.structure.assets.colors import theme_colors
from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.scene import StructureScene
from easydiffraction.utils._vendored.theme_detect import is_dark

_VENDOR = pathlib.Path(__file__).parent / 'vendor' / 'threejs'
_CDN = 'https://cdn.jsdelivr.net/npm/three@0.160.0'
_ADDON_CONTROLS = 'three/addons/controls/OrbitControls.js'
_ADDON_CSS2D = 'three/addons/renderers/CSS2DRenderer.js'


def _environment() -> Environment:
    """Return the Jinja environment for structure-view templates."""
    return Environment(
        loader=PackageLoader('easydiffraction.display.structure', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _data_url(path: pathlib.Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    return f'data:text/javascript;base64,{encoded}'


def _import_map(*, offline: bool) -> dict[str, str]:
    if offline:
        return {
            'three': _data_url(_VENDOR / 'three.module.js'),
            _ADDON_CONTROLS: _data_url(_VENDOR / 'OrbitControls.js'),
            _ADDON_CSS2D: _data_url(_VENDOR / 'CSS2DRenderer.js'),
        }
    return {
        'three': f'{_CDN}/build/three.module.js',
        _ADDON_CONTROLS: f'{_CDN}/examples/jsm/controls/OrbitControls.js',
        _ADDON_CSS2D: f'{_CDN}/examples/jsm/renderers/CSS2DRenderer.js',
    }


def _scene_payload(scene: StructureScene) -> dict:
    axes = None
    if scene.axes is not None:
        axes = {
            'origin': scene.axes.origin,
            'arrows': [
                {'vector': arrow.vector, 'colour': arrow.colour, 'letter': arrow.letter}
                for arrow in scene.axes.axes
            ],
        }
    edges = []
    if scene.cell_edges is not None:
        edges = [{'start': edge.start, 'end': edge.end} for edge in scene.cell_edges.edges]
    return {
        'atoms': [
            {'centre': a.centre, 'radius': a.radius, 'colour': a.colour, 'label': a.label,
             'asymmetric': a.asymmetric}
            for a in scene.atoms
        ],
        'wedgeSpheres': [
            {
                'centre': s.centre,
                'radius': s.radius,
                'label': s.label,
                'wedges': [{'fraction': w.fraction, 'colour': w.colour} for w in s.wedges],
                'asymmetric': s.asymmetric,
            }
            for s in scene.occupancy_spheres
        ],
        'ellipsoids': [
            {
                'centre': e.centre,
                'semiAxes': e.semi_axes,
                'orientation': [list(row) for row in e.orientation],
                'colour': e.colour,
                'label': e.label,
                'wedges': [{'fraction': w.fraction, 'colour': w.colour} for w in e.wedges],
                'asymmetric': e.asymmetric,
            }
            for e in scene.ellipsoids
        ],
        'bonds': [
            {
                'start': b.start,
                'end': b.end,
                'startColour': b.start_colour,
                'endColour': b.end_colour,
                'startElement': b.start_element,
                'endElement': b.end_element,
            }
            for b in scene.bonds
        ],
        'cellEdges': edges,
        'axes': axes,
        'labels': [{'anchor': label.anchor, 'text': label.text} for label in scene.labels],
        'legend': [{'symbol': entry.symbol, 'colour': entry.colour} for entry in scene.legend],
        'palettes': {
            scheme.value: {entry.symbol: color_for(entry.symbol, scheme.value)
                           for entry in scene.legend}
            for scheme in ColorSchemeEnum
        },
    }


def _rgb_css(rgb: tuple[int, int, int]) -> str:
    return f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'


class ThreeJsStructureRenderer(StructureRendererBase):
    """
    Interactive Three.js renderer for notebook and standalone HTML.
    """

    SUPPORTED = frozenset({'atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'})
    TEMPLATE_NAME = 'structure.html.j2'

    def supported_features(self) -> frozenset[str]:
        """Return the features the Three.js engine can draw."""
        return self.SUPPORTED

    def render(
        self,
        scene: StructureScene,
        *,
        features: frozenset[str],
        offline: bool = True,
        dark: bool | None = None,
    ) -> str:
        """
        Render the scene as a self-contained interactive HTML document.

        Parameters
        ----------
        scene : StructureScene
            The renderer-neutral primitives to draw.
        features : frozenset[str]
            The content-resolved feature set; drives the modebar's
            initial visibility toggles.
        offline : bool, default=True
            When ``True`` (default), inline the pinned Three.js assets
            so the view renders with no network; when ``False`` link the
            CDN.
        dark : bool | None, default=None
            Force the dark (``True``) or light (``False``) theme. When
            ``None`` (default), auto-detect from the environment.
            Reports pass ``False`` so the view matches their light page.

        Returns
        -------
        str
            A complete HTML document.
        """
        if dark is None:
            dark = is_dark()
        colours = theme_colors(dark=dark)
        payload = json.dumps(_scene_payload(scene)).replace('</', '<\\/')
        import_map = json.dumps({'imports': _import_map(offline=offline)}).replace('</', '<\\/')
        template = _environment().get_template(self.TEMPLATE_NAME)
        return template.render(
            container_id=f'crysview-{uuid.uuid4().hex}',
            scene_json=payload,
            import_map=import_map,
            features_json=json.dumps(sorted(features)),
            background=_rgb_css(colours['background']),
            foreground=_rgb_css(colours['foreground']),
            theme='dark' if dark else 'light',
        )
