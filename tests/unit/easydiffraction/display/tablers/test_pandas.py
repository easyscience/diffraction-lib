# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tablers/pandas.py (PandasTableBackend)."""

import pandas as pd
import pytest


class TestPandasTableBackend:
    def test_build_base_styles(self):
        from easydiffraction.display.tablers.pandas import PandasTableBackend

        backend = PandasTableBackend()
        styles = backend._build_base_styles('#aabbcc')
        assert isinstance(styles, list)
        assert len(styles) > 0
        selectors = [s['selector'] for s in styles]
        assert 'thead' in selectors

    def test_build_header_alignment_styles(self):
        from easydiffraction.display.tablers.pandas import PandasTableBackend

        backend = PandasTableBackend()
        df = pd.DataFrame({'A': [1], 'B': [2]})
        styles = backend._build_header_alignment_styles(df, ['left', 'right'])
        assert len(styles) == 2

    def test_apply_styling_returns_styler(self):
        from easydiffraction.display.tablers.pandas import PandasTableBackend

        pytest.importorskip('jinja2')
        backend = PandasTableBackend()
        df = pd.DataFrame({'A': [1.0], 'B': [2.0]})
        styler = backend._apply_styling(df, ['left', 'right'], '#aabbcc')
        assert hasattr(styler, 'to_html')

    def test_build_renderable_returns_html(self):
        from easydiffraction.display.tablers.pandas import PandasTableBackend

        pytest.importorskip('jinja2')
        backend = PandasTableBackend()
        df = pd.DataFrame({'A': [1.0], 'B': [2.0]})

        html = backend.build_renderable(['left', 'right'], df)

        assert isinstance(html, str)
        assert '<table' in html
