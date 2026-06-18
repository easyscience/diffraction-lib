# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Input-domain (property-based) tests for the validation framework.

These target the runtime validators directly — the single boundary
through which user input reaches the model — covering each input domain
the way one would test ``sqrt`` (negative / zero / positive, int / float,
and wrong types). Invalid input is *rejected by fallback*: the validator
logs and returns the ``default`` (or ``current``) value rather than
raising, so the assertions compare the returned value. The logger is kept
in ``WARN`` mode so that fallback path is exercised (a sibling test may
have left it in ``RAISE`` mode).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import log

pytestmark = pytest.mark.usefixtures('_restore_logger_reaction')


@pytest.fixture
def _restore_logger_reaction():
    """Restore the global logger reaction so WARN does not leak out."""
    saved_reaction = Logger._reaction
    saved_mode = Logger._mode
    yield
    Logger._reaction = saved_reaction
    Logger._mode = saved_mode


def _warn() -> None:
    """Keep the logger non-raising so validators take the fallback path."""
    log.configure(reaction=log.Reaction.WARN)


# ---------------------------------------------------------------------------
# TypeValidator (NUMERIC) — the sqrt-style domain sweep
# ---------------------------------------------------------------------------

NUMERIC_DEFAULT = -1.0


def _numeric_spec() -> AttributeSpec:
    return AttributeSpec(data_type=DataTypes.NUMERIC, default=NUMERIC_DEFAULT)


@given(value=st.integers())
def test_numeric_accepts_any_integer(value):
    _warn()
    assert _numeric_spec().validated(value, name='p') == value


@given(value=st.floats(allow_nan=False, allow_infinity=False))
def test_numeric_accepts_any_finite_float(value):
    _warn()
    assert _numeric_spec().validated(value, name='p') == value


@given(value=st.text())
def test_numeric_rejects_text_with_fallback(value):
    _warn()
    result = _numeric_spec().validated(value, name='p')
    assert result == NUMERIC_DEFAULT
    assert not isinstance(result, str)


@pytest.mark.parametrize(
    'value',
    [0, -1, 1, 0.0, -2.5, math.pi, np.int64(5), np.float64(2.0)],
)
def test_numeric_accepts_boundary_table(value):
    _warn()
    assert _numeric_spec().validated(value, name='p') == value


@pytest.mark.parametrize('value', ['x', '', [1], {}, (1,)])
def test_numeric_rejects_non_numeric_table(value):
    _warn()
    assert _numeric_spec().validated(value, name='p') == NUMERIC_DEFAULT


# ---------------------------------------------------------------------------
# RangeValidator — occupancy in [0, 1]; cell length > 0
# ---------------------------------------------------------------------------

OCC_DEFAULT = 0.5


def _occupancy_spec() -> AttributeSpec:
    return AttributeSpec(
        data_type=DataTypes.NUMERIC,
        default=OCC_DEFAULT,
        validator=RangeValidator(ge=0.0, le=1.0),
    )


@given(value=st.floats(min_value=0.0, max_value=1.0))
def test_occupancy_accepts_unit_interval(value):
    _warn()
    assert _occupancy_spec().validated(value, name='occ') == value


@given(value=st.floats(allow_nan=False, allow_infinity=False).filter(lambda v: v < 0.0 or v > 1.0))
def test_occupancy_rejects_outside_unit_interval(value):
    _warn()
    assert _occupancy_spec().validated(value, name='occ') == OCC_DEFAULT


@pytest.mark.parametrize('value', [0.0, 1.0, 0.5, 0.999999])
def test_occupancy_boundary_accepts(value):
    _warn()
    assert _occupancy_spec().validated(value, name='occ') == value


@pytest.mark.parametrize('value', [-0.0001, 1.0001, -5.0, 100.0])
def test_occupancy_boundary_rejects(value):
    _warn()
    assert _occupancy_spec().validated(value, name='occ') == OCC_DEFAULT


CELL_DEFAULT = 1.0


def _cell_length_spec() -> AttributeSpec:
    return AttributeSpec(
        data_type=DataTypes.NUMERIC,
        default=CELL_DEFAULT,
        validator=RangeValidator(gt=0.0),
    )


@given(value=st.floats(min_value=1e-6, max_value=1e6))
def test_cell_length_accepts_positive(value):
    _warn()
    assert _cell_length_spec().validated(value, name='a') == value


@pytest.mark.parametrize('value', [0.0, -1.0, -1e-9])
def test_cell_length_rejects_nonpositive(value):
    _warn()
    assert _cell_length_spec().validated(value, name='a') == CELL_DEFAULT


# ---------------------------------------------------------------------------
# MembershipValidator — space-group number in {1, ..., 230}
# ---------------------------------------------------------------------------

SG_DEFAULT = 1
SG_NUMBERS = tuple(range(1, 231))


def _sg_spec() -> AttributeSpec:
    return AttributeSpec(
        data_type=DataTypes.INTEGER,
        default=SG_DEFAULT,
        validator=MembershipValidator(SG_NUMBERS),
    )


@given(value=st.integers(min_value=1, max_value=230))
def test_space_group_accepts_valid_number(value):
    _warn()
    assert _sg_spec().validated(value, name='sg') == value


@given(value=st.integers().filter(lambda v: v < 1 or v > 230))
def test_space_group_rejects_out_of_range(value):
    _warn()
    assert _sg_spec().validated(value, name='sg') == SG_DEFAULT


# ---------------------------------------------------------------------------
# RegexValidator — atom-site label like "La", "O1"
# ---------------------------------------------------------------------------

LABEL_DEFAULT = 'X'


def _label_spec() -> AttributeSpec:
    return AttributeSpec(
        data_type=DataTypes.STRING,
        default=LABEL_DEFAULT,
        validator=RegexValidator(r'^[A-Za-z]{1,2}\d*$'),
    )


@given(value=st.from_regex(r'\A[A-Za-z]{1,2}[0-9]*\Z', fullmatch=True))
def test_label_accepts_matching(value):
    _warn()
    assert _label_spec().validated(value, name='label') == value


@pytest.mark.parametrize('value', ['', '1A', 'Abc', 'La-1', ' O'])
def test_label_rejects_non_matching(value):
    _warn()
    assert _label_spec().validated(value, name='label') == LABEL_DEFAULT
