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


def format_value(value: object) -> str:
    """
    Format a single CIF value for output.

    .. note::     The precision must be high enough so that the
    minimizer's     finite-difference Jacobian probes (typically ~1e-8
    relative)     survive the float→string→float round-trip through CIF.
    """
    width = 12
    precision = 8

    # Converting

    # None → CIF unknown marker
    if value is None:
        value = '?'
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

    # Format floats with given precision
    if isinstance(value, float):
        return f'{value:>{width}.{precision}f}'
    # Format strings right-aligned
    if isinstance(value, str):
        return f'{value:>{width}s}'
    # Everything else: fallback
    return str(value)


##################
# Serialize to CIF
##################


def format_param_value(param: object) -> str:
    """
    Format a parameter value for CIF output, encoding the free flag.

    CIF convention for numeric parameters:

    - Fixed or constrained parameter: plain value, e.g. ``3.89090000``
    - Free parameter without uncertainty: value with empty brackets,
      e.g. ``3.89090000()``
    - Free parameter with uncertainty: value with esd in brackets,
      e.g. ``3.89090000(200000)``

    Constrained (dependent) parameters are always written without
    brackets, even if their ``free`` flag is ``True``, because they are
    not independently varied by the minimizer.

    Non-numeric parameters and descriptors without a ``free`` attribute
    are formatted with :func:`format_value`.

    Parameters
    ----------
    param : object
        A descriptor or parameter exposing ``.value`` and optionally
        ``.free``, ``.constrained``, and ``.uncertainty``.

    Returns
    -------
    str
        Formatted CIF value string.
    """
    is_free = getattr(param, 'free', False)
    is_constrained = getattr(param, 'constrained', False)
    value = param.value  # type: ignore[attr-defined]

    if not is_free or is_constrained or not isinstance(value, (int, float)):
        return format_value(value)

    precision = 8
    uncertainty = getattr(param, 'uncertainty', None)
    formatted_value = f'{float(value):.{precision}f}'

    if uncertainty is not None and uncertainty > 0:
        from uncertainties import ufloat as _ufloat  # noqa: PLC0415

        u = _ufloat(float(value), float(uncertainty))
        return f'{u:.{precision}fS}'

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
    """
    if not len(collection):
        return ''

    lines: list[str] = []

    # Header
    first_item = list(collection.values())[0]
    lines.append('loop_')
    for p in first_item.parameters:
        tags = p._cif_handler.names  # type: ignore[attr-defined]
        lines.append(tags[0])

    # Rows
    # Limit number of displayed rows if requested
    if max_display is not None and len(collection) > max_display:
        half_display = max_display // 2
        for i in range(half_display):
            item = list(collection.values())[i]
            row_vals = [format_param_value(p) for p in item.parameters]
            lines.append(' '.join(row_vals))
        lines.append('...')
        for i in range(-half_display, 0):
            item = list(collection.values())[i]
            row_vals = [format_param_value(p) for p in item.parameters]
            lines.append(' '.join(row_vals))
    # No limit
    else:
        for item in collection.values():
            row_vals = [format_param_value(p) for p in item.parameters]
            lines.append(' '.join(row_vals))

    return '\n'.join(lines)


def datablock_item_to_cif(datablock: object) -> str:
    """
    Render a DatablockItem-like object to CIF text.

    Emits a data_ header and then concatenates category CIF sections.
    """
    # Local imports to avoid import-time cycles
    from easydiffraction.core.category import CategoryCollection  # noqa: PLC0415
    from easydiffraction.core.category import CategoryItem  # noqa: PLC0415

    header = f'data_{datablock._identity.datablock_entry_name}'
    parts: list[str] = [header]

    # First categories
    parts.extend(v.as_cif for v in vars(datablock).values() if isinstance(v, CategoryItem))

    # Then collections
    parts.extend(v.as_cif for v in vars(datablock).values() if isinstance(v, CategoryCollection))

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

    if len(info.description) > 60:
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


def project_to_cif(project: object) -> str:
    """Render a whole project by concatenating sections when present."""
    parts: list[str] = []
    if hasattr(project, 'info'):
        parts.append(project.info.as_cif)
    if getattr(project, 'structures', None):
        parts.append(project.structures.as_cif)
    if getattr(project, 'experiments', None):
        parts.append(project.experiments.as_cif)
    if getattr(project, 'analysis', None):
        parts.append(project.analysis.as_cif())
    if getattr(project, 'summary', None):
        parts.append(project.summary.as_cif())
    return '\n\n'.join([p for p in parts if p])


def experiment_to_cif(experiment: object) -> str:
    """Render an experiment: datablock part plus measured data."""
    return datablock_item_to_cif(experiment)


def analysis_to_cif(analysis: object) -> str:
    """Render analysis metadata, aliases, and constraints to CIF."""
    cur_min = format_value(analysis.current_minimizer)
    lines: list[str] = []
    lines.append(f'_analysis.fitting_engine  {cur_min}')
    lines.append(analysis.fit_mode.as_cif)
    lines.append('')
    lines.append(analysis.aliases.as_cif)
    lines.append('')
    lines.append(analysis.constraints.as_cif)
    jfe_cif = analysis.joint_fit_experiments.as_cif
    if jfe_cif:
        lines.append('')
        lines.append(jfe_cif)
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

    _read_cif_string = _make_cif_string_reader(block)

    name = _read_cif_string('_project.id')
    if name is not None:
        info.name = name

    title = _read_cif_string('_project.title')
    if title is not None:
        info.title = title

    description = _read_cif_string('_project.description')
    if description is not None:
        info.description = description


def analysis_from_cif(analysis: object, cif_text: str) -> None:
    """
    Populate an Analysis instance from CIF text.

    Reads the fitting engine, fit mode, aliases, constraints, and
    joint-fit experiment weights from the given CIF string.

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

    _read_cif_string = _make_cif_string_reader(block)

    # Restore minimizer selection
    engine = _read_cif_string('_analysis.fitting_engine')
    if engine is not None:
        from easydiffraction.analysis.fitting import Fitter  # noqa: PLC0415

        analysis.fitter = Fitter(engine)

    # Restore fit mode
    analysis.fit_mode.from_cif(block)

    # Restore aliases (loop)
    analysis.aliases.from_cif(block)

    # Restore constraints (loop)
    analysis.constraints.from_cif(block)
    if analysis.constraints._items:
        analysis.constraints.enable()

    # Restore joint-fit experiment weights (loop)
    analysis._joint_fit_experiments.from_cif(block)


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
        if raw in ('?', '.'):
            return None
        # Strip surrounding quotes
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
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
    if raw in ('?', '.'):
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
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            self.value = raw[1:-1]
        else:
            self.value = raw

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
    def _get_loop(block: object, category_item: object) -> object | None:
        for param in category_item.parameters:
            for name in param._cif_handler.names:
                loop = block.find_loop(name).get_loop()
                if loop is not None:
                    return loop
        return None

    loop = _get_loop(block, category_item)

    # If no loop found
    if loop is None:
        log.debug(f'No loop found for category {self}.')
        return

    # Get 2D array of loop values (as strings)
    num_rows = loop.length()
    num_cols = loop.width()
    array = np.array(loop.values, dtype=str).reshape(num_rows, num_cols)

    # Pre-create default items in the collection
    self._items = [self._item_type() for _ in range(num_rows)]

    # Set parent for each item to enable identity resolution
    for item in self._items:
        object.__setattr__(item, '_parent', self)  # noqa: PLC2801

    # Set those items' parameters, which are present in the loop
    for row_idx in range(num_rows):
        current_item = self._items[row_idx]
        for param in current_item.parameters:
            for cif_name in param._cif_handler.names:
                if cif_name in loop.tags:
                    col_idx = loop.tags.index(cif_name)

                    # TODO: The following is duplication of
                    #  param_from_cif
                    raw = array[row_idx][col_idx]

                    # CIF unknown / inapplicable markers → keep default
                    if raw in ('?', '.'):
                        break

                    # If numeric, parse with uncertainty if present
                    if param._value_type == DataTypes.NUMERIC:
                        has_brackets = '(' in raw
                        u = str_to_ufloat(raw)
                        param.value = u.n
                        if has_brackets and hasattr(param, 'free'):
                            param.free = True  # type: ignore[attr-defined]
                            if not np.isnan(u.s) and hasattr(param, 'uncertainty'):
                                param.uncertainty = u.s  # type: ignore[attr-defined]

                    # If string, strip quotes if present
                    # TODO: Make a helper function for this
                    elif param._value_type == DataTypes.STRING:
                        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
                            param.value = raw[1:-1]
                        else:
                            param.value = raw

                    # Other types are not supported
                    else:
                        log.debug(f'Unrecognized type: {param._value_type}')

                    break
