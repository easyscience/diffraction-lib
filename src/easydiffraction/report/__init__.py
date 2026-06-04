# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project report facade."""

from __future__ import annotations


def __getattr__(name: str) -> object:
    """Load report objects that would otherwise form import cycles."""
    if name == 'Report':
        from easydiffraction.project.categories.report.default import Report  # noqa: PLC0415

        return Report
    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)
