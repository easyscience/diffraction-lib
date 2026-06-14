# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Serialize and validate Edifa project sections."""

from __future__ import annotations

from easydiffraction.io.cif.parse import read_cif_str

_SCHEMA_NAME_TAG = '_edifa.schema_name'
_SCHEMA_VERSION_TAG = '_edifa.schema_version'
_SCHEMA_NAME = 'EasyDiffraction'
_SCHEMA_VERSION = '1'

_LINE_SEGMENT_BACKGROUND_TAGS = (
    '_background.position',
    '_background.intensity',
    '_pd_background.line_segment_X',
    '_pd_background_line_segment_X',
    '_pd_background.line_segment_intensity',
    '_pd_background_line_segment_intensity',
)
_CHEBYSHEV_BACKGROUND_TAGS = (
    '_background.order',
    '_background.coef',
    '_pd_background.Chebyshev_order',
    '_pd_background.Chebyshev_coef',
)
_BACKGROUND_TYPES = frozenset({'line-segment', 'chebyshev'})


def section_to_edifa(body: str) -> str:
    """
    Add the Edifa schema marker to a serialized section body.

    Parameters
    ----------
    body : str
        STAR/CIF section body, optionally with a ``data_`` block header.

    Returns
    -------
    str
        Edifa text with schema marker lines.
    """
    cleaned_body = body.strip()
    marker = f'{_SCHEMA_NAME_TAG} {_SCHEMA_NAME}\n{_SCHEMA_VERSION_TAG} {_SCHEMA_VERSION}'
    if cleaned_body.startswith('data_'):
        header, _, rest = cleaned_body.partition('\n')
        return f'{header}\n\n{marker}\n\n{rest.strip()}\n'

    return f'{marker}\n\n{cleaned_body}\n'


def edifa_body_from_text(text: str) -> str:
    """
    Validate Edifa text and return its section body.

    An invalid schema marker or inconsistent selector/body content
    raises ``ValueError`` via the validation helpers.

    Parameters
    ----------
    text : str
        Edifa section text containing schema marker lines.

    Returns
    -------
    str
        Section body with schema marker lines removed.
    """
    _validate_schema_marker(_marker_block_from_text(text))
    body = _strip_schema_marker_lines(text).strip()
    if body:
        _validate_selector_body_consistency(_block_from_body(body))
    return f'{body}\n' if body else ''


def _marker_block_from_text(text: str) -> object:
    """
    Parse Edifa schema marker lines as one anonymous STAR block.
    """
    import gemmi  # noqa: PLC0415

    marker_text = '\n'.join(line for line in text.splitlines() if _is_schema_marker_line(line))
    return gemmi.cif.read_string(f'data_edifa\n\n{marker_text}').sole_block()


def _block_from_body(body: str) -> object:
    """Parse a stripped Edifa section body."""
    import gemmi  # noqa: PLC0415

    if body.lstrip().startswith('data_'):
        return gemmi.cif.read_string(body).sole_block()
    return gemmi.cif.read_string(f'data_edifa\n\n{body}').sole_block()


def _validate_schema_marker(block: object) -> None:
    """Validate the required Edifa schema marker."""
    schema_name = read_cif_str(block, _SCHEMA_NAME_TAG)
    if schema_name is None:
        msg = (
            f'Edifa schema name marker {_SCHEMA_NAME_TAG} is required. '
            'Saved project sections must be Edifa files with schema markers.'
        )
        raise ValueError(msg)

    if schema_name != _SCHEMA_NAME:
        msg = (
            'This file is not an EasyDiffraction Edifa project section: '
            f"{_SCHEMA_NAME_TAG} must be '{_SCHEMA_NAME}', got {schema_name!r}."
        )
        raise ValueError(msg)

    schema_version = read_cif_str(block, _SCHEMA_VERSION_TAG)
    if schema_version is None:
        msg = (
            f'Edifa schema version marker {_SCHEMA_VERSION_TAG} is required. '
            'Saved project sections must be Edifa files with schema markers.'
        )
        raise ValueError(msg)

    try:
        major_version = int(schema_version.split('.', maxsplit=1)[0])
    except ValueError as exc:
        msg = f'Edifa schema version must start with an integer, got {schema_version!r}.'
        raise ValueError(msg) from exc

    if major_version != 1:
        msg = (
            f'Unsupported Edifa schema version {schema_version!r}. '
            'Open this project with a compatible EasyDiffraction version '
            'and re-save it as Edifa schema_version 1.'
        )
        raise ValueError(msg)


def _validate_selector_body_consistency(block: object) -> None:
    """Validate selector fields against implementation-specific body."""
    _validate_background_selector_body(block)


def _validate_background_selector_body(block: object) -> None:
    """Validate background type against background row fields."""
    background_type = read_cif_str(block, '_background.type')
    has_line_segment_fields = _has_any_tag(block, _LINE_SEGMENT_BACKGROUND_TAGS)
    has_chebyshev_fields = _has_any_tag(block, _CHEBYSHEV_BACKGROUND_TAGS)

    if background_type is None:
        if has_line_segment_fields or has_chebyshev_fields:
            msg = 'Background fields require an explicit _background.type selector.'
            raise ValueError(msg)
        return

    if background_type not in _BACKGROUND_TYPES:
        msg = f'Unknown _background.type selector: {background_type!r}.'
        raise ValueError(msg)

    if background_type == 'line-segment' and has_chebyshev_fields:
        msg = 'line-segment background cannot contain Chebyshev fields.'
        raise ValueError(msg)

    if background_type == 'chebyshev' and has_line_segment_fields:
        msg = 'chebyshev background cannot contain line-segment fields.'
        raise ValueError(msg)


def _has_any_tag(block: object, tags: tuple[str, ...]) -> bool:
    """Return whether any tag is present as a scalar or loop column."""
    return any(_has_tag(block, tag) for tag in tags)


def _has_tag(block: object, tag: str) -> bool:
    """Return whether a scalar or loop tag is present in the block."""
    if block.find_value(tag) is not None:
        return True
    loop_ref = block.find_loop(tag)
    if loop_ref is None:
        return False
    loop = loop_ref.get_loop() if hasattr(loop_ref, 'get_loop') else loop_ref
    return loop is not None


def _strip_schema_marker_lines(text: str) -> str:
    """Remove schema marker lines from Edifa text."""
    lines = [line for line in text.splitlines() if not _is_schema_marker_line(line)]
    return '\n'.join(lines)


def _is_schema_marker_line(line: str) -> bool:
    """Return whether a line contains one schema marker item."""
    stripped = line.lstrip()
    for tag in (_SCHEMA_NAME_TAG, _SCHEMA_VERSION_TAG):
        if stripped == tag or stripped.startswith((f'{tag} ', f'{tag}\t')):
            return True
    return False
