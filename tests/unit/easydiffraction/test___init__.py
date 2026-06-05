# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import importlib
from pathlib import Path

import pytest


def test_lazy_attributes_resolve_and_are_accessible():
    import easydiffraction as ed

    # Access a few lazy attributes; just ensure they exist and are callable/class-like
    assert hasattr(ed, 'Project')
    assert hasattr(ed, 'ExperimentFactory')
    assert hasattr(ed, 'StructureFactory')

    # Access utility functions from utils via lazy getattr
    assert callable(ed.show_version)
    assert callable(ed.extract_metadata)

    # Import once to exercise __getattr__; subsequent access should be cached by Python
    _ = ed.Project
    _ = ed.ExperimentFactory


def test___getattr__unknown_raises_attribute_error():
    ed = importlib.import_module('easydiffraction')
    with pytest.raises(AttributeError):
        ed.DefinitelyUnknownAttribute


def test_lazy_functions_execute_with_monkeypatch(monkeypatch, capsys, tmp_path):
    import easydiffraction as ed
    from easydiffraction.utils import utils

    # 1) list_tutorials uses _fetch_tutorials_index → monkeypatch there
    fake_tutorial_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
            'title': 'Quick Start',
            'description': 'A quick start tutorial',
        },
    }
    monkeypatch.setattr(utils, '_fetch_tutorials_index', lambda: fake_tutorial_index)
    monkeypatch.setattr(utils, '_get_version_for_url', lambda: '0.8.0')
    ed.list_tutorials()  # calls into utils.list_tutorials
    out = capsys.readouterr().out
    assert 'Tutorials available for easydiffraction' in out

    # 2) download_data should consult index and call pooch.retrieve without network
    from easydiffraction.utils import utils

    fake_index = {
        '12': {
            'path': 'data.xye',
            'hash': 'sha256:...',
            'description': 'Demo dataset',
        }
    }
    monkeypatch.setattr(utils, '_fetch_data_index', lambda: fake_index)

    calls: dict = {}

    def fake_retrieve(**kwargs):
        calls['kwargs'] = kwargs
        file_path = Path(kwargs['path']) / kwargs['fname']
        file_path.write_text('dummy data')
        return str(file_path)

    monkeypatch.setattr(utils.pooch, 'retrieve', fake_retrieve)

    result = utils.download_data(id=12, destination=str(tmp_path), overwrite=True)
    assert Path(result).exists()
    assert calls['kwargs']['url'] == utils._build_data_url('data.xye')
