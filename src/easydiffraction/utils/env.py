# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
from importlib.util import find_spec


def is_pycharm() -> bool:
    """Determines if the current environment is PyCharm.

    Returns:
        bool: True if running inside PyCharm, False otherwise.
    """
    return os.environ.get('PYCHARM_HOSTED') == '1'


def is_colab() -> bool:
    """Determines if the current environment is Google Colab.

    Returns:
        bool: True if running in Google Colab, False otherwise.
    """
    try:
        return find_spec('google.colab') is not None
    except ModuleNotFoundError:  # pragma: no cover - importlib edge case
        return False


def is_notebook() -> bool:
    """Return True when running inside a Jupyter Notebook.

    Returns:
        bool: True if inside a Jupyter Notebook, False otherwise.
    """
    try:
        import IPython  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - optional dependency
        ipython_mod = None
    else:
        ipython_mod = IPython
    if ipython_mod is None:
        return False
    if is_pycharm():
        return False
    if is_colab():
        return True

    try:
        ip = ipython_mod.get_ipython()  # type: ignore[attr-defined]
        if ip is None:
            return False
        # Prefer config-based detection when available (works with tests).
        has_cfg = hasattr(ip, 'config') and isinstance(getattr(ip, 'config'), dict)
        if has_cfg and 'IPKernelApp' in ip.config:  # type: ignore[index]
            return True
        shell = ip.__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter or qtconsole
            return True
        if shell == 'TerminalInteractiveShell':
            return False
        return False
    except Exception:
        return False


def is_github_ci() -> bool:
    """Return True when running under GitHub Actions CI.

    Returns:
        bool: True if env var ``GITHUB_ACTIONS`` is set, False otherwise.
    """
    return os.environ.get('GITHUB_ACTIONS') is not None
