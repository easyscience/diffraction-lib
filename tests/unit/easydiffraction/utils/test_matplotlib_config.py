# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_path_is_writable_accepts_temporary_directory(tmp_path):
    from easydiffraction.utils.matplotlib_config import _path_is_writable

    assert _path_is_writable(tmp_path / 'cache') is True


def test_ensure_matplotlib_config_dir_keeps_existing_env(monkeypatch):
    from easydiffraction.utils import matplotlib_config

    monkeypatch.setenv('MPLCONFIGDIR', 'configured')

    matplotlib_config.ensure_matplotlib_config_dir()

    assert matplotlib_config.os.environ['MPLCONFIGDIR'] == 'configured'


def test_ensure_matplotlib_config_dir_uses_temp_fallback(monkeypatch, tmp_path):
    from easydiffraction.utils import matplotlib_config

    calls = []

    def fake_path_is_writable(path):
        calls.append(path)
        return len(calls) == 2

    monkeypatch.delenv('MPLCONFIGDIR', raising=False)
    monkeypatch.setattr(
        matplotlib_config.pathlib.Path,
        'home',
        staticmethod(lambda: tmp_path / 'home'),
    )
    monkeypatch.setattr(matplotlib_config.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(matplotlib_config, '_path_is_writable', fake_path_is_writable)

    matplotlib_config.ensure_matplotlib_config_dir()

    assert calls == [
        tmp_path / 'home' / '.matplotlib',
        tmp_path / 'easydiffraction-matplotlib',
    ]
    assert matplotlib_config.os.environ['MPLCONFIGDIR'] == str(
        tmp_path / 'easydiffraction-matplotlib'
    )
