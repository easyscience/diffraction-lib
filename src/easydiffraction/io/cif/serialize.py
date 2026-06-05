# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Serialize and deserialize datablocks to and from CIF text."""

from __future__ import annotations

import textwrap
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

# Minimum string length to check for surrounding quotes
_MIN_QUOTED_LEN = 2

# Number of significant digits kept for CIF uncertainty notation
_CIF_UNCERTAINTY_SIG_DIGITS = 2

# Maximum CIF description length before using semicolon-delimited block
_CIF_DESCRIPTION_WRAP_LEN = 60

_ADP_FAMILY_B = 'B'
_ADP_FAMILY_U = 'U'


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
    # Preserve integers as integers in CIF output
    elif isinstance(value, (int, np.integer)):
        value = str(int(value))
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


def _strip_cif_text_field_delimiters(raw: str) -> str:
    """Return CIF text-field content without delimiter lines."""
    if raw.startswith(';\n') and raw.endswith('\n;'):
        return raw[2:-2].strip()
    return raw


def _parse_bool_cif_value(raw: str) -> bool | str:
    """Parse CIF boolean tokens, returning the raw token if invalid."""
    normalized_value = _strip_optional_quotes(raw).lower()
    if normalized_value == 'true':
        return True
    if normalized_value == 'false':
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
    parameters_hook = getattr(item, '_cif_parameters', None)
    parameters = parameters_hook() if parameters_hook is not None else item.parameters
    lines: list[str] = [param_to_cif(p) for p in parameters]
    return '\n'.join(lines)


def _validate_loop_tags(
    parameters: list[GenericDescriptorBase],
    header_tags: list[str],
) -> None:
    """Log an error if any row tag disagrees with *header_tags*."""
    for col, p in enumerate(parameters):
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
    row_parameters_fn: object,
    header_tags: list[str],
    max_display: int | None,
) -> list[str]:
    """Build formatted rows, optionally truncated."""
    lines: list[str] = []
    if max_display is not None and len(items) > max_display:
        half = max_display // 2
        for item in items[:half]:
            _validate_loop_tags(row_parameters_fn(item), header_tags)
            lines.append(' '.join(row_fn(item)))
        lines.append('...')
        for item in items[-half:]:
            _validate_loop_tags(row_parameters_fn(item), header_tags)
            lines.append(' '.join(row_fn(item)))
    else:
        for item in items:
            _validate_loop_tags(row_parameters_fn(item), header_tags)
            lines.append(' '.join(row_fn(item)))
    return lines


def _emit_rows_without_tag_validation(
    items: list,
    row_fn: object,
    max_display: int | None,
) -> list[str]:
    """Build rows for loops whose tag family is chosen externally."""
    if max_display is not None and len(items) > max_display:
        half = max_display // 2
        return [
            *_rows_without_tag_validation(items[:half], row_fn),
            '...',
            *_rows_without_tag_validation(items[-half:], row_fn),
        ]
    return _rows_without_tag_validation(items, row_fn)


def _rows_without_tag_validation(items: list, row_fn: object) -> list[str]:
    """Return formatted row strings without header-tag validation."""
    return [' '.join(row_fn(item)) for item in items]


def _adp_family_from_type(adp_type: str) -> str:
    """Return the CIF ADP tag family for an atom-site ADP type."""
    from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
        AdpTypeEnum,
    )

    adp_type_enum = AdpTypeEnum(adp_type)
    if adp_type_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}:
        return _ADP_FAMILY_U
    return _ADP_FAMILY_B


def _adp_family_for_atom_site(item: object) -> str:
    """Return the ADP tag family for an atom-site row."""
    return _adp_family_from_type(item.adp_type.value)


def _adp_family_for_atom_site_aniso(collection: object, item: object) -> str:
    """Return the ADP tag family for an atom-site-aniso row."""
    structure = collection._parent
    atom_site = structure.atom_sites[item.label.value]
    return _adp_family_from_type(atom_site.adp_type.value)


def _group_items_by_adp_family(
    items: list,
    family_fn: object,
) -> list[tuple[str, list]]:
    """Group items by B/U ADP tag family in deterministic order."""
    groups = {
        _ADP_FAMILY_B: [],
        _ADP_FAMILY_U: [],
    }
    for item in items:
        groups[family_fn(item)].append(item)
    return [(family, group) for family, group in groups.items() if group]


def _atom_site_tag_for_adp_family(parameter: object, family: str) -> str:
    """Return the atom_site tag for the selected ADP family."""
    if parameter.name == 'adp_iso':
        return f'_atom_site.{family}_iso_or_equiv'
    return parameter._cif_handler.names[0]


def _atom_site_aniso_tag_for_adp_family(parameter: object, family: str) -> str:
    """Return the atom_site_aniso tag for the selected ADP family."""
    if parameter.name.startswith('adp_'):
        suffix = parameter.name.removeprefix('adp_')
        return f'_atom_site_aniso.{family}_{suffix}'
    return parameter._cif_handler.names[0]


def _adp_family_loop_to_cif(
    items: list,
    family: str,
    tag_fn: object,
    max_display: int | None,
) -> str:
    """Render one B-family or U-family ADP loop."""
    first_item = items[0]
    parameters = list(first_item.parameters)
    lines: list[str] = ['loop_']
    lines.extend(tag_fn(parameter, family) for parameter in parameters)

    def _row(item: object) -> list[str]:
        return [format_param_value(parameter) for parameter in item.parameters]

    lines.extend(_emit_rows_without_tag_validation(items, _row, max_display))
    return '\n'.join(lines)


def _adp_collection_to_cif(
    collection: object,
    max_display: int | None,
) -> str | None:
    """
    Render ADP-sensitive structure loops with one tag family per row.
    """
    items = list(collection.values())
    category_code = collection._item_type._category_code
    if category_code == 'atom_site':
        groups = _group_items_by_adp_family(items, _adp_family_for_atom_site)
        loops = [
            _adp_family_loop_to_cif(
                group,
                family,
                _atom_site_tag_for_adp_family,
                max_display,
            )
            for family, group in groups
        ]
        return '\n\n'.join(loops)
    if category_code == 'atom_site_aniso':
        groups = _group_items_by_adp_family(
            items,
            lambda item: _adp_family_for_atom_site_aniso(collection, item),
        )
        loops = [
            _adp_family_loop_to_cif(
                group,
                family,
                _atom_site_aniso_tag_for_adp_family,
                max_display,
            )
            for family, group in groups
        ]
        return '\n\n'.join(loops)
    return None


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
    # Allow collections to conditionally suppress CIF output
    skip = getattr(collection, '_skip_cif_serialization', None)
    if skip is not None and skip():
        return ''

    lines = _scalar_descriptor_lines(collection)

    if not len(collection):
        return '\n'.join(lines)

    adp_cif = _adp_collection_to_cif(collection, max_display)
    if adp_cif is not None:
        return _join_scalar_and_loop_lines(lines, adp_cif)

    loop_cif = _standard_collection_loop_to_cif(collection, max_display)
    return _join_scalar_and_loop_lines(lines, loop_cif)


def _scalar_descriptor_lines(collection: object) -> list[str]:
    """Return scalar descriptor CIF lines for a collection."""
    scalar_descriptors = getattr(collection, 'scalar_descriptors', [])
    return [param_to_cif(p) for p in scalar_descriptors]


def _join_scalar_and_loop_lines(scalar_lines: list[str], loop_cif: str) -> str:
    """Join optional scalar lines with a loop CIF body."""
    lines = list(scalar_lines)
    if lines:
        lines.append('')
    lines.append(loop_cif)
    return '\n'.join(lines)


def _standard_collection_loop_to_cif(
    collection: object,
    max_display: int | None,
) -> str:
    """Render a non-ADP collection loop."""
    loop_parameters_hook = getattr(collection, '_cif_loop_parameters', None)

    def _loop_parameters(item: object) -> list[GenericDescriptorBase]:
        if loop_parameters_hook is not None:
            return list(loop_parameters_hook(item))
        return list(item.parameters)

    # Header — use first item's CIF tag names as the canonical columns
    first_item = next(iter(collection.values()))
    lines = ['loop_']
    header_tags: list[str] = []
    for p in _loop_parameters(first_item):
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
        return [format_param_value(p) for p in _loop_parameters(item)]

    items = list(collection.values())
    lines.extend(_emit_loop_rows(items, _row, _loop_parameters, header_tags, max_display))
    return '\n'.join(lines)


def category_owner_to_cif(
    owner: object,
    max_loop_display: int | None = None,
) -> str:
    """Render a category-owning object without a ``data_`` header."""
    from easydiffraction.core.category import CategoryCollection  # noqa: PLC0415
    from easydiffraction.core.category import CategoryItem  # noqa: PLC0415

    categories_getter = getattr(owner, '_serializable_categories', None)
    if callable(categories_getter):
        categories = categories_getter()
    else:
        categories = [
            value
            for value in vars(owner).values()
            if isinstance(value, (CategoryItem, CategoryCollection))
        ]

    item_parts = [
        category.as_cif
        for category in categories
        if isinstance(category, CategoryItem) and category.as_cif
    ]

    collection_parts = [
        category_collection_to_cif(category, max_display=max_loop_display)
        for category in categories
        if isinstance(category, CategoryCollection)
    ]

    return '\n\n'.join([part for part in item_parts + collection_parts if part])


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
    header = f'data_{datablock._identity.datablock_entry_name}'
    body = category_owner_to_cif(datablock, max_loop_display=max_loop_display)
    if not body:
        return header
    return f'{header}\n\n{body}'


def datablock_collection_to_cif(collection: object) -> str:
    """Render a collection of datablocks by joining their CIF blocks."""
    return '\n\n'.join([block.as_cif for block in collection.values()])


def _format_project_description(description: str) -> str:
    """Format project descriptions as CIF text."""
    normalized_description = ' '.join(description.split())
    if not normalized_description:
        return '?'

    if len(normalized_description) > _CIF_DESCRIPTION_WRAP_LEN:
        wrapped_description = '\n'.join(
            textwrap.wrap(
                normalized_description,
                width=_CIF_DESCRIPTION_WRAP_LEN,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
        return f'\n;\n{wrapped_description}\n;'

    return format_value(normalized_description)


def project_info_to_cif(info: object) -> str:
    """Render ProjectInfo to CIF text (id, title, description)."""
    name = f'{info.name}'

    title = f'{info.title}'
    if ' ' in title:
        title = format_value(info.title)

    description = _format_project_description(info.description)

    created = format_value(info.created.strftime('%d %b %Y %H:%M:%S'))
    last_modified = format_value(info.last_modified.strftime('%d %b %Y %H:%M:%S'))

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
    sections: list[str] = []
    for attr_name in ('info', 'rendering_plot', 'report'):
        section = getattr(project, attr_name, None)
        if section is not None:
            sections.append(_as_cif_text(section))

    publication = getattr(project, 'publication', None)
    if publication is not None:
        sections.append(category_owner_to_cif(publication))

    for attr_name in (
        'rendering_table',
        'rendering_structure',
        'structure_view',
        'structure_style',
        'verbosity',
    ):
        section = getattr(project, attr_name, None)
        if section is not None:
            sections.append(_as_cif_text(section))

    return '\n\n'.join(section for section in sections if section)


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
    return '\n\n'.join([p for p in parts if p])


def experiment_to_cif(experiment: object) -> str:
    """Render an experiment: datablock part plus measured data."""
    return datablock_item_to_cif(experiment)


def analysis_to_cif(analysis: object) -> str:
    """Render analysis metadata, aliases, and constraints to CIF."""
    return category_owner_to_cif(analysis)


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


def _project_block_from_cif_text(cif_text: str) -> gemmi.cif.Block:
    """Parse project CIF text."""
    import gemmi  # noqa: PLC0415

    return gemmi.cif.read_string(_wrap_in_data_block(cif_text, 'project')).sole_block()


def _populate_project_info_from_block(
    info: object,
    block: gemmi.cif.Block,
) -> None:
    """Populate ProjectInfo fields from a parsed CIF block."""
    from_cif = getattr(info, 'from_cif', None)
    if callable(from_cif):
        from_cif(block)
        return

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

    Reads the core project metadata fields from CIF text.

    Parameters
    ----------
    info : object
        The ``ProjectInfo`` instance to populate.
    cif_text : str
        CIF text content of ``project.cif``.
    """
    block = _project_block_from_cif_text(cif_text)

    _populate_project_info_from_block(info, block)


def project_config_from_cif(project: object, cif_text: str) -> None:
    """
    Populate project-level configuration from ``project.cif`` text.
    """
    block = _project_block_from_cif_text(cif_text)

    _populate_project_info_from_block(project.info, block)

    rendering_plot = getattr(project, 'rendering_plot', None)
    if rendering_plot is not None:
        rendering_plot.from_cif(block)

    report = getattr(project, 'report', None)
    if report is not None:
        # Missing _report.* items intentionally keep legacy defaults.
        report.from_cif(block)

    publication = getattr(project, 'publication', None)
    if publication is not None:
        publication.from_cif(block)

    rendering_table = getattr(project, 'rendering_table', None)
    if rendering_table is not None:
        rendering_table.from_cif(block)

    verbosity = getattr(project, 'verbosity', None)
    if verbosity is not None:
        verbosity.from_cif(block)

    rendering_structure = getattr(project, 'rendering_structure', None)
    if rendering_structure is not None:
        rendering_structure.from_cif(block)

    structure_view = getattr(project, 'structure_view', None)
    if structure_view is not None:
        structure_view.from_cif(block)

    structure_style = getattr(project, 'structure_style', None)
    if structure_style is not None:
        structure_style.from_cif(block)


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

    _raise_for_legacy_analysis_tags(block)
    analysis._set_fitting_mode_type(_analysis_mode_from_cif_block(block))
    analysis._set_minimizer_type(_analysis_minimizer_from_cif_block(block))
    analysis.minimizer.from_cif(block)
    analysis.software.from_cif(block)
    _restore_mode_specific_analysis_sections(analysis, block)

    # Restore aliases (loop)
    analysis.aliases.from_cif(block)

    # Restore constraints (loop)
    analysis.constraints.from_cif(block)
    if analysis.constraints._items:
        analysis.constraints.enable()

    if _has_fit_parameter_state_sections(block):
        _restore_fit_parameter_state(analysis, block)
    if _has_persisted_fit_state_sections(block):
        _restore_persisted_fit_state(analysis, block)


def _has_fit_parameter_state_sections(block: object) -> bool:
    """Return True when persisted fit-parameter rows are present."""
    return _has_cif_loop(block, '_fit_parameter.param_unique_name')


def _has_persisted_fit_state_sections(block: object) -> bool:
    """Return True when a fit-result projection is present."""
    return _has_cif_value(block, '_fit_result.result_kind')


def _restore_fit_parameter_state(analysis: object, block: object) -> None:
    """Restore fit-parameter rows independently of fit results."""
    analysis.fit_parameters.from_cif(block)


def _restore_fit_result_state(analysis: object, block: object) -> None:
    """Restore categories that describe the latest fit result."""
    analysis.fit_result.from_cif(block)
    analysis.fit_parameter_correlations.from_cif(block)


def _restore_persisted_fit_state(analysis: object, block: object) -> None:
    """
    Restore persisted fit-state categories after analysis configuration.
    """
    from easydiffraction.analysis.enums import FitResultKindEnum  # noqa: PLC0415

    analysis._set_has_persisted_fit_state(value=True)
    _restore_fit_result_state(analysis, block)

    result_kind_value = analysis.fit_result.result_kind.value
    try:
        FitResultKindEnum(result_kind_value)
    except ValueError:
        log.warning(
            'Unsupported _fit_result.result_kind in analysis CIF: '
            f'{result_kind_value!r}. Skipping kind-specific fit-state categories.',
        )


_MINIMIZER_OUTPUT_LEGACY_TAGS = (
    '_minimizer.objective_name',
    '_minimizer.objective_value',
    '_minimizer.n_data_points',
    '_minimizer.n_parameters',
    '_minimizer.n_free_parameters',
    '_minimizer.degrees_of_freedom',
    '_minimizer.covariance_available',
    '_minimizer.correlation_available',
    '_minimizer.runtime_seconds',
    '_minimizer.iterations_performed',
    '_minimizer.exit_reason',
    '_minimizer.point_estimate_name',
    '_minimizer.sampler_completed',
    '_minimizer.credible_interval_inner',
    '_minimizer.credible_interval_outer',
    '_minimizer.acceptance_rate_mean',
    '_minimizer.gelman_rubin_max',
    '_minimizer.effective_sample_size_min',
    '_minimizer.best_log_posterior',
)


def _collect_legacy_analysis_tags(block: object) -> list[str]:
    """Return deprecated analysis CIF tags present in a block."""
    legacy_tags: list[str] = []
    if _has_cif_loop(block, '_joint_fit_experiment.id'):
        legacy_tags.append('_joint_fit_experiment.id')
    if _has_cif_loop(block, '_joint_fit_experiment.weight'):
        legacy_tags.append('_joint_fit_experiment.weight')
    legacy_tags.extend(tag for tag in _MINIMIZER_OUTPUT_LEGACY_TAGS if _has_cif_value(block, tag))
    return legacy_tags


def _raise_for_legacy_analysis_tags(block: object) -> None:
    """Raise when deprecated analysis CIF tags are present."""
    legacy_tags = _collect_legacy_analysis_tags(block)
    if not legacy_tags:
        return

    msg = (
        'Legacy analysis CIF tags are no longer supported: '
        f'{legacy_tags}. Use _minimizer.type, _fitting_mode.type, '
        '_minimizer.* for settings, _fit_result.* for fit outputs, '
        '_joint_fit.experiment_id, and _joint_fit.weight.'
    )
    raise ValueError(msg)


def _analysis_mode_from_cif_block(block: object) -> str:
    """Return the fitting mode stored in an analysis CIF block."""
    read_cif_string = _make_cif_string_reader(block)
    mode_value = read_cif_string('_fitting_mode.type')
    if mode_value is not None:
        return mode_value

    from easydiffraction.analysis.enums import FitModeEnum  # noqa: PLC0415

    return FitModeEnum.default().value


def _analysis_minimizer_from_cif_block(block: object) -> str:
    """Return the minimizer type stored in an analysis CIF block."""
    read_cif_string = _make_cif_string_reader(block)
    minimizer_value = read_cif_string('_minimizer.type')
    if minimizer_value is not None:
        return minimizer_value

    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum  # noqa: PLC0415

    return MinimizerTypeEnum.default().value


def _has_joint_fit_rows(block: object) -> bool:
    """Return True when joint-fit rows are present."""
    return _has_cif_loop(block, '_joint_fit.experiment_id') or _has_cif_loop(
        block,
        '_joint_fit.weight',
    )


def _has_sequential_fit_settings(block: object) -> bool:
    """Return True when sequential-fit scalar settings are present."""
    return any(
        _has_cif_value(block, tag)
        for tag in (
            '_sequential_fit.data_dir',
            '_sequential_fit.file_pattern',
            '_sequential_fit.max_workers',
            '_sequential_fit.chunk_size',
            '_sequential_fit.reverse',
        )
    )


def _warn_inactive_analysis_sections(
    *,
    has_joint_rows: bool,
    has_sequential_settings: bool,
    has_sequential_extract_rows: bool,
) -> None:
    """Warn when inactive analysis sections are skipped."""
    skipped_sections: list[str] = []
    if has_joint_rows:
        skipped_sections.append('joint_fit')
    if has_sequential_settings or has_sequential_extract_rows:
        skipped_sections.append('sequential_fit')
    log.warning(
        'Skipping inactive analysis CIF sections while fitting_mode is single: '
        f'{skipped_sections}.'
    )


def _restore_mode_specific_analysis_sections(analysis: object, block: object) -> None:
    """Restore only the active mode-specific analysis sections."""
    has_joint_rows = _has_joint_fit_rows(block)
    has_sequential_settings = _has_sequential_fit_settings(block)
    has_sequential_extract_rows = _has_cif_loop(block, '_sequential_fit_extract.id')

    if analysis.fitting_mode.type == 'joint':
        if has_joint_rows:
            analysis.joint_fit.from_cif(block)
        return

    if analysis.fitting_mode.type == 'sequential':
        if has_sequential_settings:
            analysis.sequential_fit.from_cif(block)
        if has_sequential_extract_rows:
            analysis.sequential_fit_extract.from_cif(block)
        return

    if has_joint_rows or has_sequential_settings or has_sequential_extract_rows:
        _warn_inactive_analysis_sections(
            has_joint_rows=has_joint_rows,
            has_sequential_settings=has_sequential_settings,
            has_sequential_extract_rows=has_sequential_extract_rows,
        )


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
        raw = _strip_cif_text_field_delimiters(raw)
        return _strip_optional_quotes(raw)

    return _read


def _has_cif_value(block: gemmi.cif.Block, tag: str) -> bool:
    """Return True when a scalar CIF tag is present in the block."""
    return block.find_value(tag) is not None


def _has_cif_loop(block: gemmi.cif.Block, tag: str) -> bool:
    """Return True when a CIF loop column is present in the block."""
    loop_ref = block.find_loop(tag)
    if loop_ref is None:
        return False
    loop = loop_ref.get_loop() if hasattr(loop_ref, 'get_loop') else loop_ref
    return loop is not None


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

    # If no values found, use the descriptor default when available.
    if not found_values:
        _set_param_to_default_from_cif(self, raw=None)
        return

    # If found, pick the one at the given index.
    raw = found_values[idx]
    _set_param_from_raw_cif_value(self, raw)


def _set_param_to_default_from_cif(
    param: GenericDescriptorBase,
    *,
    raw: str | None,
) -> None:
    """
    Resolve missing or unknown CIF values to descriptor defaults.

    Parameters
    ----------
    param : GenericDescriptorBase
        Descriptor being populated from CIF.
    raw : str | None
        Raw CIF token, or ``None`` when no tag was present.
    """
    value_spec = getattr(param, '_value_spec', None)
    if value_spec is not None and (value_spec.has_default or value_spec.allow_none):
        param.value = value_spec.default_value()
        return

    detail = 'missing tag' if raw is None else f'value {raw!r}'
    log.error(
        f"Cannot load required CIF field '{param.unique_name}': {detail}.",
        exc_type=ValueError,
    )


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
    raw = _strip_cif_text_field_delimiters(raw)

    # CIF unknown / inapplicable markers → descriptor default
    if raw in {'?', '.'}:
        _set_param_to_default_from_cif(param, raw=raw)
        return

    if param._value_type == DataTypes.INTEGER:
        numeric_value = str_to_ufloat(raw).n
        integer_value = round(numeric_value)
        if not np.isclose(numeric_value, integer_value):
            log.warning(
                f'Ignoring non-integer CIF value {raw!r} for integer field {param.unique_name}.'
            )
            return
        param.value = integer_value

    elif param._value_type == DataTypes.NUMERIC:
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

    for param in self.scalar_descriptors:
        param.from_cif(block)

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
            tag_found = False
            for cif_name in param._cif_handler.names:
                if cif_name in loop.tags:
                    col_idx = loop.tags.index(cif_name)
                    # TODO: The following is duplication of
                    #  param_from_cif
                    _set_param_from_raw_cif_value(param, array[row_idx][col_idx])
                    tag_found = True
                    break
            if not tag_found:
                _set_param_to_default_from_cif(param, raw=None)

    after_from_cif = getattr(self, '_after_from_cif', None)
    if callable(after_from_cif):
        after_from_cif()

    self._rebuild_index()
