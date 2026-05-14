# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.core.variable as MUT

    assert MUT.__name__ == 'easydiffraction.core.variable'


def test_string_descriptor_type_override_raises_type_error():
    # Creating a StringDescriptor with a NUMERIC spec should raise via Diagnostics
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.core.variable import StringDescriptor
    from easydiffraction.io.cif.handler import CifHandler

    with pytest.raises(TypeError):
        StringDescriptor(
            name='title',
            value_spec=AttributeSpec(data_type=DataTypes.NUMERIC, default='x'),
            description='Title text',
            cif_handler=CifHandler(names=['_proj.title']),
        )


def test_numeric_descriptor_str_includes_units():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import NumericDescriptor
    from easydiffraction.io.cif.handler import CifHandler

    d = NumericDescriptor(
        name='w',
        value_spec=AttributeSpec(default=1.23),
        units='deg',
        cif_handler=CifHandler(names=['_x.w']),
    )
    s = str(d)
    assert s.startswith('<')
    assert s.endswith('>')
    assert 'deg' in s
    assert 'w' in s


def test_parameter_string_repr_and_as_cif_and_flags():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='a',
        value_spec=AttributeSpec(default=0.0),
        units='A',
        cif_handler=CifHandler(names=['_param.a']),
    )
    p.value = 2.5
    # Update extra attributes
    p.uncertainty = 0.1
    p.free = True

    s = str(p)
    assert '± 0.1' in s
    assert 'A' in s
    assert '(free=True)' in s

    # CIF line: free param with uncertainty uses 2-sig-digit esd brackets
    assert p.as_cif == '_param.a 2.50(10)'

    # CifHandler uid is owner's unique_name (parameter name here)
    assert p._cif_handler.uid == p.unique_name == 'a'


def test_parameter_uncertainty_must_be_non_negative():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='b',
        value_spec=AttributeSpec(default=1.0),
        cif_handler=CifHandler(names=['_param.b']),
    )
    with pytest.raises(TypeError):
        p.uncertainty = -0.5


def test_parameter_fit_bounds_assign_and_read():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='c',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_param.c']),
    )
    p.fit_min = -1.0
    p.fit_max = 10.0
    assert np.isclose(p.fit_min, -1.0)
    assert np.isclose(p.fit_max, 10.0)


def test_parameter_set_fit_bounds_from_uncertainty_sets_bounds_and_returns_none():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='d',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_param.d']),
    )
    p.value = 2.0
    p.uncertainty = 0.25

    result = p.set_fit_bounds_from_uncertainty(multiplier=4)

    assert result is None
    assert np.isclose(p.fit_min, 1.0)
    assert np.isclose(p.fit_max, 3.0)


def test_parameter_set_fit_bounds_from_uncertainty_uses_default_multiplier():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='default_multiplier',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_param.default_multiplier']),
    )
    p.value = 2.0
    p.uncertainty = 0.25

    p.set_fit_bounds_from_uncertainty()

    assert np.isclose(p.fit_min, 1.0)
    assert np.isclose(p.fit_max, 3.0)


def test_parameter_set_fit_bounds_from_uncertainty_clips_to_physical_limits():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.core.validation import RangeValidator
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='bounded',
        value_spec=AttributeSpec(
            data_type=DataTypes.NUMERIC,
            default=1.0,
            validator=RangeValidator(ge=0.5, le=1.5),
        ),
        cif_handler=CifHandler(names=['_param.bounded']),
    )
    p.value = 1.0
    p.uncertainty = 0.3

    p.set_fit_bounds_from_uncertainty(multiplier=4)

    assert np.isclose(p.fit_min, 0.5)
    assert np.isclose(p.fit_max, 1.5)


def test_parameter_set_fit_bounds_from_uncertainty_requires_valid_uncertainty():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='invalid',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_param.invalid']),
    )
    p.value = 2.0
    p.uncertainty = None

    with pytest.raises(
        ValueError,
        match=r'Cannot set fit bounds for invalid: uncertainty is missing or invalid\.',
    ):
        p.set_fit_bounds_from_uncertainty(multiplier=4)


def _make_param() -> object:
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    return Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=['_param.p']),
    )


def test_parameter_symmetry_constrained_default_is_false():
    p = _make_param()
    assert p.symmetry_constrained is False


def test_parameter_set_symmetry_constrained_forces_free_false():
    p = _make_param()
    p.free = True
    assert p.free is True
    p._set_symmetry_constrained(value=True)
    assert p.symmetry_constrained is True
    assert p.free is False


def test_parameter_free_true_ignored_when_symmetry_constrained(monkeypatch):
    from easydiffraction.utils.logging import Logger

    p = _make_param()
    p._set_symmetry_constrained(value=True)
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    p.free = True
    assert p.free is False
    assert p.symmetry_constrained is True
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


def test_parameter_free_false_allowed_when_symmetry_constrained():
    p = _make_param()
    p._set_symmetry_constrained(value=True)
    p.free = False  # should not warn or raise
    assert p.free is False


def test_parameter_clearing_symmetry_constrained_allows_free_true():
    p = _make_param()
    p._set_symmetry_constrained(value=True)
    p._set_symmetry_constrained(value=False)
    p.free = True
    assert p.free is True
    assert p.symmetry_constrained is False
