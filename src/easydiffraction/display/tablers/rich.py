# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Rich-based table renderer for terminals and notebooks."""

from __future__ import annotations

import io

from rich.box import Box
from rich.console import Console
from rich.table import Table
from rich.text import Text

try:
    from IPython.display import HTML
    from IPython.display import display
except ImportError:
    HTML = None
    display = None

from easydiffraction.display.links import TableLink
from easydiffraction.display.tablers.base import TableBackendBase
from easydiffraction.utils.environment import can_use_ipython_display
from easydiffraction.utils.logging import ConsoleManager
from easydiffraction.utils.logging import log

"""Custom compact box style used for consistent borders."""
CUSTOM_BOX = """\
┌──┐
│  │
├──┤
│  │
├──┤
├──┤
│  │
└──┘
"""
RICH_TABLE_BOX: Box = Box(CUSTOM_BOX, ascii=False)


class RichTableBackend(TableBackendBase):
    """Render tables to terminal or Jupyter using the Rich library."""

    def _format_cell(self, value: object) -> object:
        """
        Return one Rich-compatible table cell.

        Parameters
        ----------
        value : object
            Raw cell value.

        Returns
        -------
        object
            Renderable table cell.
        """
        if isinstance(value, TableLink):
            return Text(value.text, style=f'link {value.url}')
        return self._format_value(value)

    @staticmethod
    def _to_html(table: Table) -> str:
        """
        Render a Rich table to HTML using an off-screen console.

        A fresh ``Console(record=True, file=StringIO())`` avoids private
        attribute access and guarantees no visible output in notebooks.

        Parameters
        ----------
        table : Table
            Rich :class:`~rich.table.Table` to export.

        Returns
        -------
        str
            HTML string with inline styles for notebook display.
        """
        tmp = Console(force_jupyter=False, record=True, file=io.StringIO())
        tmp.print(table)
        html = tmp.export_html(inline_styles=True)
        # Remove margins inside pre blocks, shrink the font, and tighten
        # the line spacing so notebook/HTML tables stay compact (the box
        # rows otherwise inherit the page's tall code line-height).
        return html.replace(
            '<pre ',
            "<pre style='margin:0; font-size: 0.9em !important; line-height: 1.2 !important; ' ",
        )

    def build_renderable(
        self,
        alignments: object,
        df: object,
    ) -> object:
        """
        Construct a Rich Table with formatted data and alignment.

        Parameters
        ----------
        alignments : object
            Iterable of text alignment values for columns.
        df : object
            DataFrame-like object providing rows to render.

        Returns
        -------
        object
            A :class:`~rich.table.Table` configured for display.
        """
        color = self._rich_border_color
        table = Table(
            title=None,
            box=RICH_TABLE_BOX,
            show_header=True,
            header_style='bold',
            border_style=color,
        )

        # Index column
        table.add_column(justify='right', style=color)

        # Data columns
        for col, align in zip(df, alignments, strict=False):
            table.add_column(str(col), justify=align, no_wrap=False)

        # Rows
        for idx, row_values in df.iterrows():
            formatted_row = [self._format_cell(v) for v in row_values]
            table.add_row(str(idx), *formatted_row)

        return table

    def _update_display(self, table: Table, display_handle: object) -> None:
        """
        Single, consistent update path for Jupyter and terminal.

        - With a handle that has ``update()``: * If it's an IPython
        DisplayHandle, export to HTML and update. * Otherwise, treat it
        as a terminal/live-like handle and update with the Rich
        renderable. - Without a handle, print once to the shared
        console.

        Parameters
        ----------
        table : Table
            Rich :class:`~rich.table.Table` to display.
        display_handle : object
            Optional environment-specific handle for in- place updates
            (IPython or terminal live).
        """
        # Handle with update() method
        if display_handle is not None and hasattr(display_handle, 'update'):
            # IPython DisplayHandle path
            if can_use_ipython_display(display_handle) and HTML is not None:
                try:
                    html = self._to_html(table)
                    display_handle.update(HTML(html))
                except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as err:
                    log.debug(f'Rich to HTML DisplayHandle update failed: {err!r}')
                else:
                    return

            # Assume terminal/live-like handle
            else:
                try:
                    display_handle.update(table)
                except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as err:
                    log.debug(f'Rich live handle update failed: {err!r}')
                else:
                    return

        # Normal print to console
        console = ConsoleManager.get()
        console.print(table)

    def render(
        self,
        alignments: object,
        df: object,
        display_handle: object = None,
        width: int | None = None,
    ) -> object:
        """
        Render a styled table using Rich.

        Parameters
        ----------
        alignments : object
            Iterable of text-align values for columns.
        df : object
            Index-aware DataFrame to render.
        display_handle : object, default=None
            Optional environment handle for in-place updates.
        width : int | None, default=None
            Optional target table width. When set, the table is sized to
            this width so long cells wrap to fit the terminal.

        Returns
        -------
        object
            Backend-defined return value (commonly ``None``).
        """
        table = self.build_renderable(alignments, df)
        if width is not None:
            table.width = width
        self._update_display(table, display_handle)
