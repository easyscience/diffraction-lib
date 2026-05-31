# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Per-element colours, axis colours, and theme-dependent canvas colours.
"""

from __future__ import annotations

from easydiffraction.display.structure.assets.elements import ELEMENT_COLORS

Rgb = tuple[int, int, int]

# Fallback element colour (pale pink) for an unknown element.
DEFAULT_COLOR: Rgb = (255, 192, 203)

# Crystallographic axis colours (a=red, b=green, c=blue), as in VESTA.
AXIS_COLORS: dict[str, Rgb] = {'a': (220, 40, 40), 'b': (40, 180, 40), 'c': (40, 80, 220)}

# Neutral wedge colour for the vacant fraction of a mixed site.
VACANCY_COLOR: Rgb = (210, 210, 210)

# Canvas + annotation colours selected by the detected light/dark theme.
LIGHT_THEME: dict[str, Rgb] = {'background': (255, 255, 255), 'foreground': (33, 33, 33)}
DARK_THEME: dict[str, Rgb] = {'background': (33, 33, 33), 'foreground': (235, 235, 235)}


def color_for(element: str, scheme: str) -> Rgb:
    """
    Return the RGB colour for an element under a colour scheme.

    Falls back to the element's Jmol colour when the scheme has no
    entry, and to :data:`DEFAULT_COLOR` when the element is unknown.

    Parameters
    ----------
    element : str
        Bare element symbol, e.g. ``'Fe'``.
    scheme : str
        One of ``'jmol'``, ``'vesta'``.

    Returns
    -------
    Rgb
        RGB triple in the 0-255 range.
    """
    entry = ELEMENT_COLORS.get(element)
    if entry is None:
        return DEFAULT_COLOR
    value = entry.get(scheme)
    if value is not None:
        return value
    return entry.get('jmol') or DEFAULT_COLOR


def theme_colors(*, dark: bool) -> dict[str, Rgb]:
    """
    Return canvas/annotation colours for the detected theme.

    Parameters
    ----------
    dark : bool
        ``True`` for a dark host theme, ``False`` for light.

    Returns
    -------
    dict[str, Rgb]
        Mapping with ``'background'`` and ``'foreground'`` colours.
    """
    return DARK_THEME if dark else LIGHT_THEME
