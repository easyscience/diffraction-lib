# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Viewer facade and engine factory for the structure view."""

from __future__ import annotations

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.structure.enums import ViewerEngineEnum
from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer
from easydiffraction.display.structure.renderers.threejs import ThreeJsStructureRenderer
from easydiffraction.display.structure.scene import StructureScene


class ViewerFactory(RendererFactoryBase):
    """Factory for structure-view renderer engines."""

    @classmethod
    def _registry(cls) -> dict:
        return {
            ViewerEngineEnum.ASCII.value: {
                'description': ViewerEngineEnum.ASCII.description(),
                'class': AsciiStructureRenderer,
            },
            ViewerEngineEnum.THREEJS.value: {
                'description': ViewerEngineEnum.THREEJS.description(),
                'class': ThreeJsStructureRenderer,
            },
        }


class Viewer(RendererBase):
    """Switchable facade that draws a scene with the active engine."""

    @classmethod
    def _factory(cls) -> type[RendererFactoryBase]:
        """Return the structure-view engine factory."""
        return ViewerFactory

    @classmethod
    def _default_engine(cls) -> str:
        """Return the default engine name (Three.js)."""
        return ViewerEngineEnum.default().value

    def show_config(self) -> None:
        """Display the active structure-view engine."""
        self.show_current_engine()

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        """
        Draw the scene with the active engine.

        Parameters
        ----------
        scene : StructureScene
            The renderer-neutral primitives to draw.
        features : frozenset[str]
            The content-resolved feature set from the display facade.

        Returns
        -------
        str
            ASCII text or an HTML document, depending on the active engine.
        """
        return self._backend.render(scene, features=features)

    def supported_features(self) -> frozenset[str]:
        """Return the feature names the active engine can draw."""
        return self._backend.supported_features()
