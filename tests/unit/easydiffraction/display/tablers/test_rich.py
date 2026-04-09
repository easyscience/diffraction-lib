# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tablers/rich.py (RichTableBackend)."""

import pandas as pd
from rich.box import Box
from rich.table import Table


class TestRichTableBackend:
    def test_rich_table_box_constant(self):
        from easydiffraction.display.tablers.rich import RICH_TABLE_BOX

        assert isinstance(RICH_TABLE_BOX, Box)

    def test_build_table_returns_table(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        df = pd.DataFrame({'Col': [1.0, 2.0]})
        df.index += 1
        table = backend._build_table(df, ['left'], 'grey35')
        assert isinstance(table, Table)

    def test_to_html_returns_string(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        df = pd.DataFrame({'Col': [1.0]})
        df.index += 1
        table = backend._build_table(df, ['left'], 'grey35')
        html = backend._to_html(table)
        assert isinstance(html, str)
        assert '<pre' in html

    def test_render_prints_to_console(self, capsys):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        df = pd.DataFrame({'Col': ['val']})
        df.index += 1
        backend.render(['left'], df)
        out = capsys.readouterr().out
        assert 'Col' in out or 'val' in out or len(out) > 0
