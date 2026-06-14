# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Edifa schema-marker serialization and validation."""

from __future__ import annotations

import pytest

from easydiffraction.io import edifa
from easydiffraction.io.edifa.serialize import edifa_body_from_text
from easydiffraction.io.edifa.serialize import section_to_edifa

_MARKER = '_edifa.schema_name EasyDiffraction\n_edifa.schema_version 1'


# ----------------------------------------------------------------------
# Package re-exports
# ----------------------------------------------------------------------


def test_package_reexports_public_helpers():
    assert edifa.section_to_edifa is section_to_edifa
    assert edifa.edifa_body_from_text is edifa_body_from_text


# ----------------------------------------------------------------------
# section_to_edifa
# ----------------------------------------------------------------------


def test_section_to_edifa_prepends_marker_for_headerless_body():
    out = section_to_edifa('_metadata.name demo')

    assert out.startswith(_MARKER)
    assert '_metadata.name demo' in out
    assert out.endswith('\n')


def test_section_to_edifa_keeps_data_header_first():
    out = section_to_edifa('data_demo\n_metadata.name demo')

    lines = [line for line in out.splitlines() if line.strip()]
    assert lines[0] == 'data_demo'
    assert '_edifa.schema_name EasyDiffraction' in out
    assert '_edifa.schema_version 1' in out
    # Marker sits between the data header and the body content.
    assert out.index('_edifa.schema_name') < out.index('_metadata.name demo')


# ----------------------------------------------------------------------
# section_to_edifa / edifa_body_from_text round trip
# ----------------------------------------------------------------------


def test_round_trip_recovers_body_without_marker():
    body = 'data_demo\n_metadata.name demo'
    text = section_to_edifa(body)

    recovered = edifa_body_from_text(text)

    assert '_edifa.schema_name' not in recovered
    assert '_edifa.schema_version' not in recovered
    assert '_metadata.name demo' in recovered


def test_empty_body_round_trips_to_empty_string():
    text = section_to_edifa('')

    assert edifa_body_from_text(text) == ''


# ----------------------------------------------------------------------
# Schema-marker validation
# ----------------------------------------------------------------------


def test_missing_schema_name_marker_raises():
    text = '_edifa.schema_version 1\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='schema_name'):
        edifa_body_from_text(text)


def test_missing_schema_version_marker_raises():
    text = '_edifa.schema_name EasyDiffraction\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='schema_version'):
        edifa_body_from_text(text)


def test_wrong_schema_name_raises():
    text = '_edifa.schema_name SomethingElse\n_edifa.schema_version 1\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='not an EasyDiffraction Edifa'):
        edifa_body_from_text(text)


def test_non_integer_schema_version_raises():
    text = '_edifa.schema_name EasyDiffraction\n_edifa.schema_version v1\n'

    with pytest.raises(ValueError, match='must start with an integer'):
        edifa_body_from_text(text)


def test_unsupported_major_schema_version_raises():
    text = '_edifa.schema_name EasyDiffraction\n_edifa.schema_version 2\n'

    with pytest.raises(ValueError, match='Unsupported Edifa schema version'):
        edifa_body_from_text(text)


def test_minor_version_suffix_is_accepted():
    text = f'{_MARKER}.3\n\n_metadata.name demo'

    # Major version 1 is supported even with a minor suffix.
    assert '_metadata.name demo' in edifa_body_from_text(text)


# ----------------------------------------------------------------------
# Background selector/body consistency
# ----------------------------------------------------------------------


def _wrap(body: str) -> str:
    return section_to_edifa(f'data_expt\n{body}')


def test_background_fields_without_type_selector_raise():
    body = 'loop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match=r'_background\.type selector'):
        edifa_body_from_text(_wrap(body))


def test_unknown_background_type_raises():
    body = '_background.type bogus'

    with pytest.raises(ValueError, match=r'Unknown _background\.type'):
        edifa_body_from_text(_wrap(body))


def test_line_segment_type_rejects_chebyshev_fields():
    body = '_background.type line-segment\nloop_\n_background.order\n_background.coef\n0 1.0'

    with pytest.raises(ValueError, match='line-segment background cannot contain'):
        edifa_body_from_text(_wrap(body))


def test_chebyshev_type_rejects_line_segment_fields():
    body = '_background.type chebyshev\nloop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match='chebyshev background cannot contain'):
        edifa_body_from_text(_wrap(body))


def test_consistent_line_segment_background_validates():
    body = (
        '_background.type line-segment\nloop_\n_background.position\n_background.intensity\n10 0.5'
    )

    recovered = edifa_body_from_text(_wrap(body))

    assert '_background.position' in recovered
    assert '_background.type line-segment' in recovered
