# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Display metadata for descriptor labels and units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayHandler:
    """
    Display metadata for descriptor labels and units.

    Attributes
    ----------
    display_name : str | None, default=None
        Human-readable label for HTML and GUI contexts.
    display_units : str | None, default=None
        Human-readable units for HTML and GUI contexts.
    latex_name : str | None, default=None
        TeX label for LaTeX report contexts.
    latex_units : str | None, default=None
        TeX units for LaTeX report contexts.
    """

    display_name: str | None = None
    display_units: str | None = None
    latex_name: str | None = None
    latex_units: str | None = None
