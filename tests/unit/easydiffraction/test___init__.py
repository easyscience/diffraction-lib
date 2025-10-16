# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

# Focused tests for package __init__: lazy attributes and error path
import importlib

import pytest


def test_lazy_attributes_resolve_and_are_accessible():
    import easydiffraction as ed

    # Access a few lazy attributes; just ensure they exist and are callable/class-like
    assert hasattr(ed, 'Project')
    assert hasattr(ed, 'ExperimentFactory')
    assert hasattr(ed, 'SampleModelFactory')

    # Access utility functions from utils via lazy getattr
    assert callable(ed.show_version)
    assert callable(ed.get_value_from_xye_header)

    # Import once to exercise __getattr__; subsequent access should be cached by Python
    _ = ed.Project
    _ = ed.ExperimentFactory


def test___getattr__unknown_raises_attribute_error():
    ed = importlib.import_module('easydiffraction')
    with pytest.raises(AttributeError):
        ed.DefinitelyUnknownAttribute


def test_lazy_functions_execute_with_monkeypatch(monkeypatch, capsys, tmp_path):
    import easydiffraction as ed
    import easydiffraction.utils.utils as utils

    # 1) list_tutorials uses utils.fetch_tutorial_list → monkeypatch there
    monkeypatch.setattr(utils, 'fetch_tutorial_list', lambda: ['a.ipynb', 'b.ipynb'])
    ed.list_tutorials()  # calls into utils.list_tutorials
    out = capsys.readouterr().out
    assert 'Tutorials available for easydiffraction' in out

    # 2) download_from_repository should call pooch.retrieve; avoid network
    import easydiffraction.utils.utils as utils

    calls = {}
    monkeypatch.setattr(utils.pooch, 'retrieve', lambda **kw: calls.setdefault('ok', True))
    utils.download_from_repository(
        'dummy.txt', branch='main', destination=str(tmp_path), overwrite=True
    )
    assert calls.get('ok') is True
