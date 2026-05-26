# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project exception types."""

from __future__ import annotations


class EasyDiffractionError(Exception):
    """Base class for EasyDiffraction exceptions."""


class EasyDiffractionWriterError(EasyDiffractionError):
    """Raised when EasyDiffraction cannot write a valid file."""
