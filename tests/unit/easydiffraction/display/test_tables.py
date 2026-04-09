# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tables.py (TableEngineEnum, TableRenderer, TableRendererFactory)."""

import pandas as pd


class TestTableEngineEnum:
    def test_members(self):
        from easydiffraction.display.tables import TableEngineEnum

        assert TableEngineEnum.RICH == 'rich'
        assert TableEngineEnum.PANDAS == 'pandas'

    def test_default_outside_jupyter(self):
        from easydiffraction.display.tables import TableEngineEnum

        # Outside Jupyter, default is RICH
        assert TableEngineEnum.default() is TableEngineEnum.RICH

    def test_descriptions(self):
        from easydiffraction.display.tables import TableEngineEnum

        for member in TableEngineEnum:
            desc = member.description()
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestTableRendererFactory:
    def test_registry_outside_jupyter(self):
        from easydiffraction.display.tables import TableRendererFactory

        registry = TableRendererFactory._registry()
        assert 'rich' in registry
        # Pandas not available outside Jupyter
        assert 'pandas' not in registry

    def test_supported_engines(self):
        from easydiffraction.display.tables import TableRendererFactory

        engines = TableRendererFactory.supported_engines()
        assert 'rich' in engines


class TestTableRenderer:
    def test_render(self, monkeypatch, capsys):
        from easydiffraction.display.tables import TableRenderer

        # Reset singleton
        monkeypatch.setattr(TableRenderer, '_instance', None)

        headers = [('Col', 'left')]
        df = pd.DataFrame([['val']], columns=pd.MultiIndex.from_tuples(headers))
        renderer = TableRenderer.get()
        renderer.render(df)
        out = capsys.readouterr().out
        assert len(out) > 0

        # Reset singleton to not leak state
        monkeypatch.setattr(TableRenderer, '_instance', None)
