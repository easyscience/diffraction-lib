from __future__ import annotations

from typing import Any

from easydiffraction import log
from easydiffraction.display.tablers.base import TableBackendBase

try:
    from IPython.display import display
except ImportError:
    display = None


class PandasTableBackend(TableBackendBase):
    def render(
        self,
        alignments,
        df,
    ) -> Any:
        color = self._pandas_border_color

        # Base table styles
        table_styles = [
            # Outer border on the entire table
            {
                'selector': ' ',
                'props': [
                    ('border', f'1px solid {color}'),
                    ('border-collapse', 'collapse'),
                ],
            },
            # Horizontal border under header row
            {
                'selector': 'thead',
                'props': [
                    ('border-bottom', f'1px solid {color}'),
                ],
            },
            # Remove all cell borders
            {
                'selector': 'th, td',
                'props': [
                    ('border', 'none'),
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
        ]

        # Add per-column alignment styles for headers
        header_alignment_styles = [
            {
                'selector': f'th.col{df.columns.get_loc(column)}',
                'props': [('text-align', align)],
            }
            for column, align in zip(df.columns, alignments, strict=False)
        ]

        # Apply float formatting
        styler = df.style.format(precision=self.FLOAT_PRECISION)

        # Apply table styles including header alignment
        styler = styler.set_table_styles(table_styles + header_alignment_styles)

        # Apply per-column alignment for data cells
        for column, align in zip(df.columns, alignments, strict=False):
            styler = styler.set_properties(
                subset=[column],
                **{'text-align': align},
            )

        # Display the styled DataFrame
        if display is not None:
            display(styler)
        else:
            log.print(styler)
