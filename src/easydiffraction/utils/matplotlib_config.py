# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Configure Matplotlib cache paths for restricted environments."""

from __future__ import annotations

import os
import pathlib
import tempfile


def _path_is_writable(path: pathlib.Path) -> bool:
    """Return whether runtime caches can use a directory."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / '.easydiffraction-write-test'
        probe.write_text('', encoding='utf-8')
        probe.unlink()
    except OSError:
        return False
    return True


def ensure_matplotlib_config_dir() -> None:
    """Set a stable Matplotlib cache dir."""
    if os.environ.get('MPLCONFIGDIR'):
        return
    default_dir = pathlib.Path.home() / '.matplotlib'
    if _path_is_writable(default_dir):
        return
    fallback_dir = pathlib.Path(tempfile.gettempdir()) / 'easydiffraction-matplotlib'
    if _path_is_writable(fallback_dir):
        os.environ['MPLCONFIGDIR'] = str(fallback_dir)


ensure_matplotlib_config_dir()
