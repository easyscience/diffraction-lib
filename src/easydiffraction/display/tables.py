# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Table rendering engines: console (Rich) and Jupyter (pandas)."""

from __future__ import annotations

from enum import StrEnum

import pandas as pd

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.tablers.pandas import PandasTableBackend
from easydiffraction.display.tablers.rich import RichTableBackend
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class TableEngineEnum(StrEnum):
    """Available table rendering backends."""

    RICH = 'rich'
    PANDAS = 'pandas'

    @classmethod
    def default(cls) -> TableEngineEnum:
        """
        Select default engine based on environment.

        Returns Pandas when running in Jupyter, otherwise Rich.
        """
        if in_jupyter():
            log.debug('Setting default table engine to Pandas for Jupyter')
            return cls.PANDAS
        log.debug('Setting default table engine to Rich for console')
        return cls.RICH

    def description(self) -> str:
        """
        Return a human-readable description of this table engine.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is TableEngineEnum.RICH:
            return 'Console rendering with Rich'
        if self is TableEngineEnum.PANDAS:
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
        console.paragraph('Current tabler configuration')
        TableRenderer.get().render(df)

    @staticmethod
    def _prepare_dataframe(df: object) -> tuple[object, object]:
        """
        Normalize input table data for backend consumption.

        Parameters
        ----------
        df : object
            DataFrame with a two-level column index where the second
            level provides per-column alignment.

        Returns
        -------
        tuple[object, object]
            Normalized ``(alignments, dataframe)`` pair.
        """
        prepared_df = df.copy()
        prepared_df.index += 1

        alignments = prepared_df.columns.get_level_values(1)
        prepared_df.columns = prepared_df.columns.get_level_values(0)
        return alignments, prepared_df

    def build_renderable(self, df: object) -> object:
        """
        Build a backend-native renderable without displaying it.

        Parameters
        ----------
        df : object
            DataFrame with a two-level column index where the second
            level provides per-column alignment.

        Returns
        -------
        object
            Backend-native renderable, such as a Rich table or HTML.
        """
        alignments, prepared_df = self._prepare_dataframe(df)
        return self._backend.build_renderable(alignments, prepared_df)

    def render(self, df: object, display_handle: object | None = None) -> object:
        """
        Render a DataFrame as a table using the active backend.

        Parameters
        ----------
        df : object
            DataFrame with a two-level column index where the second
            level provides per-column alignment.
        display_handle : object | None, default=None
            Optional environment-specific handle used to update an
            existing output area in-place (e.g., an IPython
            DisplayHandle or a terminal live handle).

        Returns
        -------
        object
            Backend-specific return value (usually ``None``).
        """
        alignments, prepared_df = self._prepare_dataframe(df)
        return self._backend.render(alignments, prepared_df, display_handle)


class TableRendererFactory(RendererFactoryBase):
    """Factory for creating tabler instances."""

    @classmethod
    def _registry(cls) -> dict:
        """
        Build registry, adapting available engines to the environment.

        - In Jupyter: expose both 'rich' and 'pandas'. - In terminal:
        expose only 'rich' (pandas is notebook-only).
        """
        base = {
            TableEngineEnum.RICH.value: {
                'description': TableEngineEnum.RICH.description(),
                'class': RichTableBackend,
            }
        }
        if in_jupyter():
            base[TableEngineEnum.PANDAS.value] = {
                'description': TableEngineEnum.PANDAS.description(),
                'class': PandasTableBackend,
            }
        return base
