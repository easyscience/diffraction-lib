# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""EasyDiffraction public API for diffraction analysis."""

from __future__ import annotations

from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.datablocks.structure.item.factory import StructureFactory

# Imported for its side effect: in a live notebook this loads the
# self-hosted interactive-plot runtime once at import time, so Plotly
# figures render instantly (no per-plot runtime or reserved blank box).
from easydiffraction.display.plotters import notebook_preload as _notebook_preload
from easydiffraction.io.ascii import extract_data_paths_from_dir
from easydiffraction.io.ascii import extract_data_paths_from_zip
from easydiffraction.io.ascii import extract_metadata
from easydiffraction.io.ascii import extract_project_from_zip
from easydiffraction.project.project import Project
from easydiffraction.utils import matplotlib_config as _matplotlib_config
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import download_all_tutorials
from easydiffraction.utils.utils import download_data
from easydiffraction.utils.utils import download_tutorial
from easydiffraction.utils.utils import list_data
from easydiffraction.utils.utils import list_tutorials
from easydiffraction.utils.utils import show_version
