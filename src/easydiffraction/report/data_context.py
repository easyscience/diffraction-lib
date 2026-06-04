# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Build shared data for report renderers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC
from datetime import datetime

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.datablock import DEFAULT_LOOP_DISPLAY_LIMIT
from easydiffraction.core.variable import GenericDescriptorBase
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.display.plotters.base import DEFAULT_AXES_LABELS
from easydiffraction.display.plotters.base import DEFAULT_X_AXIS
from easydiffraction.display.plotting import Plotter
from easydiffraction.io.cif.serialize import format_param_value
from easydiffraction.utils.utils import package_version

_STRUCTURE_CELL_FIELDS = (
    'length_a',
    'length_b',
    'length_c',
    'angle_alpha',
    'angle_beta',
    'angle_gamma',
)
_ATOM_SITE_FIELDS = (
    'label',
    'type_symbol',
    'fract_x',
    'fract_y',
    'fract_z',
    'occupancy',
    'adp_iso',
)
_ATOM_SITE_ANISO_FIELDS = (
    'label',
    'adp_11',
    'adp_22',
    'adp_33',
    'adp_12',
    'adp_13',
    'adp_23',
)
_EXPERIMENT_TYPE_FIELDS = (
    'sample_form',
    'beam_mode',
    'radiation_probe',
    'scattering_type',
)
_EXPERIMENT_DIFFRN_FIELDS = (
    'ambient_temperature',
    'ambient_pressure',
)
_REPORT_LOOP_DISPLAY_LIMIT = DEFAULT_LOOP_DISPLAY_LIMIT
_FULL_WIDTH_TABLE_CHAR_LIMIT = 40
_TRUNCATED_DATA_CATEGORY_CODES = frozenset({'pd_data', 'total_data'})
_NUMERIC_TEXT_RE = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\(\d+\))?(?:[eE][+-]?\d+)?$')
_ADP_ANISO_CIF_RE = re.compile(r'^_atom_site_aniso\.([BU])_(\d{2})$')
_NUMBER_PARTS_RE = re.compile(
    r'^(?P<sign>[+-]?)'
    r'(?:(?P<integer>\d+)(?:\.(?P<fraction>\d*))?'
    r'|\.(?P<leading_fraction>\d+))'
    r'(?P<uncertainty>\(\d+\))?'
    r'(?P<exponent>[eE][+-]?\d+)?$'
)
_MATH_FRAGMENT_RE = re.compile(r'\$([^$]+)\$')


def _format_generated_at(moment: datetime) -> str:
    """Return a human-readable report generation timestamp."""
    return f'{moment.day} {moment:%B %Y, %H:%M}'


class ReportDataContext:
    """
    Build renderer-neutral report data from a project.

    Parameters
    ----------
    project : object
        Project facade that owns structures, experiments, and analysis.
    """

    def __init__(self, project: object) -> None:
        self._project = project

    def build(self) -> dict[str, object]:
        """
        Return the full report data context.

        Returns
        -------
        dict[str, object]
            Renderer-neutral data consumed by terminal, HTML, TeX, and
            GUI report surfaces.
        """
        project = self._project
        structures = list(_collection_values(_safe_attr(project, 'structures')))
        experiments = list(_collection_values(_safe_attr(project, 'experiments')))
        return {
            'project': self._project_context(structures, experiments),
            'structures': [self._structure_context(structure) for structure in structures],
            'experiments': [self._experiment_context(experiment) for experiment in experiments],
            'analysis': self._analysis_context(),
            'metadata': {
                'easydiffraction_version': package_version('easydiffraction'),
                'generated_at': _format_generated_at(datetime.now(tz=UTC)),
            },
        }

    def _project_context(
        self,
        structures: list[object],
        experiments: list[object],
    ) -> dict[str, object]:
        """Return project metadata for report rendering."""
        info = _safe_attr(self._project, 'info')
        return {
            'name': _safe_attr(self._project, 'name'),
            'title': _attr_value(info, 'title'),
            'description': _attr_value(info, 'description'),
            'n_phases': len(structures),
            'n_experiments': len(experiments),
        }

    def _structure_context(self, structure: object) -> dict[str, object]:
        """Return one structure summary."""
        space_group = _safe_attr(structure, 'space_group')
        cell = _safe_attr(structure, 'cell')
        atom_sites = list(_collection_values(_safe_attr(structure, 'atom_sites')))
        aniso_sites = list(_collection_values(_safe_attr(structure, 'atom_site_aniso')))
        return {
            'id': _safe_attr(structure, 'name'),
            'space_group': _attr_value(space_group, 'name_h_m'),
            'crystal_system': _attr_value(space_group, 'crystal_system'),
            'cell': _display_field_values(
                cell,
                _STRUCTURE_CELL_FIELDS,
            ),
            'cell_display': _display_field_metadata(
                cell,
                _STRUCTURE_CELL_FIELDS,
                context='html',
            ),
            'cell_latex': _display_field_metadata(
                cell,
                _STRUCTURE_CELL_FIELDS,
                context='latex',
            ),
            'atom_sites': [self._atom_site_context(atom_site) for atom_site in atom_sites],
            'atom_site_display': _display_field_metadata(
                atom_sites[0] if atom_sites else None,
                _ATOM_SITE_FIELDS,
                context='html',
            ),
            'atom_site_latex': _display_field_metadata(
                atom_sites[0] if atom_sites else None,
                _ATOM_SITE_FIELDS,
                context='latex',
            ),
            'atom_site_aniso': [
                self._atom_site_aniso_context(aniso_site) for aniso_site in aniso_sites
            ],
            'atom_site_aniso_display': _display_field_metadata(
                aniso_sites[0] if aniso_sites else None,
                _ATOM_SITE_ANISO_FIELDS,
                context='html',
            ),
            'atom_site_aniso_latex': _display_field_metadata(
                aniso_sites[0] if aniso_sites else None,
                _ATOM_SITE_ANISO_FIELDS,
                context='latex',
            ),
            'categories': _category_contexts(structure),
        }

    @staticmethod
    def _atom_site_context(atom_site: object) -> dict[str, object]:
        """Return one atom-site row."""
        return {
            'label': _attr_value(atom_site, 'label'),
            'type_symbol': _attr_value(atom_site, 'type_symbol'),
            'fract_x': _attr_display_value(atom_site, 'fract_x'),
            'fract_y': _attr_display_value(atom_site, 'fract_y'),
            'fract_z': _attr_display_value(atom_site, 'fract_z'),
            'occupancy': _attr_display_value(atom_site, 'occupancy'),
            'adp_type': _attr_value(atom_site, 'adp_type'),
            'adp_iso': _attr_display_value(atom_site, 'adp_iso'),
        }

    @staticmethod
    def _atom_site_aniso_context(aniso_site: object) -> dict[str, object]:
        """Return one atom-site-aniso row."""
        return {
            'label': _attr_value(aniso_site, 'label'),
            'adp_11': _attr_display_value(aniso_site, 'adp_11'),
            'adp_22': _attr_display_value(aniso_site, 'adp_22'),
            'adp_33': _attr_display_value(aniso_site, 'adp_33'),
            'adp_12': _attr_display_value(aniso_site, 'adp_12'),
            'adp_13': _attr_display_value(aniso_site, 'adp_13'),
            'adp_23': _attr_display_value(aniso_site, 'adp_23'),
        }

    @staticmethod
    def _experiment_context(experiment: object) -> dict[str, object]:
        """Return one experiment summary."""
        calculator = _safe_attr(experiment, 'calculator')
        diffrn = _safe_attr(experiment, 'diffrn')
        return {
            'id': _safe_attr(experiment, 'name'),
            'type': _field_values(
                _safe_attr(experiment, 'type'),
                _EXPERIMENT_TYPE_FIELDS,
            ),
            'calculator': {
                'type': _attr_value(calculator, 'type'),
            },
            'diffrn': {
                'ambient_temperature': _attr_value(
                    diffrn,
                    'ambient_temperature',
                ),
                'ambient_pressure': _attr_value(
                    diffrn,
                    'ambient_pressure',
                ),
            },
            'diffrn_display': _display_field_metadata(
                diffrn,
                _EXPERIMENT_DIFFRN_FIELDS,
                context='html',
            ),
            'diffrn_latex': _display_field_metadata(
                diffrn,
                _EXPERIMENT_DIFFRN_FIELDS,
                context='latex',
            ),
            'measured_range': _value(_safe_attr(experiment, 'measured_range')),
            'fit_data': _fit_data_context(experiment),
            'categories': _category_contexts(
                experiment,
                truncate_codes=_TRUNCATED_DATA_CATEGORY_CODES,
            ),
        }

    def _analysis_context(self) -> dict[str, object]:
        """Return analysis-section data for report rendering."""
        analysis = _safe_attr(self._project, 'analysis')
        return {
            'software': self._software_context(),
            'categories': _analysis_category_contexts(analysis),
        }

    def _software_context(self) -> dict[str, object]:
        """Return analysis software-provenance data."""
        analysis = _safe_attr(self._project, 'analysis')
        software = _safe_attr(analysis, 'software')
        return {
            'framework': _software_role_context(_safe_attr(software, 'framework')),
            'calculator': _software_role_context(_safe_attr(software, 'calculator')),
            'minimizer': _software_role_context(_safe_attr(software, 'minimizer')),
            'fit_datetime': _attr_value(software, 'timestamp'),
        }


def build_report_data_context(project: object) -> dict[str, object]:
    """
    Build renderer-neutral report data from a project.

    Parameters
    ----------
    project : object
        Project facade to summarize.

    Returns
    -------
    dict[str, object]
        Data context shared by all report renderers.
    """
    return ReportDataContext(project).build()


def _safe_attr(owner: object, attr_name: str) -> object:
    """Return a public attribute without triggering diagnostics."""
    if owner is None:
        return None
    public_attrs = getattr(type(owner), '_public_attrs', None)
    if callable(public_attrs) and attr_name not in public_attrs():
        return None
    return getattr(owner, attr_name, None)


def _value(value: object) -> object:
    """Return descriptor values, otherwise return the object itself."""
    return getattr(value, 'value', value)


def _display_value(value: object) -> object:
    """Return a report-display value, preserving parameter s.u."""
    if isinstance(value, Parameter):
        formatted = format_param_value(value)
        if formatted.endswith('()'):
            return _value(value)
        return formatted
    return _value(value)


def _attr_value(owner: object, attr_name: str) -> object:
    """Return one public attribute value."""
    return _value(_safe_attr(owner, attr_name))


def _attr_display_value(owner: object, attr_name: str) -> object:
    """Return one public attribute display value."""
    return _display_value(_safe_attr(owner, attr_name))


def _field_values(owner: object, fields: tuple[str, ...]) -> dict[str, object]:
    """Return descriptor values for a fixed field list."""
    return {field: _attr_value(owner, field) for field in fields}


def _display_field_values(owner: object, fields: tuple[str, ...]) -> dict[str, object]:
    """Return display values for a fixed field list."""
    return {field: _attr_display_value(owner, field) for field in fields}


def _display_field_metadata(
    owner: object,
    fields: tuple[str, ...],
    *,
    context: str,
) -> dict[str, dict[str, str]]:
    """Return display labels and units for a fixed field list."""
    return {
        field: _display_metadata(_safe_attr(owner, field), context=context) for field in fields
    }


def _display_metadata(value: object, *, context: str) -> dict[str, str]:
    """Return display label and units for one descriptor."""
    name_resolver = getattr(value, 'resolve_display_name', None)
    label = name_resolver(context) if callable(name_resolver) else ''
    units = _descriptor_units(value, context=context)
    return {'label': label, 'units': _display_units(units)}


def _analysis_category_contexts(analysis: object) -> list[dict[str, object]]:
    """Return generic report contexts for analysis result categories."""
    categories = (
        _safe_attr(analysis, 'minimizer'),
        _safe_attr(analysis, 'fitting_mode'),
        _safe_attr(analysis, 'fit_result'),
    )
    contexts = []
    for category in categories:
        if category is None:
            continue
        context = _category_context(category)
        if _category_has_content(context):
            contexts.append(context)
    return contexts


def _category_contexts(
    owner: object,
    *,
    skip_codes: frozenset[str] | None = None,
    truncate_codes: frozenset[str] | None = None,
) -> list[dict[str, object]]:
    """Return report rows for each public category on an owner."""
    if skip_codes is None:
        skip_codes = frozenset()
    if truncate_codes is None:
        truncate_codes = frozenset()
    categories = getattr(owner, 'categories', ())
    contexts = []
    for category in categories:
        if _skip_category(category, skip_codes):
            continue
        context = _category_context(
            category,
            truncate=_category_code(category) in truncate_codes,
        )
        if _category_has_content(context):
            contexts.append(context)
    return contexts


def _skip_category(category: object, skip_codes: frozenset[str]) -> bool:
    """Return whether a category should be omitted from reports."""
    category_code = _category_code(category)
    if category_code in skip_codes:
        return True

    skip = getattr(category, '_skip_cif_serialization', None)
    return bool(callable(skip) and skip())


def _category_context(category: object, *, truncate: bool = False) -> dict[str, object]:
    """Return one generic category-rendering context."""
    if isinstance(category, CategoryCollection):
        return _collection_category_context(category, truncate=truncate)
    return _item_category_context(category)


def _item_category_context(category: object) -> dict[str, object]:
    """Return a non-loop category context."""
    rows = _defined_descriptor_rows(_descriptor_rows(_category_parameters(category)))
    has_numeric_values = _rows_have_numeric_values(rows)
    return {
        'kind': 'item',
        'code': _category_code(category),
        'title': _category_title(category),
        'rows': rows,
        'has_numeric_values': has_numeric_values,
        'value_column_numeric': has_numeric_values,
        'colspec': _key_value_colspec(rows),
    }


def _collection_category_context(
    category: CategoryCollection,
    *,
    truncate: bool = False,
) -> dict[str, object]:
    """Return a loop-category context."""
    items = list(category.values())
    columns = _collection_columns(category, items)
    rows = [_collection_row(category, item, columns) for item in items]
    rows = [row for row in rows if _loop_row_has_report_values(row)]
    if truncate:
        rows = _truncate_loop_rows(rows)
    scalar_rows = _defined_descriptor_rows(_descriptor_rows(category.scalar_descriptors))
    _mark_numeric_columns(columns, rows)
    _apply_cell_number_alignment(columns, rows)
    return {
        'kind': 'loop',
        'code': _category_code(category),
        'title': _category_title(category),
        'scalar_rows': scalar_rows,
        'scalar_has_numeric_values': _rows_have_numeric_values(scalar_rows),
        'scalar_colspec': _key_value_colspec(scalar_rows),
        'columns': columns,
        'rows': rows,
        'colspec': _loop_colspec(columns),
        'table_width': _loop_table_width(columns, rows),
    }


def _category_has_content(context: dict[str, object]) -> bool:
    """Return whether a category context has renderable content."""
    if context['kind'] == 'item':
        return bool(context['rows'])
    return bool(context['rows'] or context['scalar_rows'])


def _defined_descriptor_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Return descriptor rows whose value column is populated."""
    return [row for row in rows if not _is_empty_value(row['value'])]


def _loop_row_has_report_values(row: dict[str, object]) -> bool:
    """Return whether a loop row has more than an identifier value."""
    return _loop_row_value_count(row) > 1


def _loop_row_value_count(row: dict[str, object]) -> int:
    """Return the number of populated cells in a loop row."""
    return sum(1 for cell in row['cells'] if not _is_empty_value(cell['value']))


def _truncate_loop_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Return display-truncated loop rows with an ellipsis row."""
    if len(rows) <= _REPORT_LOOP_DISPLAY_LIMIT:
        return rows

    half_limit = _REPORT_LOOP_DISPLAY_LIMIT // 2
    return [
        *rows[:half_limit],
        _ellipsis_loop_row(rows[0]),
        *rows[-half_limit:],
    ]


def _ellipsis_loop_row(reference_row: dict[str, object]) -> dict[str, object]:
    """Return an ellipsis row matching a loop row shape."""
    cells = [{'value': '...', 'numeric': False, 'number': None}]
    cells.extend(
        {'value': '', 'numeric': False, 'number': None} for _ in reference_row['cells'][1:]
    )
    return {'cells': cells}


def _loop_table_width(
    columns: list[dict[str, object]],
    rows: list[dict[str, object]],
) -> str:
    """Return the report width bucket for a loop table."""
    if _estimated_loop_table_chars(columns, rows) > _FULL_WIDTH_TABLE_CHAR_LIMIT:
        return 'full'
    return 'half'


def _estimated_loop_table_chars(
    columns: list[dict[str, object]],
    rows: list[dict[str, object]],
) -> int:
    """Return an approximate monospace width for loop content."""
    widths = []
    for index, column in enumerate(columns):
        label_width = len(_plain_table_text(_column_display_label(column)))
        value_width = max(
            (len(_plain_table_text(row['cells'][index]['value'])) for row in rows),
            default=0,
        )
        widths.append(max(label_width, value_width) + 4)
    return sum(widths)


def _column_display_label(column: dict[str, object]) -> str:
    """Return the preferred display label for width estimation."""
    label = column.get('html_label') or column.get('label') or column.get('name')
    units = column.get('html_units') or column.get('units')
    if units:
        return f'{label} ({units})'
    return str(label)


def _plain_table_text(value: object) -> str:
    """Return approximate plain text for table width estimates."""
    if value is None:
        return ''
    return str(value)


def _collection_columns(
    category: CategoryCollection,
    items: list[object],
) -> list[dict[str, object]]:
    """Return loop column metadata from the first row item."""
    if not items:
        return []
    columns = [
        _column_context(parameter) for parameter in _collection_loop_parameters(category, items[0])
    ]
    _apply_collection_adp_column_labels(category, columns, items)
    return columns


def _apply_collection_adp_column_labels(
    category: CategoryCollection,
    columns: list[dict[str, object]],
    items: list[object],
) -> None:
    """Set ADP column labels from active B/U CIF tag families."""
    row_parameters = [_collection_loop_parameters(category, item) for item in items]
    for index, column in enumerate(columns):
        label_contexts = [
            label_context
            for parameters in row_parameters
            if index < len(parameters)
            for label_context in [_adp_label_context(parameters[index])]
            if label_context is not None
        ]
        if not label_contexts:
            continue
        column.update(_merge_label_contexts(label_contexts))


def _merge_label_contexts(
    label_contexts: list[dict[str, str]],
) -> dict[str, str]:
    """Return merged labels, preserving the first-seen family order."""
    return {
        'label': _merge_label_values(context['label'] for context in label_contexts),
        'latex_label': _merge_label_values(context['latex_label'] for context in label_contexts),
        'html_label': _merge_label_values(context['html_label'] for context in label_contexts),
    }


def _merge_label_values(values: Iterable[str]) -> str:
    """Return slash-separated unique labels."""
    unique_values = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return ' / '.join(unique_values)


def _collection_row(
    category: CategoryCollection,
    item: object,
    columns: list[dict[str, object]],
) -> dict[str, object]:
    """Return one loop row."""
    parameters = _collection_loop_parameters(category, item)
    values = [_display_value(parameter) for parameter in parameters]
    cells = [
        {'value': value, 'numeric': column['numeric'], 'number': None}
        for value, column in zip(values, columns, strict=True)
    ]
    return {'cells': cells}


def _collection_loop_parameters(
    category: CategoryCollection,
    item: object,
) -> list[GenericDescriptorBase]:
    """Return the descriptors that define a collection row."""
    loop_parameters = getattr(category, '_cif_loop_parameters', None)
    if callable(loop_parameters):
        return list(loop_parameters(item))
    return list(item.parameters)


def _category_parameters(category: object) -> list[GenericDescriptorBase]:
    """Return descriptors that define a non-loop category."""
    parameters = getattr(category, 'parameters', ())
    return list(parameters)


def _descriptor_rows(
    parameters: Iterable[GenericDescriptorBase],
) -> list[dict[str, object]]:
    """Return key-value table rows from descriptors."""
    rows = []
    for parameter in parameters:
        value = _display_value(parameter)
        rows.append({
            'name': parameter.name,
            'label': _display_label(parameter, context='html'),
            'latex_label': _display_label(parameter, context='latex'),
            'html_label': _html_label(parameter),
            'units': _display_units(_descriptor_units(parameter, context='html')),
            'latex_units': _display_units(_descriptor_units(parameter, context='latex')),
            'html_units': _html_units(parameter),
            'value': value,
            'numeric': _descriptor_is_numeric(parameter) and _is_numeric_value(value),
            'number': None,
        })
    _apply_row_number_alignment(rows)
    return rows


def _column_context(parameter: GenericDescriptorBase) -> dict[str, object]:
    """Return loop-column metadata from one descriptor."""
    return {
        'name': parameter.name,
        'label': _display_label(parameter, context='html'),
        'latex_label': _display_label(parameter, context='latex'),
        'html_label': _html_label(parameter),
        'units': _display_units(_descriptor_units(parameter, context='html')),
        'latex_units': _display_units(_descriptor_units(parameter, context='latex')),
        'html_units': _html_units(parameter),
        'numeric': False,
        'numeric_candidate': _descriptor_is_numeric(parameter),
    }


def _mark_numeric_columns(
    columns: list[dict[str, object]],
    rows: list[dict[str, object]],
) -> None:
    """Mark each loop column that can use numeric alignment."""
    for index, column in enumerate(columns):
        column_values = [row['cells'][index]['value'] for row in rows]
        is_numeric = bool(column['numeric_candidate']) and _values_are_numeric(column_values)
        column['numeric'] = is_numeric
        if is_numeric:
            column['table_format'] = _siunitx_table_format(column_values)
        column.pop('numeric_candidate', None)
        for row in rows:
            row['cells'][index]['numeric'] = is_numeric


def _loop_colspec(columns: list[dict[str, object]]) -> str:
    """Return a TeX tabular column spec for loop-category tables."""
    return ''.join(_loop_column_colspec(column) for column in columns)


def _key_value_colspec(rows: list[dict[str, object]]) -> str:
    """Return a TeX tabular column spec for key-value tables."""
    if not _rows_have_numeric_values(rows):
        return 'll'
    values = [row['value'] for row in rows if row['numeric']]
    return f'l{_numeric_colspec(values)}'


def _loop_column_colspec(column: dict[str, object]) -> str:
    """Return one TeX tabular column spec."""
    if not column['numeric']:
        return 'c'
    table_format = column.get('table_format')
    if table_format:
        return _numeric_colspec_from_format(str(table_format))
    return _numeric_colspec([])


def _numeric_colspec(values: Iterable[object]) -> str:
    """Return one compact siunitx numeric column spec."""
    return _numeric_colspec_from_format(_siunitx_table_format(values))


def _numeric_colspec_from_format(table_format: str) -> str:
    """Return one siunitx column spec from a table-format value."""
    return f'S[table-format={table_format}]'


def _siunitx_table_format(values: Iterable[object]) -> str:
    """Return a compact siunitx table-format for numeric values."""
    parts = [
        parts
        for value in values
        if not _is_empty_value(value)
        for parts in [_siunitx_number_parts(value)]
        if parts is not None
    ]
    if not parts:
        return '1.0'

    sign = '+' if any(part['has_sign'] for part in parts) else ''
    integer_digits = max(int(part['integer_digits']) for part in parts)
    fraction_digits = max(int(part['fraction_digits']) for part in parts)
    uncertainty_digits = max(int(part['uncertainty_digits']) for part in parts)
    table_format = f'{sign}{integer_digits}.{fraction_digits}'
    if uncertainty_digits:
        table_format = f'{table_format}({uncertainty_digits})'
    return table_format


def _siunitx_number_parts(value: object) -> dict[str, object] | None:
    """Return table-format parts for one numeric value."""
    match = _NUMBER_PARTS_RE.match(_number_text(value))
    if match is None:
        return None

    integer = match.group('integer')
    leading_fraction = match.group('leading_fraction')
    fraction = match.group('fraction')
    uncertainty = match.group('uncertainty') or ''
    return {
        'has_sign': bool(match.group('sign')),
        'integer_digits': len(integer or '0'),
        'fraction_digits': len(leading_fraction or fraction or ''),
        'uncertainty_digits': len(uncertainty.strip('()')),
    }


def _apply_row_number_alignment(rows: list[dict[str, object]]) -> None:
    """Add HTML decimal-alignment metadata to key-value rows."""
    number_parts = [_number_parts(row['value']) if row['numeric'] else None for row in rows]
    left_ch, right_ch = _number_widths(number_parts)
    for row, parts in zip(rows, number_parts, strict=True):
        row['number'] = _number_context(parts, left_ch, right_ch)


def _apply_cell_number_alignment(
    columns: list[dict[str, object]],
    rows: list[dict[str, object]],
) -> None:
    """Add HTML decimal-alignment metadata to loop cells."""
    for index, column in enumerate(columns):
        if not column['numeric']:
            continue
        number_parts = [_number_parts(row['cells'][index]['value']) for row in rows]
        left_ch, right_ch = _number_widths(number_parts)
        column['number_left_ch'] = left_ch
        column['number_right_ch'] = right_ch
        for row, parts in zip(rows, number_parts, strict=True):
            row['cells'][index]['number'] = _number_context(
                parts,
                left_ch,
                right_ch,
            )


def _number_widths(
    number_parts: Iterable[dict[str, object] | None],
) -> tuple[int, int]:
    """Return left and right character widths for numeric cells."""
    populated = [parts for parts in number_parts if parts is not None]
    if not populated:
        return 0, 0
    left_ch = max(len(str(parts['left'])) for parts in populated)
    right_ch = max(len(str(parts['right'])) for parts in populated)
    return left_ch, right_ch


def _number_context(
    parts: dict[str, object] | None,
    left_ch: int,
    right_ch: int,
) -> dict[str, object] | None:
    """Return one number context with column widths attached."""
    if parts is None:
        return None
    return {
        **parts,
        'left_ch': max(left_ch, 1),
        'right_ch': max(right_ch, 1),
    }


def _number_parts(value: object) -> dict[str, object] | None:
    """Split one numeric display value around its decimal marker."""
    text = _number_text(value)
    match = _NUMBER_PARTS_RE.match(text)
    if match is None:
        return None

    sign = match.group('sign') or ''
    integer = match.group('integer')
    leading_fraction = match.group('leading_fraction')
    fraction = match.group('fraction')
    if integer is None:
        left = f'{sign}0'
        right_fraction = leading_fraction or ''
        has_decimal = True
    else:
        left = f'{sign}{integer}'
        right_fraction = fraction or ''
        has_decimal = fraction is not None

    uncertainty = match.group('uncertainty') or ''
    exponent = match.group('exponent') or ''
    return {
        'left': left,
        'right': f'{right_fraction}{uncertainty}{exponent}',
        'has_decimal': has_decimal,
    }


def _number_text(value: object) -> str:
    """Return a compact text representation for alignment."""
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return f'{value:.6g}'
    return str(value).strip()


def _values_are_numeric(values: Iterable[object]) -> bool:
    """Return whether all populated values are numeric."""
    populated_values = [value for value in values if not _is_empty_value(value)]
    return bool(populated_values) and all(_is_numeric_value(value) for value in populated_values)


def _rows_have_numeric_values(rows: Iterable[dict[str, object]]) -> bool:
    """Return whether any descriptor row has a numeric value."""
    return any(row['numeric'] for row in rows)


def _is_empty_value(value: object) -> bool:
    """Return whether a table cell should be treated as empty."""
    return value is None or (isinstance(value, str) and not value)


def _is_numeric_value(value: object) -> bool:
    """Return whether a value can be typeset as a number."""
    if isinstance(value, bool):
        return False
    if isinstance(value, (float, int)):
        return True
    return isinstance(value, str) and bool(_NUMERIC_TEXT_RE.match(value.strip()))


def _descriptor_is_numeric(parameter: GenericDescriptorBase) -> bool:
    """Return whether a descriptor semantically stores numeric data."""
    return isinstance(parameter, (IntegerDescriptor, NumericDescriptor, Parameter))


def _display_label(parameter: GenericDescriptorBase, *, context: str) -> str:
    """Return a display label for a descriptor."""
    adp_label = _adp_display_label(parameter, context=context)
    if adp_label is not None:
        return adp_label
    label = parameter.resolve_display_name(context)
    return label or parameter.name


def _adp_label_context(parameter: object) -> dict[str, str] | None:
    """Return report label metadata for active ADP tag families."""
    label = _adp_display_label(parameter, context='html')
    latex_label = _adp_display_label(parameter, context='latex')
    if label is None or latex_label is None:
        return None
    return {
        'label': label,
        'latex_label': latex_label,
        'html_label': _html_markup(latex_label),
    }


def _adp_display_label(parameter: object, *, context: str) -> str | None:
    """Return a B/U-aware ADP display label when applicable."""
    cif_name = _first_cif_name(parameter)
    if cif_name == '_atom_site.B_iso_or_equiv':
        return _adp_iso_label('B', context=context)
    if cif_name == '_atom_site.U_iso_or_equiv':
        return _adp_iso_label('U', context=context)

    match = _ADP_ANISO_CIF_RE.match(cif_name or '')
    if match is None:
        return None
    family = match.group(1)
    suffix = match.group(2)
    if context == 'latex':
        return rf'${family}_{{{suffix}}}$'
    return f'{family}{suffix}'


def _adp_iso_label(family: str, *, context: str) -> str:
    """Return one isotropic ADP label."""
    if context == 'latex':
        return rf'${family}_{{\mathrm{{iso}}}}$'
    return f'{family}iso'


def _first_cif_name(parameter: object) -> str | None:
    """Return the first CIF tag for a descriptor."""
    cif_handler = getattr(parameter, '_cif_handler', None)
    names = getattr(cif_handler, 'names', ())
    if not names:
        return None
    return str(names[0])


def _display_units(units: object) -> str:
    """Return display units, suppressing placeholder unit labels."""
    if units is None:
        return ''
    units_text = str(units)
    if units_text.lower() == 'none':
        return ''
    return units_text


def _html_label(parameter: GenericDescriptorBase) -> str:
    """Return a MathJax-capable HTML label for one descriptor."""
    latex_label = _display_label(parameter, context='latex')
    if _has_explicit_latex(parameter) and _is_latex_markup(latex_label):
        return _html_markup(latex_label)
    return _display_label(parameter, context='html')


def _html_units(parameter: GenericDescriptorBase) -> str:
    """Return MathJax-capable HTML units for one descriptor."""
    latex_units = _display_units(_descriptor_units(parameter, context='latex'))
    if not latex_units:
        return ''
    if _is_latex_markup(latex_units):
        return _mathjax_text(latex_units)

    html_units = _display_units(_descriptor_units(parameter, context='html'))
    return _plain_unit_text(html_units or latex_units)


def _has_explicit_latex(parameter: GenericDescriptorBase) -> bool:
    """Return whether a descriptor declares LaTeX display metadata."""
    display_handler = _safe_attr(parameter, 'display_handler')
    return display_handler is not None and display_handler.latex_name is not None


def _is_latex_markup(value: object) -> bool:
    """Return whether a display string contains TeX markup."""
    text = str(value)
    return '$' in text or '\\' in text


def _mathjax_text(value: object) -> str:
    """Return inline MathJax text from a LaTeX fragment."""
    text = _mathjax_markup(str(value).replace('$', ''))
    return rf'\({text}\)'


def _html_markup(value: object) -> str:
    """Return HTML text with inline LaTeX fragments as MathJax."""
    text = str(value)
    if '$' in text:
        return _MATH_FRAGMENT_RE.sub(
            lambda match: _mathjax_text(match.group(1)),
            text,
        )
    if '\\' in text:
        return _mathjax_text(text)
    return text


def _mathjax_markup(value: str) -> str:
    """Return LaTeX markup normalized for MathJax rendering."""
    placeholder = '__EASYDIFFRACTION_ANGSTROM__'
    text = _degree_unit_math(value)
    text = text.replace(r'\mathrm{\AA}', placeholder)
    text = text.replace(r'\AA', r'\mathring{\mathrm{A}}')
    return text.replace(placeholder, r'\mathring{\mathrm{A}}')


def _degree_unit_math(value: str) -> str:
    """Return TeX unit markup with degree symbols named as deg."""
    text = value
    markers = (r'^\circ{}^2', r'^\circ{}^{2}', r'^\circ^2', r'^\circ^{2}')
    for marker in markers:
        text = text.replace(marker, r'\mathrm{deg}^2')
    return text.replace(r'^\circ{}', r'\mathrm{deg}').replace(
        r'^\circ',
        r'\mathrm{deg}',
    )


def _plain_unit_text(value: str) -> str:
    """Return plain unit text normalized for report display."""
    return (
        value
        .replace('degrees_squared', 'deg²')
        .replace('degree_squared', 'deg²')
        .replace('degrees squared', 'deg²')
        .replace('degree squared', 'deg²')
        .replace('degrees', 'deg')
        .replace('degree', 'deg')
        .replace('deg^2', 'deg²')
        .replace('°²', 'deg²')
        .replace('°', 'deg')
    )


def _descriptor_units(parameter: object, *, context: str) -> str:
    """Return descriptor units without probing missing attributes."""
    display_handler = _safe_attr(parameter, 'display_handler')
    if display_handler is not None:
        if context == 'latex' and display_handler.latex_units is not None:
            return display_handler.latex_units
        if context != 'latex' and display_handler.display_units is not None:
            return display_handler.display_units

    units = _safe_attr(parameter, 'units')
    return '' if units is None else str(units)


def _category_title(category: object) -> str:
    """Return the report title for a category."""
    return _category_code(category) or type(category).__name__


def _category_code(category: object) -> str | None:
    """Return the CIF-like category code for item or collection."""
    identity = getattr(category, '_identity', None)
    category_code = getattr(identity, 'category_code', None)
    if category_code is not None:
        return category_code
    item_type = getattr(category, '_item_type', None)
    return getattr(item_type, '_category_code', None)


def _software_role_context(role: object) -> dict[str, object]:
    """Return one software role context."""
    return {
        'name': _attr_value(role, 'name'),
        'version': _attr_value(role, 'version'),
        'url': _attr_value(role, 'url'),
    }


def _fit_data_context(experiment: object) -> dict[str, object] | None:
    """Return descriptor-driven fit data for one experiment."""
    x_descriptor = _safe_attr(experiment, 'x_descriptor')
    if x_descriptor is None:
        return _single_crystal_fit_data_context(experiment)

    arrays = experiment.fit_data_arrays()
    axes_labels = _fit_data_axes_labels(experiment, x_descriptor)
    bragg_tick_sets = _fit_data_bragg_tick_sets(
        experiment,
        x_axis=x_descriptor.name,
        x_values=arrays['x'],
    )
    return {
        'x': {
            'values': arrays['x'],
            'name': x_descriptor.name,
            'units': x_descriptor.units,
            'display_name': x_descriptor.resolve_display_name('html'),
            'latex_name': x_descriptor.resolve_display_name('latex'),
            'display_units': x_descriptor.resolve_display_units('html'),
            'latex_units': x_descriptor.resolve_display_units('latex'),
        },
        'axes_labels': axes_labels,
        'series': {
            'meas': {
                'values': arrays['meas'],
                'su': arrays['meas_su'],
                'label': 'Measured',
            },
            'calc': _series_context(arrays['calc'], 'Calculated'),
            'diff': _series_context(arrays['diff'], 'Difference'),
            'bkg': _optional_series_context(arrays['bkg'], 'Background'),
        },
        'bragg_tick_sets': bragg_tick_sets,
    }


def _fit_data_axes_labels(experiment: object, x_descriptor: object) -> list[str]:
    """Return Plotly display-axis labels for a report fit figure."""
    experiment_type = _safe_attr(experiment, 'type')
    try:
        sample_form = experiment_type.sample_form.value
        scattering_type = experiment_type.scattering_type.value
        beam_mode = experiment_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[sample_form, scattering_type, beam_mode]
        return list(DEFAULT_AXES_LABELS[sample_form, scattering_type, x_axis])
    except (AttributeError, KeyError):
        units = x_descriptor.resolve_display_units('html')
        display_name = x_descriptor.resolve_display_name('html')
        x_label = f'{display_name} ({units})' if units else display_name
        return [x_label, 'Intensity (arb. units)']


def _fit_data_bragg_tick_sets(
    experiment: object,
    *,
    x_axis: object,
    x_values: object,
) -> object:
    """Return Bragg tick sets for powder Bragg report figures."""
    if not _is_powder_bragg_experiment(experiment):
        return ()

    values = list(x_values)
    if not values:
        return ()

    return Plotter._extract_bragg_tick_sets(
        experiment=experiment,
        expt_name=str(_safe_attr(experiment, 'name') or 'experiment'),
        x_axis=x_axis,
        x_min=float(min(values)),
        x_max=float(max(values)),
    )


def _is_powder_bragg_experiment(experiment: object) -> bool:
    """Return whether an experiment can use powder Bragg plot panels."""
    experiment_type = _safe_attr(experiment, 'type')
    sample_form = _value(_safe_attr(experiment_type, 'sample_form'))
    scattering_type = _value(_safe_attr(experiment_type, 'scattering_type'))
    return sample_form == 'powder' and scattering_type == 'bragg'


def _is_single_crystal_bragg_experiment(experiment: object) -> bool:
    """Return whether an experiment is single-crystal Bragg."""
    experiment_type = _safe_attr(experiment, 'type')
    sample_form = _value(_safe_attr(experiment_type, 'sample_form'))
    scattering_type = _value(_safe_attr(experiment_type, 'scattering_type'))
    return sample_form == 'single crystal' and scattering_type == 'bragg'


def _single_crystal_fit_data_context(
    experiment: object,
) -> dict[str, object] | None:
    """
    Return measured-vs-calculated agreement data for a SC fit.

    Single-crystal experiments have no profile x-axis, so the report
    shows an I_obs-vs-I_calc scatter keyed by ``intensity_calc`` on x.
    The HTML and TeX renderers dispatch on ``x['name']``.
    """
    if not _is_single_crystal_bragg_experiment(experiment):
        return None

    refln = _safe_attr(experiment, 'refln')
    if refln is None:
        return None

    calc = _safe_attr(refln, 'intensity_calc')
    meas = _safe_attr(refln, 'intensity_meas')
    meas_su = _safe_attr(refln, 'intensity_meas_su')
    if calc is None or meas is None or len(calc) == 0:
        return None

    return {
        'x': {
            'values': calc,
            'name': 'intensity_calc',
            'units': '',
            'display_name': 'Icalc',
            'latex_name': r'$I_{\mathrm{calc}}$',
            'display_units': '',
            'latex_units': '',
        },
        'axes_labels': ['Icalc', 'Imeas'],
        'series': {
            'meas': {'values': meas, 'su': meas_su, 'label': 'Measured'},
            'calc': _series_context(calc, 'Calculated'),
            'diff': _series_context(meas - calc, 'Difference'),
            'bkg': None,
        },
        'bragg_tick_sets': (),
    }


def _series_context(values: object, label: str) -> dict[str, object]:
    """Return one required fit-data series."""
    return {'values': values, 'label': label}


def _optional_series_context(
    values: object,
    label: str,
) -> dict[str, object] | None:
    """Return one optional fit-data series."""
    if values is None:
        return None
    return _series_context(values, label)


def _collection_values(collection: object) -> Iterable[object]:
    """Return collection values for project containers."""
    if collection is None:
        return ()
    values = getattr(collection, 'values', None)
    if callable(values):
        return values()
    if isinstance(collection, Iterable) and not isinstance(collection, str):
        return collection
    return (collection,)
