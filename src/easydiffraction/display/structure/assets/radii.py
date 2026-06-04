# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Per-element radius lookup with covalent fallback."""

from __future__ import annotations

from easydiffraction.display.structure.assets.elements import ELEMENT_RADII

# Last-resort radius (angstrom) for an element absent from the database.
DEFAULT_RADIUS = 1.0


def radius_for(element: str, model: str) -> tuple[float, bool]:
    """
    Return a sphere radius for an element under a radius model.

    Falls back to the element's covalent radius when the selected model
    has no value for it, and to :data:`DEFAULT_RADIUS` when the element
    is unknown.

    Parameters
    ----------
    element : str
        Bare element symbol, e.g. ``'Fe'``.
    model : str
        One of ``'vdw'``, ``'covalent'``, ``'ionic'``.

    Returns
    -------
    tuple[float, bool]
        The radius (angstrom) and a ``substituted`` flag that is
        ``True`` when the requested model's value was unavailable and a
        fallback was used.
    """
    entry = ELEMENT_RADII.get(element)
    if entry is None:
        return DEFAULT_RADIUS, True
    value = entry.get(model)
    if value is not None:
        return value, False
    covalent = entry.get('covalent')
    if covalent is not None:
        return covalent, True
    return DEFAULT_RADIUS, True
