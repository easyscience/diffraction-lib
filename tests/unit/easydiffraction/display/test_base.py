# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/base.py (RendererBase and RendererFactoryBase)."""

import pytest

from easydiffraction.display.base import RendererFactoryBase


class _StubBackend:
    pass


class _StubFactory(RendererFactoryBase):
    @classmethod
    def _registry(cls):
        return {
            'stub': {'description': 'Stub engine', 'class': _StubBackend},
        }


class TestRendererFactoryBase:
    def test_create_valid(self):
        obj = _StubFactory.create('stub')
        assert isinstance(obj, _StubBackend)

    def test_create_invalid_raises(self):
        with pytest.raises(ValueError, match='Unsupported engine'):
            _StubFactory.create('nonexistent')

    def test_supported_engines(self):
        engines = _StubFactory.supported_engines()
        assert engines == ['stub']

    def test_descriptions(self):
        desc = _StubFactory.descriptions()
        assert desc == [('stub', 'Stub engine')]
