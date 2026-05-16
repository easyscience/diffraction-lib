# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.core.validation import DataTypes
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import str_to_ufloat

if TYPE_CHECKING:
    from collections.abc import Sequence

    import gemmi

    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.variable import GenericDescriptorBase

# Maximum CIF description length before using semicolon-delimited block
_CIF_DESCRIPTION_WRAP_LEN = 60

# Minimum string length to check for surrounding quotes
_MIN_QUOTED_LEN = 2

# Number of significant digits kept for CIF uncertainty notation
_CIF_UNCERTAINTY_SIG_DIGITS = 2


def format_value(value: object) -> str:
    """
    Format a single CIF value for output.

    .. note::     The precision must be high enough so that the
    minimizer's     finite-difference Jacobian probes (typically ~1e-8
    relative)     survive the float→string→float round-trip through CIF.
    Trailing zeros after the decimal point are stripped for readability
    (e.g. ``54902.18695000`` → ``54902.18695``, ``0.0`` → ``0.``).
    """
    precision = 8

    # Converting

    # None → CIF unknown marker
    if value is None:
        value = '?'
    # Booleans use CIF true/false tokens
    elif isinstance(value, bool):
        value = 'true' if value else 'false'
    # Convert ints to floats
    elif isinstance(value, int):
        value = float(value)
    # Empty strings → CIF unknown marker
    elif isinstance(value, str) and not value.strip():
        value = '?'
    # Strings with whitespace are quoted
    elif isinstance(value, str) and (' ' in value or '\t' in value):
        value = f'"{value}"'

    # Formatting

    # Format floats with given precision; strip trailing zeros
    if isinstance(value, float):
        return f'{value:.{precision}f}'.rstrip('0')
    # Format strings as-is
    if isinstance(value, str):
        return value
    # Everything else: fallback
    return str(value)


def _strip_optional_quotes(raw: str) -> str:
    """Return an unquoted CIF token when it is wrapped in quotes."""
    is_quoted = len(raw) >= _MIN_QUOTED_LEN and raw[0] == raw[-1] and raw[0] in {"'", '"'}
    return raw[1:-1] if is_quoted else raw


def _parse_bool_cif_value(raw: str) -> bool | str:
    """Parse CIF boolean tokens, returning the raw token if invalid."""
    token = _strip_optional_quotes(raw).lower()
    if token == 'true':
        return True
    if token == 'false':
        return False
    return _strip_optional_quotes(raw)


##################
# Serialize to CIF
##################


def format_param_value(param: object) -> str:
    """
    Format a parameter value for CIF output, encoding the free flag.

    CIF convention for numeric parameters:

    - Fixed or constrained parameter: plain value, e.g. ``3.8909``
    - Free parameter without uncertainty: value with empty brackets,
      e.g. ``3.8909()``
    - Free parameter with uncertainty: value with esd in brackets,
      e.g. ``3.89(20)``

    User-constrained (dependent) parameters are always written without
    brackets, even if their ``free`` flag is ``True``, because they are
    not independently varied by the minimizer.

    Non-numeric parameters and descriptors without a ``free`` attribute
    are formatted with :func:`format_value`.

    Parameters
    ----------
    param : object
        A descriptor or parameter exposing ``.value`` and optionally
        ``.free``, ``.user_constrained``, and ``.uncertainty``.

    Returns
    -------
    str
        Formatted CIF value string.
    """
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    is_free = param.free if isinstance(param, Parameter) else False
    is_user_constrained = param.user_constrained if isinstance(param, Parameter) else False
    value = param.value  # type: ignore[attr-defined]

    if not is_free or is_user_constrained or not isinstance(value, (int, float)):
        return format_value(value)

    precision = 8
    uncertainty = getattr(param, 'uncertainty', None)
    formatted_value = f'{float(value):.{precision}f}'.rstrip('0')

    if uncertainty is not None and uncertainty > 0:
        from uncertainties import ufloat as _ufloat  # noqa: PLC0415

        u = _ufloat(float(value), float(uncertainty))
        return f'{u:.{_CIF_UNCERTAINTY_SIG_DIGITS}uS}'

    return f'{formatted_value}()'


def param_to_cif(param: object) -> str:
    """
    Render a single descriptor/parameter to a CIF line.

    Expects ``param`` to expose ``_cif_handler.names`` and ``value``.
    Free parameters are written with uncertainty brackets (see
    :func:`format_param_value`).
    """
    tags: Sequence[str] = param._cif_handler.names  # type: ignore[attr-defined]
    main_key: str = tags[0]
    return f'{main_key} {format_param_value(param)}'


def category_item_to_cif(item: object) -> str:
    """
    Render a CategoryItem-like object to CIF text.

    Expects ``item.parameters`` iterable of params with
    ``_cif_handler.names`` and ``value``.
    """
    lines: list[str] = [param_to_cif(p) for p in item.parameters]
    return '\n'.join(lines)


def _validate_loop_tags(
    item: object,
    header_tags: list[str],
) -> None:
    """Log an error if any row tag disagrees with *header_tags*."""
    for col, p in enumerate(item.parameters):
        tag = p._cif_handler.names[0]  # type: ignore[attr-defined]
        if tag != header_tags[col]:
            log.error(
                f'CIF tag mismatch in loop column {col}: '
                f"header expects '{header_tags[col]}', "
                f"row has '{tag}'",
                exc_type=ValueError,
            )


def _emit_loop_rows(
    items: list,
    row_fn: object,
    header_tags: list[str],
    max_display: int | None,
) -> list[str]:
    """Build formatted rows, optionally truncated."""
    lines: list[str] = []
    if max_display is not None and len(items) > max_display:
        half = max_display // 2
        for item in items[:half]:
            _validate_loop_tags(item, header_tags)
            lines.append(' '.join(row_fn(item)))
        lines.append('...')
        for item in items[-half:]:
            _validate_loop_tags(item, header_tags)
            lines.append(' '.join(row_fn(item)))
    else:
        for item in items:
            _validate_loop_tags(item, header_tags)
            lines.append(' '.join(row_fn(item)))
    return lines


def category_collection_to_cif(
    collection: object,
    max_display: int | None = None,
) -> str:
    """
    Render a CategoryCollection-like object to CIF text.

    Uses first item to build loop header, then emits rows for each item.

    Parameters
    ----------
    collection : object
        A ``CategoryCollection``-like object.
    max_display : int | None, default=None
        When set to a positive integer, truncate the output to at most
        this many rows (half from the start, half from the end) with an
        ``...`` separator.  ``None`` emits all rows.

    Returns
    -------
    str
        CIF text representing the collection as a loop.
    """
    if not len(collection):
        return ''

    # Allow collections to conditionally suppress CIF output
    skip = getattr(collection, '_skip_cif_serialization', None)
    if skip is not None and skip():
        return ''

    lines: list[str] = []

    # Header — use first item's CIF tag names as the canonical columns
    first_item = next(iter(collection.values()))
    lines.append('loop_')
    header_tags: list[str] = []
    for p in first_item.parameters:
        tags = p._cif_handler.names  # type: ignore[attr-defined]
        header_tags.append(tags[0])
        lines.append(tags[0])

    # Allow collections to customise per-item row formatting
    row_hook = getattr(collection, '_format_cif_row', None)

    def _row(item: object) -> list[str]:
        if row_hook is not None:
            override = row_hook(item)
            if override is not None:
                return override
        return [format_param_value(p) for p in item.parameters]

    items = list(collection.values())
    lines.extend(_emit_loop_rows(items, _row, header_tags, max_display))

    return '\n'.join(lines)


def datablock_item_to_cif(
    datablock: object,
    max_loop_display: int | None = None,
) -> str:
    """
    Render a DatablockItem-like object to CIF text.

    Emits a data_ header and then concatenates category CIF sections.

    Parameters
    ----------
    datablock : object
        A ``DatablockItem``-like object.
    max_loop_display : int | None, default=None
        When set, truncate loop categories to this many rows. ``None``
        emits all rows (used for serialisation).

    Returns
    -------
    str
        CIF text representing the datablock as a loop.
    """
    # Local imports to avoid import-time cycles
    from easydiffraction.core.category import CategoryCollection  # noqa: PLC0415
    from easydiffraction.core.category import CategoryItem  # noqa: PLC0415

    header = f'data_{datablock._identity.datablock_entry_name}'
    parts: list[str] = [header]

    # First categories
    parts.extend(
        cif_text
        for cif_text in (v.as_cif for v in vars(datablock).values() if isinstance(v, CategoryItem))
        if cif_text
    )

    # Then collections
    parts.extend(
        cif_text
        for cif_text in (
            category_collection_to_cif(v, max_display=max_loop_display)
            for v in vars(datablock).values()
            if isinstance(v, CategoryCollection)
        )
        if cif_text
    )

    return '\n\n'.join(parts)


def datablock_collection_to_cif(collection: object) -> str:
    """Render a collection of datablocks by joining their CIF blocks."""
    return '\n\n'.join([block.as_cif for block in collection.values()])


def project_info_to_cif(info: object) -> str:
    """Render ProjectInfo to CIF text (id, title, description)."""
    name = f'{info.name}'

    title = f'{info.title}'
    if ' ' in title:
        title = f"'{title}'"

    if len(info.description) > _CIF_DESCRIPTION_WRAP_LEN:
        description = f'\n;\n{info.description}\n;'
    elif info.description:
        description = f'{info.description}'
        if ' ' in description:
            description = f"'{description}'"
    else:
        description = '?'

    created = f"'{info._created.strftime('%d %b %Y %H:%M:%S')}'"
    last_modified = f"'{info._last_modified.strftime('%d %b %Y %H:%M:%S')}'"

    return (
        f'_project.id               {name}\n'
        f'_project.title            {title}\n'
        f'_project.description      {description}\n'
        f'_project.created          {created}\n'
        f'_project.last_modified    {last_modified}'
    )


def _as_cif_text(section: object) -> str:
    """Return CIF text from either an ``as_cif`` property or method."""
    cif_value = section.as_cif
    return cif_value() if callable(cif_value) else cif_value


def project_config_to_cif(project: object) -> str:
    """Render project-level configuration to ``project.cif`` text."""
    lines: list[str] = [_as_cif_text(project.info)]
    rendering = getattr(project, 'rendering', None)
    if rendering is not None:
        lines.extend(('', _as_cif_text(rendering)))
    return '\n'.join(lines)


def project_to_cif(project: object) -> str:
    """Render a whole project by concatenating sections when present."""
    parts: list[str] = []
    if hasattr(project, 'info'):
        parts.append(project_config_to_cif(project))
    if getattr(project, 'structures', None):
        parts.append(_as_cif_text(project.structures))
    if getattr(project, 'experiments', None):
        parts.append(_as_cif_text(project.experiments))
    if getattr(project, 'analysis', None):
        parts.append(_as_cif_text(project.analysis))
    if getattr(project, 'summary', None):
        parts.append(project.summary.as_cif())
    return '\n\n'.join([p for p in parts if p])


def experiment_to_cif(experiment: object) -> str:
    """Render an experiment: datablock part plus measured data."""
    return datablock_item_to_cif(experiment)


def analysis_to_cif(analysis: object) -> str:
    """Render analysis metadata, aliases, and constraints to CIF."""
    lines: list[str] = []
    lines.extend((
        analysis.fit.as_cif,
        '',
        analysis.aliases.as_cif,
        '',
        analysis.constraints.as_cif,
    ))
    joint_fit_cif = analysis.joint_fit.as_cif
    if joint_fit_cif:
        lines.extend(('', joint_fit_cif))
    return '\n'.join(lines)


def summary_to_cif(_summary: object) -> str:
    """Render a summary CIF block (placeholder for now)."""
    return 'To be added...'


def _wrap_in_data_block(cif_text: str, block_name: str = '_') -> str:
    """
    Wrap bare CIF key-value pairs in a ``data_`` block header.

    Parameters
    ----------
    cif_text : str
        CIF text without a ``data_`` header.
    block_name : str, default='_'
        Name for the CIF data block.

    Returns
    -------
    str
        CIF text with a ``data_<block_name>`` header prepended.
    """
    return f'data_{block_name}\n\n{cif_text}'


def _populate_project_info_from_block(
    info: object,
    block: gemmi.cif.Block,
) -> None:
    """Populate ProjectInfo fields from a parsed CIF block."""
    read_cif_string = _make_cif_string_reader(block)

    name = read_cif_string('_project.id')
    if name is not None:
        info.name = name

    title = read_cif_string('_project.title')
    if title is not None:
        info.title = title

    description = read_cif_string('_project.description')
    if description is not None:
        info.description = description


def project_info_from_cif(info: object, cif_text: str) -> None:
    """
    Populate a ProjectInfo instance from CIF text.

    Reads ``_project.id``, ``_project.title``, and
    ``_project.description`` from the given CIF string and sets them on
    the *info* object.

    Parameters
    ----------
    info : object
        The ``ProjectInfo`` instance to populate.
    cif_text : str
        CIF text content of ``project.cif``.
    """
    import gemmi  # noqa: PLC0415

    doc = gemmi.cif.read_string(_wrap_in_data_block(cif_text, 'project'))
    block = doc.sole_block()

    _populate_project_info_from_block(info, block)


def project_config_from_cif(project: object, cif_text: str) -> None:
    """
    Populate project-level configuration from ``project.cif`` text.
    """
    import gemmi  # noqa: PLC0415

    doc = gemmi.cif.read_string(_wrap_in_data_block(cif_text, 'project'))
    block = doc.sole_block()

    _populate_project_info_from_block(project.info, block)

    rendering = getattr(project, 'rendering', None)
    if rendering is not None:
        rendering.from_cif(block)


def analysis_from_cif(analysis: object, cif_text: str) -> None:
    """
    Populate an Analysis instance from CIF text.

    Reads the fit configuration, aliases, constraints, and joint-fit
    experiment weights from the given CIF string.

    Parameters
    ----------
    analysis : object
        The ``Analysis`` instance to populate.
    cif_text : str
        CIF text content of ``analysis.cif``.
    """
    import gemmi  # noqa: PLC0415

    doc = gemmi.cif.read_string(_wrap_in_data_block(cif_text, 'analysis'))
    block = doc.sole_block()

    # Restore fit configuration
    analysis.fit.from_cif(block)

    # Restore aliases (loop)
    analysis.aliases.from_cif(block)

    # Restore constraints (loop)
    analysis.constraints.from_cif(block)
    if analysis.constraints._items:
        analysis.constraints.enable()

    # Restore joint-fit weights (loop)
    analysis._joint_fit.from_cif(block)


def _make_cif_string_reader(block: gemmi.cif.Block) -> object:
    """
    Return a helper that reads a single CIF tag as a stripped string.

    Parameters
    ----------
    block : gemmi.cif.Block
        Parsed CIF data block.

    Returns
    -------
    object
        A function ``(tag) -> str | None`` that returns the unquoted
        value for *tag*, or ``None`` if not found.
    """

    def _read(tag: str) -> str | None:
        vals = list(block.find_values(tag))
        if not vals:
            return None
        raw = vals[0]
        # CIF unknown / inapplicable markers
        if raw in {'?', '.'}:
            return None
        # Strip surrounding quotes
        if len(raw) >= _MIN_QUOTED_LEN and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            raw = raw[1:-1]
        return raw

    return _read


# TODO: Check the following methods:

######################
# Deserialize from CIF
######################


def param_from_cif(
    self: GenericDescriptorBase,
    block: gemmi.cif.Block,
    idx: int = 0,
) -> None:
    """
    Populate a single descriptor from a CIF block.

    Parameters
    ----------
    self : GenericDescriptorBase
        The descriptor instance to populate.
    block : gemmi.cif.Block
        Parsed CIF block to read values from.
    idx : int, default=0
        Row index used when the tag belongs to a loop.
    """
    found_values: list[Any] = []

    # Try to find the value(s) from the CIF block iterating over
    # the possible cif names in order of preference.
    for tag in self._cif_handler.names:
        candidates = list(block.find_values(tag))
        if candidates:
            found_values = candidates
            break

    # If no values found, the parameter keeps its default value.
    if not found_values:
        return

    # If found, pick the one at the given index
    raw = found_values[idx]

    # CIF unknown / inapplicable markers → keep default
    if raw in {'?', '.'}:
        return

    # If numeric, parse with uncertainty if present
    if self._value_type == DataTypes.NUMERIC:
        has_brackets = '(' in raw
        u = str_to_ufloat(raw)
        self.value = u.n
        if has_brackets and hasattr(self, 'free'):
            self.free = True  # type: ignore[attr-defined]
            if not np.isnan(u.s) and hasattr(self, 'uncertainty'):
                self.uncertainty = u.s  # type: ignore[attr-defined]

    # If string, strip quotes if present
    elif self._value_type == DataTypes.STRING:
        self.value = _strip_optional_quotes(raw)

    elif self._value_type == DataTypes.BOOL:
        self.value = _parse_bool_cif_value(raw)

    # Other types are not supported
    else:
        log.debug(f'Unrecognized type: {self._value_type}')


def category_item_from_cif(
    self: CategoryItem,
    block: gemmi.cif.Block,
    idx: int = 0,
) -> None:
    """Populate each parameter from CIF block at given loop index."""
    for param in self.parameters:
        param.from_cif(block, idx=idx)


def _set_param_from_raw_cif_value(
    param: GenericDescriptorBase,
    raw: str,
) -> None:
    """
    Parse a raw CIF string and set the parameter value.

    Handles numeric values (with optional uncertainty in brackets),
    quoted strings, and unknown/inapplicable CIF markers.

    Parameters
    ----------
    param : GenericDescriptorBase
        The parameter to update.
    raw : str
        The raw string from the CIF loop cell.
    """
    # CIF unknown / inapplicable markers → keep default
    if raw in {'?', '.'}:
        return

    if param._value_type == DataTypes.NUMERIC:
        has_brackets = '(' in raw
        u = str_to_ufloat(raw)
        param.value = u.n
        if has_brackets and hasattr(param, 'free'):
            param.free = True  # type: ignore[attr-defined]
            if not np.isnan(u.s) and hasattr(param, 'uncertainty'):
                param.uncertainty = u.s  # type: ignore[attr-defined]

    # If string, strip quotes if present
    elif param._value_type == DataTypes.STRING:
        param.value = _strip_optional_quotes(raw)

    elif param._value_type == DataTypes.BOOL:
        param.value = _parse_bool_cif_value(raw)

    else:
        log.debug(f'Unrecognized type: {param._value_type}')


def _find_loop_for_category(
    block: object,
    category_item: object,
) -> object | None:
    """
    Find the first CIF loop that matches a category item's parameters.

    Parameters
    ----------
    block : object
        Parsed CIF block to search.
    category_item : object
        Category item whose parameters provide CIF names.

    Returns
    -------
    object | None
        The matching loop, or ``None`` if not found.
    """
    for param in category_item.parameters:
        for name in param._cif_handler.names:
            loop = block.find_loop(name).get_loop()
            if loop is not None:
                return loop
    return None


def category_collection_from_cif(
    self: CategoryCollection,
    block: gemmi.cif.Block,
) -> None:
    """
    Populate a CategoryCollection from a CIF loop.

    Parameters
    ----------
    self : CategoryCollection
        The collection instance to populate.
    block : gemmi.cif.Block
        Parsed CIF block to read the loop from.

    Raises
    ------
    ValueError
        If the collection has no ``_item_type`` defined.
    """
    # TODO: Find a better way and then remove TODO in the AtomSite
    #  class
    # TODO: Rename to _item_cls?
    if self._item_type is None:
        msg = 'Child class is not defined.'
        raise ValueError(msg)

    # Create a temporary instance to access its parameters and
    # parameter CIF names
    category_item = self._item_type()

    # Iterate over category parameters and their possible CIF names
    # trying to find the whole loop it belongs to inside the CIF block
    loop = _find_loop_for_category(block, category_item)

    # If no loop found
    if loop is None:
        log.debug(f'No loop found for category {self}.')
        return

    # Get 2D array of loop values (as strings)
    num_rows = loop.length()
    num_cols = loop.width()
    array = np.array(loop.values, dtype=str).reshape(num_rows, num_cols)

    # Pre-create default items in the collection
    self._adopt_items([self._item_type() for _ in range(num_rows)])

    # Set those items' parameters, which are present in the loop
    for row_idx in range(num_rows):
        current_item = self._items[row_idx]
        for param in current_item.parameters:
            for cif_name in param._cif_handler.names:
                if cif_name in loop.tags:
                    col_idx = loop.tags.index(cif_name)
                    # TODO: The following is duplication of
                    #  param_from_cif
                    _set_param_from_raw_cif_value(param, array[row_idx][col_idx])
                    break
