# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for the crysview structure view."""

from __future__ import annotations

from enum import StrEnum


class ViewerEngineEnum(StrEnum):
    """Available structure-view renderer engines."""

    ASCII = 'ascii'
    THREEJS = 'threejs'

    @classmethod
    def default(cls) -> ViewerEngineEnum:
        """Select the default engine (rich Three.js, headless-friendly)."""
        return cls.THREEJS

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is ViewerEngineEnum.ASCII:
            return 'Console ASCII schematic structure view'
        if self is ViewerEngineEnum.THREEJS:
            return 'Interactive Three.js 3D structure view'
        return ''


class AtomShapeEnum(StrEnum):
    """How each atom is depicted in the structure view."""

    BALL = 'ball'
    ORTEP = 'ortep'

    @classmethod
    def default(cls) -> AtomShapeEnum:
        """Select the default atom shape (ORTEP thermal surfaces)."""
        return cls.ORTEP

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is AtomShapeEnum.BALL:
            return 'Ball-and-stick radius-model spheres'
        if self is AtomShapeEnum.ORTEP:
            return 'ORTEP ADP probability surfaces (ellipsoids)'
        return ''


class RadiusModelEnum(StrEnum):
    """Standard per-element radius model for atom sphere size."""

    VDW = 'vdw'
    COVALENT = 'covalent'
    IONIC = 'ionic'
    ATOMIC = 'atomic'

    @classmethod
    def default(cls) -> RadiusModelEnum:
        """Select the default radius model (covalent; charge-free)."""
        return cls.COVALENT

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is RadiusModelEnum.VDW:
            return 'Van der Waals radii'
        if self is RadiusModelEnum.COVALENT:
            return 'Covalent radii'
        if self is RadiusModelEnum.IONIC:
            return 'Ionic (Shannon) radii'
        if self is RadiusModelEnum.ATOMIC:
            return 'Atomic (empirical) radii'
        return ''


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
