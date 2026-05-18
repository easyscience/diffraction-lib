"""Factory for project verbosity categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class VerbosityFactory(FactoryBase):
    """Create project verbosity category instances."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
