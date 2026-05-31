# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for the crysview structure view."""

from __future__ import annotations

from enum import StrEnum

from easydiffraction.utils.environment import in_jupyter


class ViewerEngineEnum(StrEnum):
    """Available structure-view renderer engines."""

    ASCII = 'ascii'
    THREEJS = 'threejs'

    @classmethod
    def default(cls) -> ViewerEngineEnum:
        """Select the default engine based on environment."""
        if in_jupyter():
            return cls.THREEJS
        return cls.ASCII

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is ViewerEngineEnum.ASCII:
            return 'Console ASCII schematic structure view'
        if self is ViewerEngineEnum.THREEJS:
            return 'Interactive Three.js 3D structure view'
        return ''


class AtomViewEnum(StrEnum):
    """
    How atoms are sized and shaped in the structure view.

    The radius models draw fixed balls; ``adp`` draws displacement
    surfaces (spheres for isotropic sites, ellipsoids for anisotropic).
    """

    VDW = 'vdw'
    COVALENT = 'covalent'
    IONIC = 'ionic'
    ADP = 'adp'

    @classmethod
    def default(cls) -> AtomViewEnum:
        """Select the default atom view (ADP displacement surfaces)."""
        return cls.ADP

    @property
    def is_adp(self) -> bool:
        """Return whether atoms are drawn as displacement surfaces."""
        return self is AtomViewEnum.ADP

    def radius_model(self) -> str:
        """
        Return the radius-table name for ball sizing.

        The ``adp`` view still needs ball radii for mixed-occupancy
        sites and as a fallback for zero-displacement atoms, where it
        uses covalent radii.
        """
        if self is AtomViewEnum.ADP:
            return AtomViewEnum.COVALENT.value
        return self.value

    def description(self) -> str:
        """Human-readable description for UI listings."""
        descriptions = {
            AtomViewEnum.VDW: 'Van der Waals radius balls',
            AtomViewEnum.COVALENT: 'Covalent radius balls',
            AtomViewEnum.IONIC: 'Ionic (Shannon) radius balls',
            AtomViewEnum.ADP: 'ADP probability surfaces (spheres / ellipsoids)',
        }
        return descriptions.get(self, '')


class ColorSchemeEnum(StrEnum):
    """Standard element colour palette."""

    JMOL = 'jmol'
    VESTA = 'vesta'

    @classmethod
    def default(cls) -> ColorSchemeEnum:
        """Select the default colour scheme (Jmol/CPK)."""
        return cls.JMOL

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is ColorSchemeEnum.JMOL:
            return 'Jmol / CPK colour scheme'
        if self is ColorSchemeEnum.VESTA:
            return 'VESTA colour scheme'
        return ''
