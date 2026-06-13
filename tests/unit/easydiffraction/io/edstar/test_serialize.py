# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for EdSTAR schema-marker serialization and validation."""

from __future__ import annotations

import pytest

from easydiffraction.io import edstar
from easydiffraction.io.edstar.serialize import edstar_body_from_text
from easydiffraction.io.edstar.serialize import section_to_edstar

_MARKER = '_edstar.schema_name EasyDiffraction\n_edstar.schema_version 1'


# ----------------------------------------------------------------------
# Package re-exports
# ----------------------------------------------------------------------


def test_package_reexports_public_helpers():
    assert edstar.section_to_edstar is section_to_edstar
    assert edstar.edstar_body_from_text is edstar_body_from_text


# ----------------------------------------------------------------------
# section_to_edstar
# ----------------------------------------------------------------------


def test_section_to_edstar_prepends_marker_for_headerless_body():
    out = section_to_edstar('_metadata.name demo')

    assert out.startswith(_MARKER)
    assert '_metadata.name demo' in out
    assert out.endswith('\n')


def test_section_to_edstar_keeps_data_header_first():
    out = section_to_edstar('data_demo\n_metadata.name demo')

    lines = [line for line in out.splitlines() if line.strip()]
    assert lines[0] == 'data_demo'
    assert '_edstar.schema_name EasyDiffraction' in out
    assert '_edstar.schema_version 1' in out
    # Marker sits between the data header and the body content.
    assert out.index('_edstar.schema_name') < out.index('_metadata.name demo')


# ----------------------------------------------------------------------
# section_to_edstar / edstar_body_from_text round trip
# ----------------------------------------------------------------------


def test_round_trip_recovers_body_without_marker():
    body = 'data_demo\n_metadata.name demo'
    text = section_to_edstar(body)

    recovered = edstar_body_from_text(text)

    assert '_edstar.schema_name' not in recovered
    assert '_edstar.schema_version' not in recovered
    assert '_metadata.name demo' in recovered


def test_empty_body_round_trips_to_empty_string():
    text = section_to_edstar('')

    assert edstar_body_from_text(text) == ''


# ----------------------------------------------------------------------
# Schema-marker validation
# ----------------------------------------------------------------------


def test_missing_schema_name_marker_raises():
    text = '_edstar.schema_version 1\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='schema_name'):
        edstar_body_from_text(text)


def test_missing_schema_version_marker_raises():
    text = '_edstar.schema_name EasyDiffraction\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='schema_version'):
        edstar_body_from_text(text)


def test_wrong_schema_name_raises():
    text = '_edstar.schema_name SomethingElse\n_edstar.schema_version 1\n\n_metadata.name demo'

    with pytest.raises(ValueError, match='not an EasyDiffraction EdSTAR'):
        edstar_body_from_text(text)


def test_non_integer_schema_version_raises():
    text = '_edstar.schema_name EasyDiffraction\n_edstar.schema_version v1\n'

    with pytest.raises(ValueError, match='must start with an integer'):
        edstar_body_from_text(text)


def test_unsupported_major_schema_version_raises():
    text = '_edstar.schema_name EasyDiffraction\n_edstar.schema_version 2\n'

    with pytest.raises(ValueError, match='Unsupported EdSTAR schema version'):
        edstar_body_from_text(text)


def test_minor_version_suffix_is_accepted():
    text = f'{_MARKER}.3\n\n_metadata.name demo'

    # Major version 1 is supported even with a minor suffix.
    assert '_metadata.name demo' in edstar_body_from_text(text)


# ----------------------------------------------------------------------
# Background selector/body consistency
# ----------------------------------------------------------------------


def _wrap(body: str) -> str:
    return section_to_edstar(f'data_expt\n{body}')


def test_background_fields_without_type_selector_raise():
    body = 'loop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match=r'_background\.type selector'):
        edstar_body_from_text(_wrap(body))


def test_unknown_background_type_raises():
    body = '_background.type bogus'

    with pytest.raises(ValueError, match=r'Unknown _background\.type'):
        edstar_body_from_text(_wrap(body))


def test_line_segment_type_rejects_chebyshev_fields():
    body = '_background.type line-segment\nloop_\n_background.order\n_background.coef\n0 1.0'

    with pytest.raises(ValueError, match='line-segment background cannot contain'):
        edstar_body_from_text(_wrap(body))


def test_chebyshev_type_rejects_line_segment_fields():
    body = '_background.type chebyshev\nloop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match='chebyshev background cannot contain'):
        edstar_body_from_text(_wrap(body))


def test_consistent_line_segment_background_validates():
    body = (
        '_background.type line-segment\nloop_\n_background.position\n_background.intensity\n10 0.5'
    )

    recovered = edstar_body_from_text(_wrap(body))

    assert '_background.position' in recovered
    assert '_background.type line-segment' in recovered
