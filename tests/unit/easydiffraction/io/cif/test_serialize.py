# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_module_import():
    import easydiffraction.io.cif.serialize as MUT

    expected_module_name = 'easydiffraction.io.cif.serialize'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_format_value_quotes_whitespace_strings():
    import easydiffraction.io.cif.serialize as MUT

    assert MUT.format_value('a b') == '"a b"'
    assert MUT.format_value('ab') == 'ab'


def test_param_to_cif_minimal():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.io.cif.handler import CifHandler

    class P:
        def __init__(self):
            self._cif_handler = CifHandler(names=['_x.y'])
            self.value = 3

    p = P()
    assert MUT.param_to_cif(p) == '_x.y 3'


def test_format_param_value_with_uncertainty_uses_two_sig_digits():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_x.p']),
    )
    p.value = 11.98509310
    p.free = True
    p.uncertainty = 0.03069505

    assert MUT.format_param_value(p) == '11.985(31)'


def test_format_param_value_with_large_uncertainty_is_readable():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_x.p']),
    )
    p.value = 882.16515040
    p.free = True
    p.uncertainty = 58.10490730

    assert MUT.format_param_value(p) == '882(58)'


def test_param_from_cif_empty_brackets_marks_free_without_uncertainty():
    import warnings

    import gemmi

    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='2theta_offset',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_instr.2theta_offset']),
    )
    doc = gemmi.cif.read_string('data_test\n_instr.2theta_offset 0.5()\n')

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        p.from_cif(doc.sole_block())

    assert p.value == 0.5
    assert p.free is True
    assert p.uncertainty is None


def test_param_from_cif_missing_tag_keeps_sentinel_default_without_validating():
    # Regression: a parameter whose default is a sentinel outside its own
    # validator (e.g. the NaN used by data_range axis bounds, validated
    # to [0, 180]) must load cleanly when its CIF tag is absent. The
    # default is authoritative and is applied without re-validation, just
    # as construction does — otherwise loading an experiment CIF with
    # measured data (and no data_range tags) raised.
    import math

    import gemmi

    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import RangeValidator
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='two_theta_min',
        value_spec=AttributeSpec(
            default=float('nan'),
            validator=RangeValidator(ge=0, le=180),
        ),
        cif_handler=CifHandler(names=['_data_range.2theta_min']),
    )
    # Block without the tag: the absent value falls back to the default.
    doc = gemmi.cif.read_string('data_test\n_instr.2theta_offset 0.5\n')

    p.from_cif(doc.sole_block())

    assert math.isnan(p.value)


def test_category_collection_to_cif_empty_and_one_row():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.io.cif.handler import CifHandler

    class Item(CategoryItem):
        def __init__(self, name, value):
            super().__init__()
            self._identity.category_entry_name = name
            self._p = type('P', (), {})()
            self._p._cif_handler = CifHandler(names=['_x'])
            self._p.value = value

        @property
        def parameters(self):
            return [self._p]

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    coll = CategoryCollection(item_type=Item)
    assert MUT.category_collection_to_cif(coll) == ''
    i = Item('n1', 5)
    coll['n1'] = i
    out = MUT.category_collection_to_cif(coll)
    assert 'loop_' in out
    assert '_x' in out
    assert '5' in out


def test_project_to_cif_assembles_present_sections():
    import easydiffraction.io.cif.serialize as MUT

    class Obj:
        def __init__(self, text):
            self._text = text

        @property
        def as_cif(self):
            return self._text

    class Project:
        def __init__(self):
            self.info = Obj('I')
            self.structures = None
            self.experiments = Obj('E')
            self.analysis = None
            self.summary = None

    p = Project()
    out = MUT.project_to_cif(p)
    assert out == 'I\n\nE'


def test_analysis_from_cif_restores_fit_parameters_without_fit_result():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.analysis.analysis import Analysis

    class Project:
        structures = type('Structures', (), {'parameters': []})()
        experiments = type('Experiments', (), {'parameters': [], 'names': []})()
        _varname = 'proj'

    analysis = Analysis(project=Project())
    cif_text = """
_fitting_mode.type single
_minimizer.type 'lmfit (leastsq)'
loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.start_value
_fit_parameter.start_uncertainty
scale 0.0 2.0 1.0 0.1
"""

    MUT.analysis_from_cif(analysis, cif_text)

    assert analysis._has_persisted_fit_state() is False
    assert len(analysis.fit_parameters) == 1
    assert analysis.fit_parameters['scale'].start_value.value == 1.0


def test_atom_site_cif_emits_one_adp_family_per_row():
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='mixed')
    structure.atom_sites.create(label='B1', type_symbol='Si', adp_type='Biso', adp_iso=0.4)
    structure.atom_sites.create(label='U1', type_symbol='O', adp_type='Uiso', adp_iso=0.01)

    b_loop, u_loop = structure.atom_sites.as_cif.split('\n\n')

    assert '_atom_site.B_iso_or_equiv' in b_loop
    assert '_atom_site.U_iso_or_equiv' not in b_loop
    assert 'B1' in b_loop
    assert 'U1' not in b_loop
    assert '_atom_site.U_iso_or_equiv' in u_loop
    assert '_atom_site.B_iso_or_equiv' not in u_loop
    assert 'U1' in u_loop
    assert 'B1' not in u_loop


def test_atom_site_aniso_cif_emits_one_adp_family_per_row():
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='mixed')
    structure.atom_sites.create(label='B1', type_symbol='Si', adp_iso=0.4)
    structure.atom_sites.create(label='U1', type_symbol='O', adp_iso=0.01)
    structure.atom_sites['B1'].adp_type = 'Bani'
    structure.atom_sites['U1'].adp_type = 'Uani'

    b_loop, u_loop = structure.atom_site_aniso.as_cif.split('\n\n')

    assert '_atom_site_aniso.B_11' in b_loop
    assert '_atom_site_aniso.U_11' not in b_loop
    assert 'B1' in b_loop
    assert 'U1' not in b_loop
    assert '_atom_site_aniso.U_11' in u_loop
    assert '_atom_site_aniso.B_11' not in u_loop
    assert 'U1' in u_loop
    assert 'B1' not in u_loop


def _make_beta_structure():
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='beta')
    structure.space_group.name_h_m = 'P 1'
    structure.cell.length_a = 5.0
    structure.cell.length_b = 6.0
    structure.cell.length_c = 8.0
    structure.atom_sites.create(label='Fe', type_symbol='Fe', adp_iso=0.0)
    structure.atom_sites['Fe'].adp_type = 'beta'
    structure._sync_atom_site_aniso()
    aniso = structure.atom_site_aniso['Fe']
    aniso.adp_11 = 0.00123
    aniso.adp_22 = 0.00078
    aniso.adp_33 = 0.00091
    aniso.adp_12 = -0.0004
    return structure


def test_atom_site_aniso_cif_emits_beta_family():
    structure = _make_beta_structure()

    cif = structure.atom_site_aniso.as_cif

    assert '_atom_site_aniso.beta_11' in cif
    assert '_atom_site_aniso.beta_23' in cif
    assert '_atom_site_aniso.U_11' not in cif
    assert '_atom_site_aniso.B_11' not in cif


def test_beta_atom_round_trips_through_cif():
    from easydiffraction.datablocks.structure.item.factory import StructureFactory

    structure = _make_beta_structure()
    reloaded = StructureFactory.from_cif_str(structure.as_cif)
    reloaded._update_categories()

    assert reloaded.atom_sites['Fe'].adp_type.value == 'beta'
    aniso = reloaded.atom_site_aniso['Fe']
    assert aniso.adp_11.value == pytest.approx(0.00123)
    assert aniso.adp_22.value == pytest.approx(0.00078)
    assert aniso.adp_12.value == pytest.approx(-0.0004)
