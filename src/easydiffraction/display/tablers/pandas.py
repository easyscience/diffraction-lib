# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Pandas-input table renderer emitting inline-styled HTML for notebooks.
"""

from __future__ import annotations

import html
import re

try:
    from IPython.display import HTML
    from IPython.display import display
except ImportError:
    HTML = None
    display = None

from easydiffraction.display.tablers.base import TableBackendBase
from easydiffraction.utils.environment import can_use_ipython_display
from easydiffraction.utils.logging import log

# Rich-style inline colour markup, e.g. ``[red]text[/red]``.
_RICH_COLOR_RE = re.compile(r'\[(\w+)\](.*?)\[/\1\]')

# Theme-neutral translucent greys. Both read correctly on light and dark
# backgrounds, so the table needs no theme-sync script -- which matters
# because JupyterLab strips ``<style>``/``<script>`` from untrusted
# (reopened, not yet re-run) cell outputs. Inline values like these
# survive that sanitisation, so a saved notebook shows the themed table
# without re-execution.
BORDER_COLOR = 'rgba(128, 128, 128, 0.4)'
INDEX_COLOR = 'rgba(128, 128, 128, 0.7)'

# Compact cell metrics matching the Rich layout. ``border: 0`` and
# ``min-width: 0`` neutralise MkDocs Material's ``table:not([class])``
# rules, which otherwise inject a per-row ``border-top`` (stray rules
# between rows) and ``th { min-width: 5rem }`` (over-wide columns) onto
# class-less embedded tables. ``white-space: nowrap`` keeps each cell on
# one line so a wide table scrolls horizontally rather than folding into
# multi-line rows. Inline values win over the theme stylesheet, so no
# CSS class or ``<style>`` block is needed.
_CELL_STYLE = (
    'padding: 0.25em 0.5em; line-height: 1.15em; border: 0; min-width: 0; white-space: nowrap'
)
_TRANSPARENT_ROW = 'background-color: transparent'


class PandasTableBackend(TableBackendBase):
    """
    Render tables as inline-styled HTML for Jupyter notebooks.

    Every style is inlined on the table elements rather than collected
    in a pandas ``Styler`` ``<style>`` block. Inline styles survive
    JupyterLab's untrusted-output sanitisation, so a saved notebook
    reopened before re-execution still shows the themed table instead of
    falling back to the host default (bold index, row striping).
    """

    def _cell_html(self, value: object) -> tuple[str, str | None]:
        """
        Return escaped cell text and an optional colour override.

        Parameters
        ----------
        value : object
            Raw cell value. May carry Rich markup (``[red]text[/red]``).

        Returns
        -------
        tuple[str, str | None]
            HTML-escaped text and a CSS colour (``None`` when absent).
        """
        text = self._format_value(value)
        match = _RICH_COLOR_RE.fullmatch(text)
        colour = None
        if match is not None:
            colour, text = match.groups()
        return html.escape(text), colour

    def _cell_td(self, value: object, align: str) -> str:
        """
        Return one data ``<td>`` with inline alignment and colour.

        Parameters
        ----------
        value : object
            Raw cell value.
        align : str
            CSS ``text-align`` value for the column.

        Returns
        -------
        str
            Inline-styled ``<td>`` element.
        """
        text, colour = self._cell_html(value)
        colour_css = f'; color: {colour}' if colour else ''
        return f'<td style="{_CELL_STYLE}; text-align: {align}{colour_css}">{text}</td>'

    def _build_html(self, alignments: object, df: object) -> str:
        """
        Build inline-styled HTML for the provided table.

        Parameters
        ----------
        alignments : object
            Per-column text alignments (e.g. ``'left'``/``'right'``).
        df : object
            Index-aware DataFrame whose index is shown as the first
            column.

        Returns
        -------
        str
            Self-contained HTML table with all styling inlined.
        """
        columns = list(df.columns)
        aligns = list(alignments)
        border = f'1px solid {BORDER_COLOR}'
        header = f'{_CELL_STYLE}; border-bottom: {border}; font-weight: bold'
        index = f'{_CELL_STYLE}; color: {INDEX_COLOR}; font-weight: normal; text-align: right'
        # ``display: table`` overrides MkDocs Material's
        # ``table:not([class]) { display: inline-block }`` rule. Left as
        # inline-block the table drops out of the collapsing-border
        # model, so the header's translucent ``border-bottom`` stacks
        # into a darker line than the outer border and stops one pixel
        # short of the right edge. The wrapping ``overflow-x: auto`` div
        # (added below) restores the horizontal scrolling that
        # Material's ``inline-block`` would otherwise have provided for
        # wide tables.
        table_style = (
            f'border: {border}; border-collapse: collapse; display: table; '
            f'margin-top: 0.5em; margin-left: 0.5em'
        )

        header_cells = ''.join(
            f'<th style="{header}; text-align: {align}">{html.escape(str(column))}</th>'
            for column, align in zip(columns, aligns, strict=False)
        )
        # ``border-bottom: 0`` neutralises hosts (e.g. JupyterLab's
        # ``.jp-RenderedHTMLCommon thead``) that paint an opaque header
        # rule on the thead element. Left in place that rule wins the
        # border collapse and recolours the divider; zeroing it keeps
        # the header/body divider the same translucent grey as the outer
        # border, sourced only from the header cells' ``border-bottom``.
        head = (
            f'<table style="{table_style}">'
            f'<thead style="border-bottom: 0"><tr style="{_TRANSPARENT_ROW}">'
            f'<th style="{header}"></th>{header_cells}</tr></thead><tbody>'
        )
        parts = [head]
        for idx, row in df.iterrows():
            cells = ''.join(
                self._cell_td(row[column], align)
                for column, align in zip(columns, aligns, strict=False)
            )
            index_cell = f'<th style="{index}">{html.escape(str(idx))}</th>'
            parts.append(f'<tr style="{_TRANSPARENT_ROW}">{index_cell}{cells}</tr>')
        parts.append('</tbody></table>')
        return f'<div style="overflow-x: auto; max-width: 100%">{"".join(parts)}</div>'

    def build_renderable(self, alignments: object, df: object) -> object:
        """
        Build notebook HTML for the provided table.

        Parameters
        ----------
        alignments : object
            Per-column text alignments.
        df : object
            Index-aware DataFrame whose index is shown as the first
            column.

        Returns
        -------
        object
            Inline-styled HTML string for the table.
        """
        return self._build_html(alignments, df)

    def render(
        self,
        alignments: object,
        df: object,
        display_handle: object | None = None,
        width: int | None = None,
    ) -> object:
        """
        Render an inline-styled HTML table in Jupyter.

        Parameters
        ----------
        alignments : object
            Per-column text alignments.
        df : object
            Index-aware DataFrame whose index is shown as the first
            column.
        display_handle : object | None, default=None
            Optional IPython DisplayHandle for in-place updates.
        width : int | None, default=None
            Ignored. HTML tables reflow to the available width.

        Returns
        -------
        object
            ``None``; the table is displayed as a side effect.
        """
        del width
        self._display(self._build_html(alignments, df), display_handle)

    @staticmethod
    def _display(html_table: str, display_handle: object | None) -> None:
        """
        Display the HTML, updating an existing area when possible.

        Parameters
        ----------
        html_table : str
            Inline-styled HTML table to display.
        display_handle : object | None
            Optional IPython DisplayHandle for in-place updates.
        """
        if HTML is None:
            return
        if (
            display_handle is not None
            and hasattr(display_handle, 'update')
            and can_use_ipython_display(display_handle)
        ):
            try:
                display_handle.update(HTML(html_table))
            except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as err:
                log.debug(f'Pandas DisplayHandle update failed: {err!r}')
            else:
                return
        display(HTML(html_table))
