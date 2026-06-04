# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import importlib

import pytest

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class SimpleItem(CategoryItem):
    _category_code = 'simple'
    _category_entry_name = 'a'

    def __init__(self):
        super().__init__()
        object.__setattr__(
            self,
            '_a',
            StringDescriptor(
                name='a',
                description='',
                value_spec=AttributeSpec(default='_'),
                cif_handler=CifHandler(names=['_simple.a']),
            ),
        )
        object.__setattr__(
            self,
            '_b',
            StringDescriptor(
                name='b',
                description='',
                value_spec=AttributeSpec(default='_'),
                cif_handler=CifHandler(names=['_simple.b']),
            ),
        )

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._a.value = value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b.value = value


class SimpleCollection(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=SimpleItem)


def test_category_item_uses_declared_identity_metadata():
    it = SimpleItem()

    assert type(it)._category_code == 'simple'
    assert type(it)._category_entry_name == 'a'
    assert it._identity.category_code == 'simple'

    it.a = 'name1'

    assert it._identity.category_entry_name == 'name1'


@pytest.mark.parametrize(
    ('module_name', 'class_name', 'attr_name', 'value', 'category_code'),
    [
        pytest.param(
            'easydiffraction.analysis.categories.aliases.default',
            'Alias',
            'label',
            'alias_1',
            'alias',
            id='alias',
        ),
        pytest.param(
            'easydiffraction.analysis.categories.constraints.default',
            'Constraint',
            'id',
            'constraint_1',
            'constraint',
            id='constraint',
        ),
        pytest.param(
            'easydiffraction.analysis.categories.joint_fit.default',
            'JointFitItem',
            'experiment_id',
            'exp_1',
            'joint_fit',
            id='joint_fit',
        ),
        pytest.param(
            'easydiffraction.analysis.categories.sequential_fit_extract.default',
            'SequentialFitExtractItem',
            'id',
            'rule_1',
            'sequential_fit_extract',
            id='sequential_fit_extract',
        ),
        pytest.param(
            'easydiffraction.datablocks.structure.categories.atom_sites.default',
            'AtomSite',
            'label',
            'Fe1',
            'atom_site',
            id='atom_site',
        ),
        pytest.param(
            'easydiffraction.datablocks.structure.categories.atom_site_aniso.default',
            'AtomSiteAniso',
            'label',
            'Fe1',
            'atom_site_aniso',
            id='atom_site_aniso',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.linked_phases.default',
            'LinkedPhase',
            'id',
            'phase_1',
            'linked_phases',
            id='linked_phases',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.background.line_segment',
            'LineSegment',
            'id',
            'bg_1',
            'background',
            id='background_line_segment',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.background.chebyshev',
            'PolynomialTerm',
            'id',
            'poly_1',
            'background',
            id='background_chebyshev',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.excluded_regions.default',
            'ExcludedRegion',
            'id',
            'mask_1',
            'excluded_regions',
            id='excluded_region',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.refln.bragg_sc',
            'Refln',
            'id',
            'refl_1',
            'refln',
            id='refln',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.data.bragg_pd',
            'PdCwlDataPoint',
            'point_id',
            '1',
            'pd_data',
            id='pd_cwl_data',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.data.bragg_pd',
            'PdTofDataPoint',
            'point_id',
            '2',
            'pd_data',
            id='pd_tof_data',
        ),
        pytest.param(
            'easydiffraction.datablocks.experiment.categories.data.total_pd',
            'TotalDataPoint',
            'point_id',
            '3',
            'total_data',
            id='total_data',
        ),
    ],
)
def test_loop_items_resolve_declared_category_identity(
    module_name,
    class_name,
    attr_name,
    value,
    category_code,
):
    module = importlib.import_module(module_name)
    item_cls = getattr(module, class_name)
    item = item_cls()

    getattr(item, attr_name).value = value

    assert item_cls._category_code == category_code
    assert item_cls._category_entry_name == attr_name
    assert item._identity.category_code == category_code
    assert item._identity.category_entry_name == value


def test_category_item_str_and_properties():
    it = SimpleItem()
    it.a = 'name1'
    s = str(it)
    assert '<' in s
    assert 'a=' in s
    assert 'b=' in s
    assert it.unique_name.endswith('.simple.name1') or it.unique_name == 'simple.name1'
    assert len(it.parameters) == 2


def test_category_collection_str_and_cif_calls():
    c = SimpleCollection()
    c.create(a='n1')
    c.create(a='n2')
    s = str(c)
    assert 'collection' in s
    assert '2 items' in s
    # as_cif delegates to serializer; should be a string (possibly empty)
    assert isinstance(c.as_cif, str)


def test_category_item_help(capsys):
    it = SimpleItem()
    it.a = 'name1'
    it.help()
    out = capsys.readouterr().out
    assert 'Parameters' in out
    assert 'string' in out  # Type column
    assert '✓' in out  # a and b are writable
    assert 'Methods' in out


def test_category_collection_help(capsys):
    c = SimpleCollection()
    c.create(a='n1')
    c.create(a='n2')
    c.help()
    out = capsys.readouterr().out
    assert 'Items (2)' in out
    assert 'n1' in out
    assert 'n2' in out
