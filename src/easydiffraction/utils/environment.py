# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Runtime environment detection and artifact-path resolution."""

from __future__ import annotations

import os
import sys
import tempfile
from enum import StrEnum
from importlib.util import find_spec
from pathlib import Path

_ARTIFACT_ROOT_ENV_VAR = 'EASYDIFFRACTION_ARTIFACT_ROOT'
_PIXI_PROJECT_ROOT_ENV_VAR = 'PIXI_PROJECT_ROOT'
_FIGURE_EMBED_MODE_ENV_VAR = 'EASYDIFFRACTION_FIGURE_EMBED_MODE'
_TUTORIALS_DIR = Path('docs') / 'docs' / 'tutorials'
_TUTORIAL_ARTIFACT_ROOT = Path('tmp') / 'tutorials'


def _repo_root() -> Path | None:
    project_root = os.environ.get(_PIXI_PROJECT_ROOT_ENV_VAR)
    if project_root:
        return Path(project_root).resolve()

    for parent in Path(__file__).resolve().parents:
        if (parent / 'pixi.toml').is_file() and (parent / _TUTORIALS_DIR).is_dir():
            return parent

    return None


def _tutorial_artifact_root() -> Path | None:
    repo_root = _repo_root()
    if repo_root is None:
        return None

    tutorials_dir = (repo_root / _TUTORIALS_DIR).resolve()
    cwd = Path.cwd().resolve()
    if not cwd.is_relative_to(tutorials_dir):
        return None

    return (repo_root / _TUTORIAL_ARTIFACT_ROOT).resolve()


def _artifact_root() -> Path | None:
    artifact_root = os.environ.get(_ARTIFACT_ROOT_ENV_VAR)
    if not artifact_root:
        return _tutorial_artifact_root()

    root = Path(artifact_root)
    if root.is_absolute():
        return root.resolve()

    project_root = os.environ.get(_PIXI_PROJECT_ROOT_ENV_VAR)
    if project_root:
        return (Path(project_root) / root).resolve()

    return (Path.cwd() / root).resolve()


def in_pytest() -> bool:
    """
    Determine whether the code is running inside a pytest session.

    Returns
    -------
    bool
        True if pytest is loaded, False otherwise.
    """
    return 'pytest' in sys.modules


def in_warp() -> bool:
    """
    Determine whether the terminal is the Warp terminal emulator.

    Returns
    -------
    bool
        True if the TERM_PROGRAM environment variable equals
        ``'WarpTerminal'``, False otherwise.
    """
    return os.getenv('TERM_PROGRAM') == 'WarpTerminal'


def in_pycharm() -> bool:
    """
    Check whether the current environment is PyCharm.

    Returns
    -------
    bool
        True if running inside PyCharm, False otherwise.
    """
    return os.environ.get('PYCHARM_HOSTED') == '1'


def in_colab() -> bool:
    """
    Check whether the current environment is Google Colab.

    Returns
    -------
    bool
        True if running in Google Colab, False otherwise.
    """
    try:
        return find_spec('google.colab') is not None
    except ModuleNotFoundError:  # pragma: no cover - importlib edge case
        return False


def in_jupyter() -> bool:
    """
    Return True when running inside a Jupyter Notebook.

    Returns
    -------
    bool
        True if inside a Jupyter Notebook, False otherwise.
    """
    try:
        import IPython  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError:  # pragma: no cover - optional dependency
        ipython_mod = None
    else:
        ipython_mod = IPython
    if ipython_mod is None or in_pycharm():
        return False
    if in_colab():
        return True

    try:
        ip = ipython_mod.get_ipython()  # type: ignore[attr-defined]
        if ip is None:
            return False
        # Prefer config-based detection when available (works with
        # tests).
        has_cfg = hasattr(ip, 'config') and isinstance(ip.config, dict)
        if has_cfg and 'IPKernelApp' in ip.config:  # type: ignore[index]
            return True
        # Jupyter or qtconsole use ZMQInteractiveShell
        return ip.__class__.__name__ == 'ZMQInteractiveShell'  # noqa: TRY300
    except (NameError, AttributeError):
        return False


def in_github_ci() -> bool:
    """
    Return True when running under GitHub Actions CI.

    Returns
    -------
    bool
        True if env var ``GITHUB_ACTIONS`` is set, False otherwise.
    """
    return os.environ.get('GITHUB_ACTIONS') is not None


def resolve_artifact_path(path: str | Path) -> Path:
    """
    Resolve a path against the configured artifact root.

    Parameters
    ----------
    path : str | Path
        Path to resolve.

    Returns
    -------
    Path
        The original path when no artifact root is configured or when
        *path* is absolute. Otherwise, the absolute path under the
        configured artifact root.
    """
    resolved_path = Path(path)
    artifact_root = _artifact_root()
    if artifact_root is None or resolved_path.is_absolute():
        return resolved_path

    return (artifact_root / resolved_path).resolve()


def create_artifact_temp_dir(prefix: str) -> Path:
    """
    Create a temporary directory under the artifact root when set.

    Parameters
    ----------
    prefix : str
        Prefix for the temporary directory name.

    Returns
    -------
    Path
        Path to the created temporary directory.
    """
    artifact_root = _artifact_root()
    if artifact_root is None:
        return Path(tempfile.mkdtemp(prefix=prefix))

    artifact_root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=artifact_root)).resolve()


# ----------------------------------------------------------------------
# Figure embedding mode
# ----------------------------------------------------------------------


class FigureEmbedMode(StrEnum):
    """
    How interactive figure HTML embeds its JavaScript runtime.

    ``INLINE`` renders eagerly for live Jupyter; ``SHARED`` emits a lazy
    placeholder activated by a once-per-page shared runtime for the docs
    site; ``STANDALONE`` renders an eager self-contained fragment for
    reports, with runtime delivery decided by the caller's ``offline``
    flag.
    """

    INLINE = 'inline'
    SHARED = 'shared'
    STANDALONE = 'standalone'


def resolve_figure_embed_mode() -> FigureEmbedMode:
    """
    Resolve the active figure embedding mode from the environment.

    Reads ``EASYDIFFRACTION_FIGURE_EMBED_MODE``. An unset or empty value
    resolves to :attr:`FigureEmbedMode.INLINE`. Any other value must
    name a supported mode; an unknown value raises ``ValueError`` so a
    typo in a docs or CI environment fails the build loudly instead of
    silently falling back to eager output.

    Returns
    -------
    FigureEmbedMode
        The resolved embedding mode.

    Raises
    ------
    ValueError
        If the variable is set to a non-empty value that is not a
        supported mode.
    """
    raw = os.environ.get(_FIGURE_EMBED_MODE_ENV_VAR, '').strip()
    if not raw:
        return FigureEmbedMode.INLINE
    try:
        return FigureEmbedMode(raw.lower())
    except ValueError:
        supported = ', '.join(mode.value for mode in FigureEmbedMode)
        message = f'Invalid {_FIGURE_EMBED_MODE_ENV_VAR}={raw!r}; supported values: {supported}.'
        raise ValueError(message) from None


# ----------------------------------------------------------------------
# IPython/Jupyter helpers
# ----------------------------------------------------------------------


def is_ipython_display_handle(obj: object) -> bool:
    """
    Return True if ``obj`` is an IPython DisplayHandle instance.

    Tries to import ``IPython.display.DisplayHandle`` and uses
    ``isinstance`` when available. Falls back to a conservative module
    name heuristic if IPython is missing. Any errors result in
    ``False``.
    """
    try:  # Fast path when IPython is available
        from IPython.display import (  # noqa: PLC0415
            DisplayHandle,  # type: ignore[import-not-found]
        )

        try:
            return isinstance(obj, DisplayHandle)
        except TypeError:
            return False
    except ImportError:
        # Fallback heuristic when IPython is unavailable
        try:
            mod = getattr(getattr(obj, '__class__', None), '__module__', '')
            return isinstance(mod, str) and mod.startswith('IPython')
        except (TypeError, AttributeError):
            return False


def can_update_ipython_display() -> bool:
    """
    Return True if IPython HTML display utilities are available.

    This indicates we can safely construct ``IPython.display.HTML`` and
    update a display handle.
    """
    try:
        pass  # type: ignore[import-not-found]
    except ImportError:
        return False
    else:
        return True


def can_use_ipython_display(handle: object) -> bool:
    """
    Return True if we can update the given IPython DisplayHandle.

    Combines type checking of the handle with availability of IPython
    HTML utilities.
    """
    try:
        return is_ipython_display_handle(handle) and can_update_ipython_display()
    except (ImportError, TypeError, AttributeError):
        return False
