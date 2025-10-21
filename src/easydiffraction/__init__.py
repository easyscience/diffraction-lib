# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from importlib import import_module

from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log

Logger.configure()

_LAZY_ENTRIES = [
    ('easydiffraction.project.project', 'Project'),
    ('easydiffraction.experiments.experiment.factory', 'ExperimentFactory'),
    ('easydiffraction.sample_models.sample_model.factory', 'SampleModelFactory'),
    ('easydiffraction.utils.utils', 'download_from_repository'),
    ('easydiffraction.utils.utils', 'fetch_tutorials'),
    ('easydiffraction.utils.utils', 'list_tutorials'),
    ('easydiffraction.utils.utils', 'get_value_from_xye_header'),
    ('easydiffraction.utils.utils', 'show_version'),
]

_LAZY_MAP = {attr_name: module_name for module_name, attr_name in _LAZY_ENTRIES}

__all__ = list(_LAZY_MAP.keys()) + ['Logger', 'log', 'console']


def __getattr__(name):
    if name not in _LAZY_MAP:
        raise AttributeError()
    module_name = _LAZY_MAP[name]
    module = import_module(module_name)
    attr = getattr(module, name)
    return attr
