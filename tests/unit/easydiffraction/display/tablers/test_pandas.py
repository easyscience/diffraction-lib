# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tablers/pandas.py (PandasTableBackend)."""

import pandas as pd
import pytest


class TestPandasTableBackend:
    def test_build_base_styles(self):
        from easydiffraction.display.tablers.pandas import PANDAS_AXIS_FRAME_COLOR
        from easydiffraction.display.tablers.pandas import PandasTableBackend

        backend = PandasTableBackend()
        styles = backend._build_base_styles(PANDAS_AXIS_FRAME_COLOR)
        assert isinstance(styles, list)
        assert len(styles) > 0
        selectors = [s['selector'] for s in styles]
        assert 'thead' in selectors
        assert any(
            PANDAS_AXIS_FRAME_COLOR in value for style in styles for _, value in style['props']
        )

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
        from easydiffraction.display.tablers.pandas import PANDAS_TABLE_THEME_CLASS
        from easydiffraction.display.tablers.pandas import PandasTableBackend
        from easydiffraction.display.theme import TABLE_AXIS_FRAME_CSS_VAR

        pytest.importorskip('jinja2')
        backend = PandasTableBackend()
        df = pd.DataFrame({'A': [1.0], 'B': [2.0]})

        html = backend.build_renderable(['left', 'right'], df)

        assert isinstance(html, str)
        assert '<table' in html
        assert PANDAS_TABLE_THEME_CLASS in html
        assert TABLE_AXIS_FRAME_CSS_VAR in html
        assert 'window.__edPandasTableThemeObserverInstalled' in html
