# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Sequence

import numpy as np

from easydiffraction.core.validation import DataTypes
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import str_to_ufloat

if TYPE_CHECKING:
    import gemmi

    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.parameters import GenericDescriptorBase


def format_value(value) -> str:
    """Format a single CIF value, quoting strings with whitespace."""
    if isinstance(value, str) and (' ' in value or '\t' in value):
        return f'"{value}"'
    return str(value)


##################
# Serialize to CIF
##################


def param_to_cif(param) -> str:
    """Render a single descriptor/parameter to a CIF line.

    Expects ``param`` to expose ``_cif_handler.names`` and ``value``.
    """
    tags: Sequence[str] = param._cif_handler.names  # type: ignore[attr-defined]
    main_key: str = tags[0]
    return f'{main_key} {format_value(param.value)}'


def category_item_to_cif(item) -> str:
    """Render a CategoryItem-like object to CIF text.

    Expects ``item.parameters`` iterable of params with
    ``_cif_handler.names`` and ``value``.
    """
    lines: list[str] = []
    for p in item.parameters:
        lines.append(param_to_cif(p))
    return '\n'.join(lines)


def category_collection_to_cif(collection) -> str:
    """Render a CategoryCollection-like object to CIF text.

    Uses first item to build loop header, then emits rows for each item.
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
    for item in collection.values():
        row_vals = [format_value(p.value) for p in item.parameters]
        lines.append(' '.join(row_vals))

    return '\n'.join(lines)


def datastore_to_cif(datastore, max_points: Optional[int] = None) -> str:
    """Render a datastore to CIF text.

    Expects ``datastore`` to have ``_cif_mapping()`` and attributes per
    mapping keys.
    """
    cif_lines: list[str] = ['loop_']

    mapping: dict[str, str] = datastore._cif_mapping()  # type: ignore[attr-defined]
    for cif_key in mapping.values():
        cif_lines.append(cif_key)

    data_arrays: list[np.ndarray] = []
    for attr_name in mapping:
        arr = getattr(datastore, attr_name, None)
        data_arrays.append(np.array([]) if arr is None else arr)

    if not data_arrays or not data_arrays[0].size:
        return ''

    n_points = len(data_arrays[0])

    def format_row(i: int) -> str:
        return ' '.join(str(data_arrays[j][i]) for j in range(len(data_arrays)))

    if max_points is not None and n_points > 2 * max_points:
        for i in range(max_points):
            cif_lines.append(format_row(i))
        cif_lines.append('...')
        for i in range(-max_points, 0):
            cif_lines.append(format_row(i))
    else:
        for i in range(n_points):
            cif_lines.append(format_row(i))

    return '\n'.join(cif_lines)


def datablock_item_to_cif(datablock) -> str:
    """Render a DatablockItem-like object to CIF text.

    Emits a data_ header and then concatenates category CIF sections.
    """
    # Local imports to avoid import-time cycles
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem

    header = f'data_{datablock._identity.datablock_entry_name}'
    parts: list[str] = [header]
    for v in vars(datablock).values():
        if isinstance(v, CategoryItem):
            parts.append(v.as_cif)
    for v in vars(datablock).values():
        if isinstance(v, CategoryCollection):
            parts.append(v.as_cif)
    return '\n\n'.join(parts)


def datablock_collection_to_cif(collection) -> str:
    """Render a collection of datablocks by joining their CIF blocks."""
    return '\n\n'.join([block.as_cif for block in collection.values()])


def project_info_to_cif(info) -> str:
    """Render ProjectInfo to CIF text (id, title, description,
    dates).
    """
    name = f'{info.name}'

    title = f'{info.title}'
    if ' ' in title:
        title = f"'{title}'"

    if len(info.description) > 60:
        description = f'\n;\n{info.description}\n;'
    else:
        description = f'{info.description}'
        if ' ' in description:
            description = f"'{description}'"

    created = f"'{info._created.strftime('%d %b %Y %H:%M:%S')}'"
    last_modified = f"'{info._last_modified.strftime('%d %b %Y %H:%M:%S')}'"

    return (
        f'_project.id               {name}\n'
        f'_project.title            {title}\n'
        f'_project.description      {description}\n'
        f'_project.created          {created}\n'
        f'_project.last_modified    {last_modified}'
    )


def project_to_cif(project) -> str:
    """Render a whole project by concatenating sections when present."""
    parts: list[str] = []
    if hasattr(project, 'info'):
        parts.append(project.info.as_cif)
    if getattr(project, 'sample_models', None):
        parts.append(project.sample_models.as_cif)
    if getattr(project, 'experiments', None):
        parts.append(project.experiments.as_cif)
    if getattr(project, 'analysis', None):
        parts.append(project.analysis.as_cif())
    if getattr(project, 'summary', None):
        parts.append(project.summary.as_cif())
    return '\n\n'.join([p for p in parts if p])


def experiment_to_cif(experiment) -> str:
    """Render an experiment: datablock part plus measured data."""
    block = datablock_item_to_cif(experiment)
    data = experiment.datastore.as_cif
    return f'{block}\n\n{data}' if data else block


def analysis_to_cif(analysis) -> str:
    """Render analysis metadata, aliases, and constraints to CIF."""
    cur_min = format_value(analysis.current_minimizer)
    lines: list[str] = []
    lines.append(f'_analysis.calculator_engine  {format_value(analysis.current_calculator)}')
    lines.append(f'_analysis.fitting_engine  {cur_min}')
    lines.append(f'_analysis.fit_mode  {format_value(analysis.fit_mode)}')
    lines.append('')
    lines.append(analysis.aliases.as_cif)
    lines.append('')
    lines.append(analysis.constraints.as_cif)
    return '\n'.join(lines)


def summary_to_cif(_summary) -> str:
    """Render a summary CIF block (placeholder for now)."""
    return 'To be added...'


# TODO: Check the following methods:

######################
# Deserialize from CIF
######################


def param_from_cif(
    self: GenericDescriptorBase,
    block: gemmi.cif.Block,
    idx: int = 0,
) -> None:
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
    # If numeric, parse with uncertainty if present
    if self._value_type == DataTypes.NUMERIC:
        u = str_to_ufloat(raw)
        self.value = u.n
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


# TODO: from_cif or add_from_cif as in collections?
def category_collection_from_cif(self: CategoryCollection, block: gemmi.cif.Block) -> None:
    # TODO: Find a better way and then remove TODO in the AtomSite
    #  class
    if self._item_type is None:
        raise ValueError('Child class is not defined.')
    # Create a temporary instance to access category_code needed
    # to find the loop in the CIF block
    child_obj = self._item_type()
    category_code = child_obj._identity.category_code
    # Derive row count from category code
    row_count = len(block.find_mmcif_category(f'_{category_code}.'))
    # Delegate to child class to parse each row and add to collection
    for row_idx in range(row_count):
        child_obj = self._item_type()
        child_obj.from_cif(block, idx=row_idx)
        self.add(child_obj)
