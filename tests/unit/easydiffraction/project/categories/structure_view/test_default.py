# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the project structure_view default category."""

from __future__ import annotations

import pytest

from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.project.categories.structure_view.default import StructureView
from easydiffraction.utils.logging import Logger


@pytest.fixture
def view() -> StructureView:
    """Return a freshly constructed StructureView."""
    return StructureView()


@pytest.fixture
def raise_mode(monkeypatch) -> None:
    """Force the shared Logger into RAISE mode for this test.

    Another test may have leaked WARN mode into the process-global
    Logger, so validation-failure tests pin RAISE explicitly.
    """
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


# ----------------------------------------------------------------------
#  Module / class identity
# ----------------------------------------------------------------------


def test_module_import():
    import easydiffraction.project.categories.structure_view.default as MUT

    expected_module_name = 'easydiffraction.project.categories.structure_view.default'
    assert MUT.__name__ == expected_module_name


def test_type_info_tag():
    assert StructureView.type_info.tag == 'default'


def test_type_info_description():
    assert StructureView.type_info.description == 'Project structure_view category'


def test_category_code_class_attr():
    assert StructureView._category_code == 'structure_view'


def test_instantiation(view):
    assert view is not None


def test_identity_category_code(view):
    assert view._identity.category_code == 'structure_view'


def test_registered_with_factory():
    from easydiffraction.project.categories.structure_view.factory import StructureViewFactory

    # The @StructureViewFactory.register decorator in default.py must
    # register the concrete class under its type_info tag.
    assert StructureView in StructureViewFactory._registry


# ----------------------------------------------------------------------
#  Descriptor types
# ----------------------------------------------------------------------


def test_boolean_descriptor_types(view):
    assert isinstance(view.show_labels, BoolDescriptor)
    assert isinstance(view.show_moments, BoolDescriptor)


def test_range_descriptor_types(view):
    for descriptor in (
        view.range_a_min,
        view.range_a_max,
        view.range_b_min,
        view.range_b_max,
        view.range_c_min,
        view.range_c_max,
    ):
        assert isinstance(descriptor, NumericDescriptor)


# ----------------------------------------------------------------------
#  Defaults
# ----------------------------------------------------------------------


def test_default_show_labels(view):
    assert view.show_labels.value is False


def test_default_show_moments(view):
    assert view.show_moments.value is True


def test_default_range_minimums(view):
    assert view.range_a_min.value == 0.0
    assert view.range_b_min.value == 0.0
    assert view.range_c_min.value == 0.0


def test_default_range_maximums(view):
    assert view.range_a_max.value == 1.0
    assert view.range_b_max.value == 1.0
    assert view.range_c_max.value == 1.0


# ----------------------------------------------------------------------
#  CIF handler names
# ----------------------------------------------------------------------


def test_boolean_cif_handler_names(view):
    assert view.show_labels._cif_handler.names == ['_structure_view.show_labels']
    assert view.show_moments._cif_handler.names == ['_structure_view.show_moments']


def test_range_cif_handler_names(view):
    expected = {
        'range_a_min': ['_structure_view.range_a_min'],
        'range_a_max': ['_structure_view.range_a_max'],
        'range_b_min': ['_structure_view.range_b_min'],
        'range_b_max': ['_structure_view.range_b_max'],
        'range_c_min': ['_structure_view.range_c_min'],
        'range_c_max': ['_structure_view.range_c_max'],
    }
    for attr, names in expected.items():
        assert getattr(view, attr)._cif_handler.names == names


def test_descriptor_names_match_attribute(view):
    assert view.show_labels.name == 'show_labels'
    assert view.show_moments.name == 'show_moments'
    assert view.range_a_min.name == 'range_a_min'
    assert view.range_c_max.name == 'range_c_max'


# ----------------------------------------------------------------------
#  Boolean setters
# ----------------------------------------------------------------------


def test_show_labels_setter(view):
    view.show_labels = True
    assert view.show_labels.value is True


def test_show_moments_setter(view):
    view.show_moments = False
    assert view.show_moments.value is False


def test_show_labels_setter_rejects_non_bool(view, raise_mode):
    with pytest.raises(TypeError):
        view.show_labels = 'nope'


def test_show_moments_setter_rejects_non_bool(view, raise_mode):
    with pytest.raises(TypeError):
        view.show_moments = 'yes'


def test_show_labels_setter_keeps_current_in_warn_mode(view, monkeypatch):
    # In WARN mode a bad-type assignment logs and keeps the current
    # value rather than raising.
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    view.show_labels = 'nope'
    assert view.show_labels.value is False


# ----------------------------------------------------------------------
#  Range setters — valid values
# ----------------------------------------------------------------------


def test_range_a_setters_valid(view):
    view.range_a_min = 0.25
    view.range_a_max = 0.75
    assert view.range_a_min.value == 0.25
    assert view.range_a_max.value == 0.75


def test_range_b_setters_valid(view):
    view.range_b_min = 0.1
    view.range_b_max = 0.9
    assert view.range_b_min.value == 0.1
    assert view.range_b_max.value == 0.9


def test_range_c_setters_valid(view):
    view.range_c_min = 0.2
    view.range_c_max = 0.8
    assert view.range_c_min.value == 0.2
    assert view.range_c_max.value == 0.8


# ----------------------------------------------------------------------
#  Range setters — ordering guard (min < max, strict)
# ----------------------------------------------------------------------


def test_range_min_above_max_is_ignored(view, raise_mode):
    # Default window is (0.0, 1.0); a min of 0.9 still satisfies
    # min < max, so set max low first to create the violation.
    view.range_a_max = 0.3
    # 0.5 is not < 0.3, so the assignment must be rejected and the
    # ordering guard must NOT raise (it only warns).
    view.range_a_min = 0.5
    assert view.range_a_min.value == 0.0


def test_range_max_below_min_is_ignored(view, raise_mode):
    view.range_a_min = 0.6
    # 0.3 is not > 0.6, so the assignment is rejected; value unchanged.
    view.range_a_max = 0.3
    assert view.range_a_max.value == 1.0


def test_range_equal_bounds_are_ignored(view, raise_mode):
    # Strict inequality: min == max must be rejected.
    view.range_a_min = 0.4
    view.range_a_max = 0.4
    assert view.range_a_max.value == 1.0


def test_ordering_guard_does_not_raise_even_in_raise_mode(view, raise_mode):
    # The ordering guard logs a warning without exc_type, so it must
    # never raise regardless of the Logger reaction mode.
    view.range_b_max = 0.2
    view.range_b_min = 0.9  # rejected, but no exception
    assert view.range_b_min.value == 0.0


def test_ordering_guard_warns(view, monkeypatch, capsys):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    view.range_c_max = 0.2
    view.range_c_min = 0.9
    out = capsys.readouterr().out
    assert 'range_c_min' in out
    assert 'min < max' in out


# ----------------------------------------------------------------------
#  Range setters — non-numeric input
# ----------------------------------------------------------------------


def test_range_setter_rejects_non_numeric(view, raise_mode):
    # A non-numeric value fails the ``lower < value < upper`` comparison
    # inside the guard, raising a plain TypeError.
    with pytest.raises(TypeError):
        view.range_a_min = 'oops'


def test_range_setter_rejects_non_numeric_in_warn_mode(view, monkeypatch):
    # The comparison TypeError is raised by Python itself, so it
    # surfaces irrespective of the Logger reaction mode.
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    with pytest.raises(TypeError):
        view.range_b_max = 'oops'


# ----------------------------------------------------------------------
#  view_range()
# ----------------------------------------------------------------------


def test_view_range_defaults(view):
    assert view.view_range() == (
        (0.0, 1.0),
        (0.0, 1.0),
        (0.0, 1.0),
    )


def test_view_range_reflects_updates(view):
    view.range_a_min = 0.1
    view.range_a_max = 0.6
    view.range_b_min = 0.2
    view.range_b_max = 0.7
    view.range_c_min = 0.3
    view.range_c_max = 0.8
    assert view.view_range() == (
        (0.1, 0.6),
        (0.2, 0.7),
        (0.3, 0.8),
    )


def test_view_range_is_per_axis_min_max(view):
    view.range_b_min = 0.25
    view.range_b_max = 0.75
    axis_a, axis_b, axis_c = view.view_range()
    assert axis_a == (0.0, 1.0)
    assert axis_b == (0.25, 0.75)
    assert axis_c == (0.0, 1.0)


# ----------------------------------------------------------------------
#  as_cif
# ----------------------------------------------------------------------


def test_as_cif_returns_str(view):
    assert isinstance(view.as_cif, str)


def test_as_cif_contains_all_handlers(view):
    cif = view.as_cif
    for name in (
        '_structure_view.show_labels',
        '_structure_view.show_moments',
        '_structure_view.range_a_min',
        '_structure_view.range_a_max',
        '_structure_view.range_b_min',
        '_structure_view.range_b_max',
        '_structure_view.range_c_min',
        '_structure_view.range_c_max',
    ):
        assert name in cif


def test_as_cif_reflects_boolean_values(view):
    view.show_labels = True
    view.show_moments = False
    cif = view.as_cif
    assert '_structure_view.show_labels true' in cif
    assert '_structure_view.show_moments false' in cif


# ----------------------------------------------------------------------
#  parameters collection
# ----------------------------------------------------------------------


def test_parameters_lists_all_descriptors(view):
    names = {param.name for param in view.parameters}
    assert names == {
        'show_labels',
        'show_moments',
        'range_a_min',
        'range_a_max',
        'range_b_min',
        'range_b_max',
        'range_c_min',
        'range_c_max',
    }
