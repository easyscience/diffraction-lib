# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Joint-fit factory - delegates to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class JointFitFactory(FactoryBase):
    """Create joint-fit collections by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
