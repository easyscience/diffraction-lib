# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for project display categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class DisplayFactory(FactoryBase):
    """Create project display category instances."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
