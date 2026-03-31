# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Atom-sites factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class AtomSitesFactory(FactoryBase):
    """Create atom-sites collections by tag."""

    _default_rules = {
        frozenset(): 'default',
    }
