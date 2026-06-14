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
        self.experiment_type = type(
            'T', (), {'radiation_probe': type('P', (), {'value': 'neutron'})()}
        )()
        self.linked_structures = _DummyLinkedPhases()


class _DummyStructure:
    name = 'PhaseA'
    atom_sites = ()

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


def test_structure_cif_for_pdffit_uses_legacy_iucr_tags():
    """Edifa structure tags map to the legacy spellings diffpy reads."""
    from easydiffraction.analysis.calculators.pdffit import _structure_cif_for_pdffit
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='ni')
    structure.space_group.name_h_m = 'F m -3 m'
    structure.cell.length_a = 3.52
    structure.atom_sites.create(
        id='Ni',
        type_symbol='Ni',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        occupancy=1.0,
        adp_iso=0.42,
    )

    cif = _structure_cif_for_pdffit(structure)

    assert '_atom_site.label' in cif
    assert '_atom_site.id' not in cif
    assert '_space_group.name_H-M_alt' in cif
    assert '_space_group.name_h_m' not in cif
    # ADPs are normalized to the U convention for diffpy.
    assert '_atom_site.U_iso_or_equiv' in cif
    assert '_atom_site.B_iso_or_equiv' not in cif
    assert '_atom_site.adp_iso' not in cif


def test_structure_cif_for_pdffit_normalizes_mixed_b_u_iso_adp():
    import math

    from easydiffraction.analysis.calculators.pdffit import _structure_cif_for_pdffit
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='mixed')
    structure.space_group.name_h_m = 'P 1'
    structure.cell.length_a = 5.0
    structure.atom_sites.create(
        id='B1',
        type_symbol='Si',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        adp_type='Biso',
        adp_iso=0.8,
    )
    structure.atom_sites.create(
        id='U1',
        type_symbol='O',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        adp_type='Uiso',
        adp_iso=0.01,
    )

    cif = _structure_cif_for_pdffit(structure)

    # Both rows use the U tag; the Biso value is converted (B / 8π² ≈
    # 0.0101) while the native Uiso value is left as-is.
    assert '_atom_site.U_iso_or_equiv' in cif
    assert '_atom_site.B_iso_or_equiv' not in cif
    assert math.isclose(0.8 / (8.0 * math.pi**2), 0.010132, abs_tol=1e-5)
    assert '0.0101' in cif
    assert '0.01' in cif
    # The live structure is restored to its original B value afterwards.
    assert structure.atom_sites['B1'].adp_iso.value == 0.8
