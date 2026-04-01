# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""General-purpose enumerations shared across the library."""

from __future__ import annotations

from enum import StrEnum


class VerbosityEnum(StrEnum):
    """
    Console output verbosity level.

    Controls how much information is printed during operations such as
    data loading, fitting, and saving.

    Members
    -------
    FULL Multi-line output with headers, tables, and details. SHORT
    Single-line status messages per action. SILENT No console output.
    """

    FULL = 'full'
    SHORT = 'short'
    SILENT = 'silent'

    @classmethod
    def default(cls) -> VerbosityEnum:
        """Return the default verbosity (FULL)."""
        return cls.FULL
