# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the Experiments collection.

These exercise the convenience constructors (``create``,
``add_from_cif_str``, ``add_from_cif_path``, ``add_from_data_path``)
and the ``show_params`` helper. The ``ExperimentFactory`` boundary is
stubbed so no real calculation engine, CIF document, or data file is
touched.
"""

import pytest
from typeguard import TypeCheckError

from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.experiment.item.base import ExperimentBase


class _DummyType:
    """Minimal stand-in for an ExperimentType used by ExperimentBase."""

    def __init__(self):
        self.sample_form = type('E', (), {'value': 'powder'})
        self.beam_mode = type('E', (), {'value': 'constant wavelength'})
        self.scattering_type = type('E', (), {'value': 'bragg'})


class _DummyExp(ExperimentBase):
    """Lightweight experiment that records data-load calls."""

    def __init__(self, name='e1', *, num_points=7):
        super().__init__(name=name, type=_DummyType())
        self._num_points = num_points
        self._loaded_paths = []
        self._show_params_calls = 0

    @property
    def loaded_paths(self):
        return self._loaded_paths

    @property
    def show_params_calls(self):
        return self._show_params_calls

    def _load_ascii_data_to_experiment(self, data_path):
        self._loaded_paths.append(data_path)
        return self._num_points

    def show_params(self):
        self._show_params_calls += 1


class _ParentWithVerbosity:
    """Parent stub exposing ``verbosity.fit.value`` like a Project."""

    def __init__(self, fit_value):
        self.verbosity = type(
            'V',
            (),
            {'fit': type('F', (), {'value': fit_value})()},
        )()


def _patch_factory(monkeypatch, method_name, experiment):
    """Replace an ExperimentFactory classmethod with a recording stub."""
    import easydiffraction.datablocks.experiment.collection as mut

    calls = {}

    def fake(*args, **kwargs):
        calls['args'] = args
        calls['kwargs'] = kwargs
        return experiment

    monkeypatch.setattr(mut.ExperimentFactory, method_name, fake)
    return calls


# ----------------------------------------------------------------------
# create
# ----------------------------------------------------------------------


def test_create_forwards_all_metadata_and_adds(monkeypatch):
    exps = Experiments()
    experiment = _DummyExp('cwl')
    calls = _patch_factory(monkeypatch, 'from_scratch', experiment)

    exps.create(
        name='cwl',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )

    # All metadata is forwarded by keyword to the factory.
    assert calls['kwargs'] == {
        'name': 'cwl',
        'sample_form': 'powder',
        'beam_mode': 'constant wavelength',
        'radiation_probe': 'neutron',
        'scattering_type': 'bragg',
    }
    # The created experiment is added under its name.
    assert 'cwl' in exps
    assert exps['cwl'] is experiment


def test_create_defaults_optional_metadata_to_none(monkeypatch):
    exps = Experiments()
    experiment = _DummyExp('bare')
    calls = _patch_factory(monkeypatch, 'from_scratch', experiment)

    exps.create(name='bare')

    assert calls['kwargs'] == {
        'name': 'bare',
        'sample_form': None,
        'beam_mode': None,
        'radiation_probe': None,
        'scattering_type': None,
    }
    assert exps['bare'] is experiment


def test_create_rejects_non_string_name(monkeypatch):
    exps = Experiments()
    _patch_factory(monkeypatch, 'from_scratch', _DummyExp('x'))

    # @typechecked enforces the keyword signature before the body runs.
    with pytest.raises(TypeCheckError):
        exps.create(name=123)


# ----------------------------------------------------------------------
# add_from_cif_str / add_from_cif_path
# ----------------------------------------------------------------------


def test_add_from_cif_str_uses_factory_and_adds(monkeypatch):
    exps = Experiments()
    experiment = _DummyExp('from_str')
    calls = _patch_factory(monkeypatch, 'from_cif_str', experiment)

    exps.add_from_cif_str('data_block\n_x 1')

    assert calls['args'] == ('data_block\n_x 1',)
    assert exps['from_str'] is experiment


def test_add_from_cif_path_uses_factory_and_adds(monkeypatch):
    exps = Experiments()
    experiment = _DummyExp('from_path')
    calls = _patch_factory(monkeypatch, 'from_cif_path', experiment)

    exps.add_from_cif_path('data/some.cif')

    assert calls['args'] == ('data/some.cif',)
    assert exps['from_path'] is experiment


# ----------------------------------------------------------------------
# add_from_data_path
# ----------------------------------------------------------------------


def test_add_from_data_path_full_verbosity_when_no_parent(monkeypatch, capsys):
    exps = Experiments()
    experiment = _DummyExp('full', num_points=128)
    _patch_factory(monkeypatch, 'from_scratch', experiment)

    # No parent => verbosity falls back to FULL.
    exps._parent = None
    exps.add_from_data_path(name='full', data_path='data/full.dat')

    out = capsys.readouterr().out
    assert 'Data loaded successfully' in out
    assert '128' in out
    assert "'full'" in out
    assert experiment.loaded_paths == ['data/full.dat']
    assert exps['full'] is experiment


def test_add_from_data_path_short_verbosity(monkeypatch, capsys):
    exps = Experiments()
    experiment = _DummyExp('short', num_points=5)
    _patch_factory(monkeypatch, 'from_scratch', experiment)
    exps._parent = _ParentWithVerbosity('short')

    exps.add_from_data_path(name='short', data_path='data/short.dat')

    out = capsys.readouterr().out
    assert 'Data loaded' in out
    assert '5 points' in out
    # The verbose multi-line header is not emitted in SHORT mode.
    assert 'Data loaded successfully' not in out
    assert exps['short'] is experiment


def test_add_from_data_path_silent_verbosity_emits_no_status(monkeypatch, capsys):
    exps = Experiments()
    experiment = _DummyExp('silent', num_points=9)
    _patch_factory(monkeypatch, 'from_scratch', experiment)
    exps._parent = _ParentWithVerbosity('silent')

    exps.add_from_data_path(name='silent', data_path='data/silent.dat')

    out = capsys.readouterr().out
    assert 'Data loaded' not in out
    # Data is still loaded and the experiment is still registered.
    assert experiment.loaded_paths == ['data/silent.dat']
    assert exps['silent'] is experiment


# ----------------------------------------------------------------------
# show_params
# ----------------------------------------------------------------------


def test_show_params_delegates_to_each_experiment():
    exps = Experiments()
    a = _DummyExp('a')
    b = _DummyExp('b')
    exps.add(a)
    exps.add(b)

    exps.show_params()

    assert a.show_params_calls == 1
    assert b.show_params_calls == 1


def test_show_params_on_empty_collection_is_noop():
    exps = Experiments()

    # No experiments => loop body never runs, nothing raised.
    exps.show_params()
