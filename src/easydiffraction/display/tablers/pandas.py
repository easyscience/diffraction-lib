# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Pandas-based table renderer for notebooks using DataFrame Styler."""

from __future__ import annotations

try:
    from IPython.display import HTML
    from IPython.display import display
except ImportError:
    HTML = None
    display = None

from easydiffraction.display.tablers.base import TableBackendBase
from easydiffraction.utils.environment import can_use_ipython_display
from easydiffraction.utils.logging import log


class PandasTableBackend(TableBackendBase):
    """Render tables using the pandas Styler in Jupyter environments."""

    @staticmethod
    def _build_base_styles(color: str) -> list[dict]:
        """
        Return base CSS table styles for a given border color.

        Parameters
        ----------
        color : str
            CSS color value (e.g., ``#RRGGBB``) to use for borders and
            header accents.

        Returns
        -------
        list[dict]
            A list of ``Styler.set_table_styles`` dictionaries.
        """
        return [
            # Margins and outer border on the entire table
            {
                'selector': ' ',
                'props': [
                    ('border', f'1px solid {color}'),
                    ('border-collapse', 'collapse'),
                    ('margin-top', '0.5em'),
                    ('margin-left', '0.5em'),
                ],
            },
            # Horizontal border under header row
            {
                'selector': 'thead',
                'props': [
                    ('border-bottom', f'1px solid {color}'),
                ],
            },
            # Cell border, padding and line height
            {
                'selector': 'th, td',
                'props': [
                    ('border', 'none'),
                    ('padding-top', '0.25em'),
                    ('padding-bottom', '0.25em'),
                    ('line-height', '1.15em'),
                ],
            },
            # Style for index column
            {
                'selector': 'th.row_heading',
                'props': [
                    ('color', color),
                    ('font-weight', 'normal'),
                ],
            },
            # Remove zebra-row background
            {
                'selector': 'tbody tr:nth-child(odd), tbody tr:nth-child(even)',
                'props': [
                    ('background-color', 'transparent'),
                ],
            },
        ]

    @staticmethod
    def _build_header_alignment_styles(df: object, alignments: object) -> list[dict]:
        """
        Generate header cell alignment styles per column.

        Parameters
        ----------
        df : object
            DataFrame whose columns are being rendered.
        alignments : object
            Iterable of text alignment values (e.g., ``'left'``,
            ``'center'``) matching ``df`` columns.

        Returns
        -------
        list[dict]
            A list of CSS rules for header cell alignment.
        """
        return [
            {
                'selector': f'th.col{df.columns.get_loc(column)}',
                'props': [('text-align', align)],
            }
            for column, align in zip(df.columns, alignments, strict=False)
        ]

    def _apply_styling(self, df: object, alignments: object, color: str) -> object:
        """
        Build a configured Styler with alignments and base styles.

        Parameters
        ----------
        df : object
            DataFrame to style.
        alignments : object
            Iterable of text alignment values for columns.
        color : str
            CSS color value used for borders/header.

        Returns
        -------
        object
            A configured pandas Styler ready for display.
        """
        table_styles = self._build_base_styles(color)
        header_alignment_styles = self._build_header_alignment_styles(df, alignments)

        styler = df.style.format(precision=self.FLOAT_PRECISION)
        styler = styler.set_table_attributes('class="dataframe"')  # For mkdocs-jupyter
        styler = styler.set_table_styles(table_styles + header_alignment_styles)

        for column, align in zip(df.columns, alignments, strict=False):
            styler = styler.set_properties(
                subset=[column],
                **{'text-align': align},
            )
        return styler

    @staticmethod
    def _update_display(styler: object, display_handle: object) -> None:
        """
        Single, consistent update path for Jupyter.

        If a handle with ``update()`` is provided and it's a
        DisplayHandle, update the output area in-place using HTML.
        Otherwise, display once via IPython ``display()``.

        Parameters
        ----------
        styler : object
            Configured DataFrame Styler to be rendered.
        display_handle : object
            Optional IPython DisplayHandle used for in-place updates.
        """
        # Handle with update() method
        if display_handle is not None and hasattr(display_handle, 'update'):
            # IPython DisplayHandle path
            if can_use_ipython_display(display_handle) and HTML is not None:
                try:
                    html = styler.to_html()
                    display_handle.update(HTML(html))
                except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as err:
                    log.debug(f'Pandas DisplayHandle update failed: {err!r}')
                else:
                    return

            # This should not happen in Pandas backend
            else:
                pass

        # Normal display
        display(styler)

    def render(
        self,
        alignments: object,
        df: object,
        display_handle: object | None = None,
    ) -> object:
        """
        Render a styled DataFrame.

        Parameters
        ----------
        alignments : object
            Iterable of column justifications (e.g. 'left').
        df : object
            DataFrame whose index is displayed as the first column.
        display_handle : object | None, default=None
            Optional IPython DisplayHandle to update an existing output
            area in place when running in Jupyter.

        Returns
        -------
        object
            Backend-defined return value (commonly ``None``).
        """
        color = self._pandas_border_color
        styler = self._apply_styling(df, alignments, color)
        self._update_display(styler, display_handle)
