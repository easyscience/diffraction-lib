from __future__ import annotations

from typing import Any

from rich.box import Box
from rich.console import Console
from rich.table import Table

from easydiffraction.display.tablers.base import TableBackendBase

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
# box.SQUARE:
# ┌─┬┐ top
# │ ││ head
# ├─┼┤ head_row
# │ ││ mid
# ├─┼┤ foot_row
# ├─┼┤ foot_row
# │ ││ foot
# └─┴┘ bottom


class RichTableBackend(TableBackendBase):
    def __init__(self) -> None:
        super().__init__()
        self.console = Console(
            force_jupyter=False,
        )

    @property
    def _box(self):
        return Box(
            CUSTOM_BOX,
            ascii=False,
        )

    def render(
        self,
        alignments,
        df,
    ) -> Any:
        color = self._rich_border_color

        table = Table(
            title=None,
            box=self._box,
            show_header=True,
            header_style='bold',
            border_style=color,
        )

        # Add index column header first
        table.add_column(justify='right', style=color)

        # Add other column headers with alignment
        for col, align in zip(df, alignments, strict=False):
            table.add_column(str(col), justify=align)

        # Add rows (prepend the index value as first column)
        for idx, row_values in df.iterrows():
            formatted_row = [self._format_value(val) for val in row_values]
            table.add_row(str(idx), *formatted_row)

        # Display the table
        self.console.print(table)
