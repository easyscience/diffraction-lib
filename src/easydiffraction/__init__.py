# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import pathlib
import tempfile


def _path_is_writable(path: pathlib.Path) -> bool:
    """
    Return whether a directory can be used for runtime cache files.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / '.easydiffraction-write-test'
        probe.write_text('', encoding='utf-8')
        probe.unlink()
    except OSError:
        return False
    return True


def _ensure_matplotlib_config_dir() -> None:
    """
    Set a stable Matplotlib cache dir when the default is unusable.
    """
    if os.environ.get('MPLCONFIGDIR'):
        return
    default_dir = pathlib.Path.home() / '.matplotlib'
    if _path_is_writable(default_dir):
        return
    fallback_dir = pathlib.Path(tempfile.gettempdir()) / 'easydiffraction-matplotlib'
    if _path_is_writable(fallback_dir):
        os.environ['MPLCONFIGDIR'] = str(fallback_dir)


_ensure_matplotlib_config_dir()

from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.datablocks.structure.item.factory import StructureFactory
from easydiffraction.io.ascii import extract_data_paths_from_dir
from easydiffraction.io.ascii import extract_data_paths_from_zip
from easydiffraction.io.ascii import extract_metadata
from easydiffraction.io.ascii import extract_project_from_zip
from easydiffraction.project.project import Project
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import download_all_tutorials
from easydiffraction.utils.utils import download_data
from easydiffraction.utils.utils import download_tutorial
from easydiffraction.utils.utils import list_data
from easydiffraction.utils.utils import list_tutorials
from easydiffraction.utils.utils import show_version
