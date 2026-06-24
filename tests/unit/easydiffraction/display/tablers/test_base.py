# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tablers/base.py (TableBackendBase)."""

import math


class TestTableBackendBase:
    def test_float_precision_constant(self):
        from easydiffraction.display.tablers.base import TableBackendBase

        assert TableBackendBase.FLOAT_PRECISION == 5

    def test_format_value_float(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        result = backend._format_value(math.pi)
        assert result == '3.14159'

    def test_format_value_nonf_float(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        result = backend._format_value('hello')
        assert result == 'hello'

    def test_rich_to_hex(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        hex_val = backend._rich_to_hex('red')
        assert hex_val.startswith('#')
        assert len(hex_val) == 7

    def test_is_dark_theme_outside_jupyter(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        # Outside Jupyter, default is True
        assert backend._is_dark_theme() is True

    def test_is_dark_theme_without_ipython_installed(self, monkeypatch):
        # Regression: base.py must tolerate IPython being absent (it is an
        # optional display dependency, guarded at import). Without the guard
        # `import easydiffraction` fails in a clean install.
        import easydiffraction.display.tablers.base as base_module
        from easydiffraction.display.tablers.rich import RichTableBackend

        monkeypatch.setattr(base_module, 'get_ipython', None)
        backend = RichTableBackend()
        assert backend._is_dark_theme() is True

    def test_rich_border_color_property(self):
        from easydiffraction.display.tablers.rich import RichTableBackend

        backend = RichTableBackend()
        color = backend._rich_border_color
        assert isinstance(color, str)

    def test_pandas_border_color_property(self):
        from easydiffraction.display.tablers.rich import RichTableBackend
        from easydiffraction.display.theme import DARK_AXIS_FRAME_COLOR

        backend = RichTableBackend()
        color = backend._pandas_border_color
        assert color == DARK_AXIS_FRAME_COLOR
