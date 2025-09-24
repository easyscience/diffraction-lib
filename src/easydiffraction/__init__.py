# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from importlib import import_module

from easydiffraction.utils.formatting import chapter
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import section
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import log

Logger.configure()

_LAZY_ENTRIES = [
    ('easydiffraction.analysis.analysis', 'Analysis'),
    ('easydiffraction.experiments.experiment', 'Experiment'),
    ('easydiffraction.experiments.experiments', 'Experiments'),
    ('easydiffraction.project', 'Project'),
    ('easydiffraction.project', 'ProjectInfo'),
    ('easydiffraction.sample_models.sample_model', 'SampleModel'),
    ('easydiffraction.sample_models.sample_models', 'SampleModels'),
    ('easydiffraction.summary', 'Summary'),
    ('easydiffraction.utils.utils', 'download_from_repository'),
    ('easydiffraction.utils.utils', 'fetch_tutorials'),
    ('easydiffraction.utils.utils', 'list_tutorials'),
    ('easydiffraction.utils.utils', 'get_value_from_xye_header'),
    ('easydiffraction.utils.utils', 'show_version'),
]

_LAZY_MAP = {attr_name: module_name for module_name, attr_name in _LAZY_ENTRIES}

__all__ = list(_LAZY_MAP.keys()) + [
    'Logger',
    'log',
    'chapter',
    'section',
    'paragraph',
]


def __getattr__(name):
    if name not in _LAZY_MAP:
        raise AttributeError()
    module_name = _LAZY_MAP[name]
    module = import_module(module_name)
    attr = getattr(module, name)
    return attr
