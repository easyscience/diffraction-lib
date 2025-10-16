# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Any
from typing import Optional
from typing import Sequence

import numpy as np

from easydiffraction.utils.utils import str_to_ufloat


def format_value(value) -> str:
    """Format a single CIF value, quoting strings with whitespace."""
    if isinstance(value, str) and (' ' in value or '\t' in value):
        return f'"{value}"'
    return str(value)


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
    from textwrap import wrap

    wrapped_title = wrap(info.title, width=46)
    wrapped_description = wrap(info.description, width=46)

    title_str = f"_project.title            '{wrapped_title[0]}'" if wrapped_title else ''
    for line in wrapped_title[1:]:
        title_str += f"\n{' ' * 27}'{line}'"

    if wrapped_description:
        base = '_project.description      '
        indent = ' ' * len(base)
        desc_str = f"{base}'{wrapped_description[0]}"
        for line in wrapped_description[1:]:
            desc_str += f'\n{indent}{line}'
        desc_str += "'"
    else:
        desc_str = "_project.description      ''"

    created = info._created.strftime('%d %b %Y %H:%M:%S')
    modified = info._last_modified.strftime('%d %b %Y %H:%M:%S')

    return (
        f'_project.id               {info.name}\n'
        f'{title_str}\n'
        f'{desc_str}\n'
        f"_project.created          '{created}'\n"
        f"_project.last_modified    '{modified}'\n"
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


def param_from_cif(self, block: Any, idx: int = 0) -> None:
    found_values: list[Any] = []
    for tag in self.full_cif_names:
        candidate = list(block.find_values(tag))
        if candidate:
            found_values = candidate
            break
    if not found_values:
        self.value = self.default_value
        return
    raw = found_values[idx]
    if self.value_type is float:
        u = str_to_ufloat(raw)
        self.value = u.n
        if hasattr(self, 'uncertainty'):
            self.uncertainty = u.s  # type: ignore[attr-defined]
    elif self.value_type is str:
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            self.value = raw[1:-1]
        else:
            self.value = raw
    else:
        self.value = raw


def category_item_from_cif(self, block, idx: int = 0) -> None:
    """Populate each parameter from CIF block at given loop index."""
    for param in self.parameters:
        param.from_cif(block, idx=idx)


# TODO: from_cif or add_from_cif as in collections?
def category_collection_from_cif(self, block):
    # Derive loop size using category_entry_name first CIF tag alias
    if self._item_type is None:
        raise ValueError('Child class is not defined.')
    # TODO: Find a better way and then remove TODO in the AtomSite
    #  class
    # Create a temporary instance to access category_entry_name
    # attribute used as ID column for the items in this collection
    child_obj = self._item_type()
    entry_attr = getattr(child_obj, child_obj._category_entry_attr_name)
    # Try to find the value(s) from the CIF block iterating over
    # the possible cif names in order of preference.
    size = 0
    for name in entry_attr.full_cif_names:
        size = len(block.find_values(name))
        break
    # If no values found, nothing to do
    if not size:
        return
    # If values found, delegate to child class to parse each
    # row and add to collection
    for row_idx in range(size):
        child_obj = self._item_type()
        child_obj.from_cif(block, idx=row_idx)
        self.add(child_obj)
