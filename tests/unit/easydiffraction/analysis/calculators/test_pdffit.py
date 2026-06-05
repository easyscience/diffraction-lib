# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import collections

import numpy as np


def test_module_import():
    import easydiffraction.analysis.calculators.pdffit as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.pdffit'


def test_pdffit_engine_flag_and_hkl_message(monkeypatch):
    from easydiffraction.analysis.calculators import pdffit as pdffit_mod
    from easydiffraction.analysis.calculators.pdffit import PdffitCalculator

    calc = PdffitCalculator()
    assert isinstance(calc.engine_imported, bool)

    messages: list[str] = []

    def fake_debug(*parts):
        messages.append(' '.join(str(p) for p in parts))

    monkeypatch.setattr(pdffit_mod.log, 'debug', fake_debug)

    # calculate_structure_factors logs a not-applicable note and returns [] by contract
    out = calc.calculate_structure_factors(structures=None, experiments=None)
    assert out == []
    assert any('HKLs (not applicable)' in m for m in messages)


# -- Stub classes for test_pdffit_cif_v2_to_v1_regex_behavior ----------


class _DummyParam:
    def __init__(self, v):
        self.value = v


class _DummyPeak:
    def __init__(self):
        self.sharp_delta_1 = _DummyParam(0.0)
        self.sharp_delta_2 = _DummyParam(0.0)
        self.damp_particle_diameter = _DummyParam(0.0)
        self.cutoff_q = _DummyParam(1.0)
        self.damp_q = _DummyParam(0.0)
        self.broad_q = _DummyParam(0.0)


class _DummyLinkedPhases(collections.UserDict):
    def __getitem__(self, k):
        return type('LP', (), {'scale': _DummyParam(1.0)})()


class _DummyExperiment:
    def __init__(self):
        self.name = 'E'
        self.peak = _DummyPeak()
        self.data = type('D', (), {'x': np.linspace(0.0, 1.0, 5)})()
        self.type = type('T', (), {'radiation_probe': type('P', (), {'value': 'neutron'})()})()
        self.linked_phases = _DummyLinkedPhases()


class _DummyStructure:
    name = 'PhaseA'

    @property
    def as_cif(self):
        return '_atom.site.label A1\n_cell.length_a 1.0'


class _FakePdf:
    def add_structure(self, s):
        pass

    def setvar(self, *a, **k):
        pass

    def read_data_lists(self, *a, **k):
        pass

    def calc(self):
        pass

    def getpdf_fit(self):
        return [0.0, 0.0, 0.0, 0.0, 0.0]


class _FakeParser:
    def parse(self, text):
        assert '_atom_site_label' in text or '_atom.site.label' not in text
        return object()


# ----------------------------------------------------------------------


def test_pdffit_cif_v2_to_v1_regex_behavior(monkeypatch):
    # Exercise the regex conversion path indirectly by providing minimal objects
    # Monkeypatch PdfFit and parser to avoid real engine usage
    import easydiffraction.analysis.calculators.pdffit as mod
    from easydiffraction.analysis.calculators.pdffit import PdffitCalculator

    monkeypatch.setattr(mod, 'PdfFit', _FakePdf)
    monkeypatch.setattr(mod, 'pdffit_cif_parser', _FakeParser)
    monkeypatch.setattr(mod, 'redirect_stdout', lambda *a, **k: None)
    monkeypatch.setattr(mod, '_pdffit_devnull', None, raising=False)

    calc = PdffitCalculator()
    pattern = calc.calculate_pattern(
        _DummyStructure(), _DummyExperiment(), called_by_minimizer=False
    )
    assert isinstance(pattern, np.ndarray)
    assert pattern.shape[0] == 5
