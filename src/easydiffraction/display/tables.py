"""Table rendering engines: console (rich) and Jupyter (pandas)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from easydiffraction import log
from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.tablers.pandas import PandasTableBackend
from easydiffraction.display.tablers.rich import RichTableBackend


class TableEngineEnum(str, Enum):
    RICH = 'rich'
    PANDAS = 'pandas'


class TableRenderer(RendererBase):
    """Renderer for tabular data with selectable engines (singleton)."""

    @classmethod
    def _factory(cls) -> RendererFactoryBase:
        return TableRendererFactory

    @classmethod
    def _default_engine(cls) -> str:
        """Decide default engine: Pandas in Jupyter, Rich otherwise."""
        try:
            from IPython import get_ipython

            ip = get_ipython()

            # Running inside a Jupyter notebook
            if ip and 'IPKernelApp' in ip.config:
                log.debug('Setting default table engine to Pandas for Jupyter')
                return TableEngineEnum.PANDAS.value

        except Exception:
            log.debug('No IPython available')
            pass

        log.debug('Setting default table engine to Rich for console')
        return TableEngineEnum.RICH.value

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

    _SUPPORTED_ENGINES = {
        TableEngineEnum.RICH.value: {
            'description': 'Console rendering with Rich',
            'class': RichTableBackend,
        },
        TableEngineEnum.PANDAS.value: {
            'description': 'Jupyter DataFrame rendering with Pandas',
            'class': PandasTableBackend,
        },
    }
