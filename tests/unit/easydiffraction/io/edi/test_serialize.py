# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Edi schema-marker serialization and validation."""

from __future__ import annotations

import pytest

from easydiffraction.io import edi
from easydiffraction.io.edi.serialize import edi_body_from_text
from easydiffraction.io.edi.serialize import section_to_edi

_MARKER = '_edi.schema_version 1'


# ----------------------------------------------------------------------
# Package re-exports
# ----------------------------------------------------------------------


def test_package_reexports_public_helpers():
    assert edi.section_to_edi is section_to_edi
    assert edi.edi_body_from_text is edi_body_from_text


# ----------------------------------------------------------------------
# section_to_edi
# ----------------------------------------------------------------------


def test_section_to_edi_prepends_marker_for_headerless_body():
    out = section_to_edi('_metadata.name demo')

    assert out.startswith(_MARKER)
    assert '_metadata.name demo' in out
    assert out.endswith('\n')


def test_section_to_edi_keeps_data_header_first():
    out = section_to_edi('data_demo\n_metadata.name demo')

    lines = [line for line in out.splitlines() if line.strip()]
    assert lines[0] == 'data_demo'
    assert '_edi.schema_version 1' in out
    # Marker sits between the data header and the body content.
    assert out.index('_edi.schema_version') < out.index('_metadata.name demo')


# ----------------------------------------------------------------------
# section_to_edi / edi_body_from_text round trip
# ----------------------------------------------------------------------


def test_round_trip_recovers_body_without_marker():
    body = 'data_demo\n_metadata.name demo'
    text = section_to_edi(body)

    recovered = edi_body_from_text(text)

    assert '_edi.schema_name' not in recovered
    assert '_edi.schema_version' not in recovered
    assert '_metadata.name demo' in recovered


def test_empty_body_round_trips_to_empty_string():
    text = section_to_edi('')

    assert edi_body_from_text(text) == ''


# ----------------------------------------------------------------------
# Schema-marker validation
# ----------------------------------------------------------------------


def test_missing_schema_version_marker_raises():
    text = '_metadata.name demo'

    with pytest.raises(ValueError, match='schema_version'):
        edi_body_from_text(text)


def test_non_integer_schema_version_raises():
    text = '_edi.schema_version v1\n'

    with pytest.raises(ValueError, match='must start with an integer'):
        edi_body_from_text(text)


def test_unsupported_major_schema_version_raises():
    text = '_edi.schema_version 2\n'

    with pytest.raises(ValueError, match='Unsupported Edi schema version'):
        edi_body_from_text(text)


def test_minor_version_suffix_is_accepted():
    text = f'{_MARKER}.3\n\n_metadata.name demo'

    # Major version 1 is supported even with a minor suffix.
    assert '_metadata.name demo' in edi_body_from_text(text)


# ----------------------------------------------------------------------
# Background selector/body consistency
# ----------------------------------------------------------------------


def _wrap(body: str) -> str:
    return section_to_edi(f'data_expt\n{body}')


def test_background_fields_without_type_selector_raise():
    body = 'loop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match=r'_background\.type selector'):
        edi_body_from_text(_wrap(body))


def test_unknown_background_type_raises():
    body = '_background.type bogus'

    with pytest.raises(ValueError, match=r'Unknown _background\.type'):
        edi_body_from_text(_wrap(body))


def test_line_segment_type_rejects_chebyshev_fields():
    body = '_background.type line-segment\nloop_\n_background.order\n_background.coef\n0 1.0'

    with pytest.raises(ValueError, match='line-segment background cannot contain'):
        edi_body_from_text(_wrap(body))


def test_chebyshev_type_rejects_line_segment_fields():
    body = '_background.type chebyshev\nloop_\n_background.position\n_background.intensity\n10 0.5'

    with pytest.raises(ValueError, match='chebyshev background cannot contain'):
        edi_body_from_text(_wrap(body))


def test_consistent_line_segment_background_validates():
    body = (
        '_background.type line-segment\nloop_\n_background.position\n_background.intensity\n10 0.5'
    )

    recovered = edi_body_from_text(_wrap(body))

    assert '_background.position' in recovered
    assert '_background.type line-segment' in recovered
