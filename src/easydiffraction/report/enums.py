# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration types used by report components."""

from __future__ import annotations

from enum import StrEnum


class ReportFormatEnum(StrEnum):
    """Report output format."""

    CIF = 'cif'
    HTML = 'html'
    TEX = 'tex'
    PDF = 'pdf'

    @classmethod
    def default(cls) -> ReportFormatEnum:
        """Return the default report format."""
        return cls.CIF


class ReportStyleEnum(StrEnum):
    """Report template style."""

    IUCR = 'iucr'
    REVTEX = 'revtex'

    @classmethod
    def default(cls) -> ReportStyleEnum:
        """Return the default report style."""
        return cls.IUCR
