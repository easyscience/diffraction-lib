# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Table rendering engines: console (Rich) and Jupyter (pandas)."""

from __future__ import annotations

from enum import Enum
from typing import Any

import pandas as pd

from easydiffraction import log
from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.tablers.pandas import PandasTableBackend
from easydiffraction.display.tablers.rich import RichTableBackend
from easydiffraction.utils.env import is_notebook


class TableEngineEnum(str, Enum):
    RICH = 'rich'
    PANDAS = 'pandas'

    @classmethod
    def default(cls) -> 'TableEngineEnum':
        """Select default engine based on environment.

        Returns Pandas when running in Jupyter, otherwise Rich.
        """
        if is_notebook():
            log.debug('Setting default table engine to Pandas for Jupyter')
            return cls.PANDAS
        log.debug('Setting default table engine to Rich for console')
        return cls.RICH

    def description(self) -> str:
        if self is TableEngineEnum.RICH:
            return 'Console rendering with Rich'
        elif self is TableEngineEnum.PANDAS:
            return 'Jupyter DataFrame rendering with Pandas'
        return ''


class TableRenderer(RendererBase):
    """Renderer for tabular data with selectable engines (singleton)."""

    @classmethod
    def _factory(cls) -> RendererFactoryBase:
        return TableRendererFactory

    @classmethod
    def _default_engine(cls) -> str:
        """Default engine derived from TableEngineEnum."""
        return TableEngineEnum.default().value

    def show_config(self) -> None:
        """Display minimal configuration for this renderer."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [['engine', self._engine]]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        log.paragraph('Current tabler configuration')
        TableRenderer.get().render(df)

    def render(self, df) -> Any:
        # Work on a copy to avoid mutating the original DataFrame
        df = df.copy()

        # Force starting index from 1
        df.index += 1

        # Extract column alignments
        alignments = df.columns.get_level_values(1)

        # Remove alignments from df (Keep only the first index level)
        df.columns = df.columns.get_level_values(0)

        return self._backend.render(alignments, df)


class TableRendererFactory(RendererFactoryBase):
    """Factory for creating tabler instances."""

    @classmethod
    def _registry(cls) -> dict:
        """Build registry from TableEngineEnum ensuring single source of
        truth for descriptions and engine ids.
        """
        return {
            TableEngineEnum.RICH.value: {
                'description': TableEngineEnum.RICH.description(),
                'class': RichTableBackend,
            },
            TableEngineEnum.PANDAS.value: {
                'description': TableEngineEnum.PANDAS.description(),
                'class': PandasTableBackend,
            },
        }
