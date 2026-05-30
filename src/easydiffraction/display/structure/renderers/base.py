# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base for structure-scene renderer engines."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from easydiffraction.display.structure.scene import StructureScene


class StructureRendererBase(ABC):
    """Base class an engine implements to draw a structure scene."""

    @abstractmethod
    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        """
        Draw the scene and return the engine-specific output.

        Parameters
        ----------
        scene : StructureScene
            The renderer-neutral primitives to draw.
        features : frozenset[str]
            The content-resolved feature set from the facade. The renderer
            draws the features it supports and announces + skips the rest.

        Returns
        -------
        str
            ASCII text or an HTML document, depending on the engine.
        """
        raise NotImplementedError

    @abstractmethod
    def supported_features(self) -> frozenset[str]:
        """
        Return the feature names this engine can draw.

        Returns
        -------
        frozenset[str]
            Subset of ``atoms``, ``bonds``, ``cell``, ``axes``,
            ``moments``, ``labels``.
        """
        raise NotImplementedError
