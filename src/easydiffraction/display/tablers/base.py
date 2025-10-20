from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from IPython import get_ipython
from jupyter_dark_detect import is_dark
from rich.color import Color


class TableBackendBase(ABC):
    FLOAT_PRECISION = 5
    RICH_BORDER_DARK_THEME = 'grey35'
    RICH_BORDER_LIGHT_THEME = 'grey85'

    def __init__(self) -> None:
        super().__init__()
        self._float_fmt = f'{{:.{self.FLOAT_PRECISION}f}}'.format

    def _format_value(self, value: Any) -> Any:
        return self._float_fmt(value) if isinstance(value, float) else str(value)

    def _is_dark_theme(self) -> bool:
        """Return 'dark' or 'light'.

        If not running inside Jupyter, return default.
        """
        default = True

        in_jupyter = (
            get_ipython() is not None and get_ipython().__class__.__name__ == 'ZMQInteractiveShell'
        )

        if not in_jupyter:
            return default

        return is_dark()

    def _rich_to_hex(self, color):
        c = Color.parse(color)
        rgb = c.get_truecolor()
        hex_value = '#{:02x}{:02x}{:02x}'.format(*rgb)
        return hex_value

    @property
    def _rich_border_color(self) -> str:
        return (
            self.RICH_BORDER_DARK_THEME if self._is_dark_theme() else self.RICH_BORDER_LIGHT_THEME
        )

    @property
    def _pandas_border_color(self) -> str:
        return self._rich_to_hex(self._rich_border_color)

    @abstractmethod
    def render(
        self,
        alignments,
        df,
    ) -> Any:
        pass
