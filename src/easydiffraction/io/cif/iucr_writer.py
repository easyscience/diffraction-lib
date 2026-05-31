# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""IUCr journal-submission CIF writer."""

from __future__ import annotations

import math
import pathlib
import re
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

from easydiffraction.io.cif.iucr_transformers import IucrCategoryTransformer
from easydiffraction.io.cif.iucr_transformers import IucrItem
from easydiffraction.io.cif.serialize import format_param_value
from easydiffraction.io.cif.serialize import format_value
from easydiffraction.utils.utils import package_version

_BLOCK_SEPARATOR = '#====================================================='
_TEXT_WRAP_WIDTH = 80
_ITEM_WIDTH = 38

_JOURNAL_ITEMS = (
    ('_journal.name_full', 'name_full'),
    ('_journal.year', 'year'),
    ('_journal.volume', 'volume'),
    ('_journal.issue', 'issue'),
    ('_journal.page_first', 'page_first'),
    ('_journal.page_last', 'page_last'),
    ('_journal.paper_category', 'paper_category'),
    ('_journal.paper_DOI', 'paper_doi'),
    ('_journal.coden_ASTM', 'coden_astm'),
    ('_journal.suppl_publ_number', 'suppl_publ_number'),
)

_JOURNAL_DATE_ITEMS = (
    ('_journal_date.accepted', 'accepted'),
    ('_journal_date.from_coeditor', 'from_coeditor'),
    ('_journal_date.printers_final', 'printers_final'),
)

_JOURNAL_COEDITOR_ITEMS = (
    ('_journal_coeditor.code', 'code'),
    ('_journal_coeditor.name', 'name'),
    ('_journal_coeditor.notes', 'notes'),
)

_PUBL_CONTACT_AUTHOR_ITEMS = (
    ('_publ_contact_author.name', 'name'),
    ('_publ_contact_author.address', 'address'),
    ('_publ_contact_author.email', 'email'),
    ('_publ_contact_author.phone', 'phone'),
    ('_publ_contact_author.id_ORCID', 'id_orcid'),
    ('_publ_contact_author.id_IUCr', 'id_iucr'),
)

_PUBL_AUTHOR_ITEMS = (
    ('_publ_author.name', 'name'),
    ('_publ_author.address', 'address'),
    ('_publ_author.footnote', 'footnote'),
    ('_publ_author.id_ORCID', 'id_orcid'),
    ('_publ_author.id_IUCr', 'id_iucr'),
)
_PUBL_AUTHOR_TAGS = tuple(tag for tag, _ in _PUBL_AUTHOR_ITEMS)

_PUBL_BODY_ITEMS = (
    ('_publ_body.title', 'title'),
    ('_publ_body.contents', 'contents'),
)

_PACKAGE_BY_ENGINE = {
    'cryspy': 'cryspy',
    'crysfml': 'crysfml',
    'pdffit': 'diffpy.pdffit2',
    'lmfit': 'lmfit',
    'dfols': 'dfols',
    'bumps': 'bumps',
    'emcee': 'emcee',
}


def write_iucr_cif(
    project: object,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Write the project as an IUCr journal-submission CIF.

    Parameters
    ----------
    project : object
        Project instance to export.
    path : str | pathlib.Path | None, default=None
        Target CIF path. When omitted, the report is written to
        ``<project.info.path>/reports/<project.name>.cif``.

    Returns
    -------
    pathlib.Path
        Path of the written report CIF.
    """
    output_path = iucr_report_path(project, path)
    content = _render_iucr_cif(project)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding='utf-8')
    return output_path


def iucr_report_path(
    project: object,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Return the target IUCr report path for a project.

    Parameters
    ----------
    project : object
        Project instance.
    path : str | pathlib.Path | None, default=None
        Explicit report path.

    Returns
    -------
    pathlib.Path
        Resolved report path.
    """
    return _report_path(project, path)


def _render_iucr_cif(project: object) -> str:
    """Render all IUCr CIF blocks for *project*."""
    blocks = [_write_global_block(project)]
    blocks.extend(_write_sc_blocks(project))
    blocks.extend(_write_rietveld_blocks(project))
    return f'\n\n{_BLOCK_SEPARATOR}\n'.join(blocks) + '\n'


def _write_global_block(project: object) -> str:
    """Render the leading ``data_global`` metadata block."""
    lines = ['data_global']
    _write_audit_section(lines)
    _write_computing_section(lines, project)
    _write_publication_sections(lines, project)
    _write_formula_section(lines, project)
    return '\n'.join(lines)


def _write_audit_section(lines: list[str]) -> None:
    """Append audit metadata."""
    method = _software_label('EasyDiffraction', package_name='easydiffraction')
    _section(lines, 'Audit')
    _write_item(lines, '_audit.creation_method', method)
    _write_item(lines, '_audit.creation_date', _iso_creation_datetime())


def _write_computing_section(lines: list[str], project: object) -> None:
    """Append software-stack metadata."""
    framework = _software_role_label(project, 'framework')
    calculator = _software_role_label(project, 'calculator')
    minimizer = _software_role_label(project, 'minimizer')
    refinement = _structure_refinement_label(framework, calculator, minimizer)

    _section(lines, 'Computing')
    _write_item(lines, '_computing.structure_refinement', refinement)

    _section(lines, 'EasyDiffraction software')
    _write_item(lines, '_easydiffraction_software.framework', framework)
    _write_item(lines, '_easydiffraction_software.calculator', calculator)
    _write_item(lines, '_easydiffraction_software.minimizer', minimizer)
    fit_datetime = _software_fit_datetime(project)
    if fit_datetime is not None:
        _write_item(lines, '_easydiffraction_software.fit_datetime', fit_datetime)


def _write_publication_sections(lines: list[str], project: object) -> None:
    """
    Append publication metadata from the project publication owner.
    """
    publication = getattr(project, 'publication', None)
    _write_publication_item_section(
        lines,
        'Journal',
        getattr(publication, 'journal', None),
        _JOURNAL_ITEMS,
    )
    _write_publication_item_section(
        lines,
        'Journal dates',
        getattr(publication, 'journal_date', None),
        _JOURNAL_DATE_ITEMS,
    )
    _write_publication_item_section(
        lines,
        'Journal coeditor',
        getattr(publication, 'journal_coeditor', None),
        _JOURNAL_COEDITOR_ITEMS,
    )
    _write_publication_item_section(
        lines,
        'Publication contact author',
        getattr(publication, 'contact_author', None),
        _PUBL_CONTACT_AUTHOR_ITEMS,
    )

    _section(lines, 'Publication authors')
    _write_loop(lines, _PUBL_AUTHOR_TAGS, _publication_author_rows(publication))

    _write_publication_body_section(
        lines,
        getattr(publication, 'body', None),
    )


def _write_formula_section(lines: list[str], project: object) -> None:
    """Append chemical-formula summary metadata."""
    formula = _chemical_formula_values(project)
    _write_chemical_formula_section(lines, formula)


def _write_chemical_formula_section(
    lines: list[str],
    formula: _FormulaValues,
) -> None:
    """Append one chemical-formula section."""
    _section(lines, 'Chemical formula')
    _write_item(lines, '_chemical_formula.sum', formula.sum_formula)
    _write_item(lines, '_chemical_formula.moiety', formula.moiety)
    _write_item(lines, '_chemical_formula.weight', formula.weight)
    _write_item(lines, '_chemical_formula.IUPAC', formula.iupac)


def _write_sc_blocks(project: object) -> list[str]:
    """Render single-crystal structure/experiment blocks."""
    blocks: list[str] = []
    for experiment in _single_crystal_experiments(project):
        structure = _linked_structure(project, experiment)
        blocks.append(_write_sc_block(project, structure, experiment))
    return blocks


def _write_sc_block(
    project: object,
    structure: object,
    experiment: object,
) -> str:
    """Render one single-crystal data block."""
    block_name = _block_name(getattr(structure, 'name', None) or 'I')
    lines = [f'data_{block_name}']
    _write_chemical_formula_section(lines, _structure_formula_values(structure))
    _write_cell_section(lines, structure)
    _write_space_group_section(lines, structure)
    _write_symmetry_operations_section(lines, structure)
    _write_diffrn_section(lines, experiment)
    _write_wavelength_section(lines, experiment)
    _write_atom_site_sections(lines, structure)
    _write_atom_site_aniso_sections(lines, structure)
    _write_sc_refinement_section(lines, project, experiment)
    _write_reflns_section(lines, project, experiment)
    _write_sc_refln_loop(lines, experiment)
    _write_sc_project_extensions(lines, experiment)
    return '\n'.join(lines)


def _write_cell_section(lines: list[str], structure: object) -> None:
    """Append unit-cell parameters."""
    cell = getattr(structure, 'cell', None)
    _section(lines, 'Cell')
    for tag, attr_name in (
        ('_cell.length_a', 'length_a'),
        ('_cell.length_b', 'length_b'),
        ('_cell.length_c', 'length_c'),
        ('_cell.angle_alpha', 'angle_alpha'),
        ('_cell.angle_beta', 'angle_beta'),
        ('_cell.angle_gamma', 'angle_gamma'),
    ):
        _write_item(lines, tag, _attribute_value(cell, attr_name))


def _write_space_group_section(lines: list[str], structure: object) -> None:
    """Append space-group metadata."""
    space_group = getattr(structure, 'space_group', None)
    _section(lines, 'Space group')
    _write_item(
        lines,
        '_space_group.name_H-M_alt',
        _attribute_value(space_group, 'name_h_m'),
    )
    _write_item(
        lines,
        '_space_group.IT_coordinate_system_code',
        _attribute_value(space_group, 'it_coordinate_system_code'),
    )
    _write_item(lines, '_space_group.crystal_system', '?')


def _write_symmetry_operations_section(lines: list[str], structure: object) -> None:
    """Append symmetry operations."""
    transformer = IucrCategoryTransformer.create('symmetry_operations')
    loop = transformer.loop(structure)
    _section(lines, 'Symmetry operations')
    _write_loop(lines, loop.tags, loop.rows)


def _write_diffrn_section(lines: list[str], experiment: object) -> None:
    """Append diffraction metadata."""
    diffrn = getattr(experiment, 'diffrn', None)
    expt_type = getattr(experiment, 'type', None)
    _section(lines, 'Diffraction')
    _write_item(
        lines,
        '_diffrn.ambient_temperature',
        _attribute_value(diffrn, 'ambient_temperature'),
    )
    _write_item(
        lines,
        '_diffrn.ambient_pressure',
        _attribute_value(diffrn, 'ambient_pressure'),
    )
    _write_item(
        lines,
        '_diffrn_radiation.probe',
        _attribute_value(expt_type, 'radiation_probe'),
    )


def _write_wavelength_section(lines: list[str], experiment: object) -> None:
    """Append wavelength metadata when available."""
    wavelength = _attribute_value(
        getattr(experiment, 'instrument', None),
        'setup_wavelength',
    )
    if wavelength is None:
        return

    transformer = IucrCategoryTransformer.create('wavelength')
    items = transformer.items(experiment)
    if items is not None:
        _section(lines, 'Wavelength')
        for item in items:
            _write_item(lines, item.tag, item.value)
        return

    loop = transformer.loop(experiment)
    if loop is None:
        return

    _section(lines, 'Wavelength')
    _write_loop(lines, loop.tags, loop.rows)


def _write_atom_site_sections(lines: list[str], structure: object) -> None:
    """Append atom-site loops grouped by ADP convention."""
    atom_sites = list(_collection_values(getattr(structure, 'atom_sites', None)))
    for family in ('B', 'U'):
        rows = [
            _atom_site_row(atom_site)
            for atom_site in atom_sites
            if _adp_family(atom_site) == family
        ]
        if not rows:
            continue
        _section(lines, f'Atom sites ({family})')
        _write_loop(lines, _atom_site_tags(family), rows)


def _write_atom_site_aniso_sections(lines: list[str], structure: object) -> None:
    """Append anisotropic ADP loops grouped by ADP convention."""
    aniso_sites = list(_collection_values(getattr(structure, 'atom_site_aniso', None)))
    atom_site_by_label = {
        str(_attribute_value(atom_site, 'label')): atom_site
        for atom_site in _collection_values(getattr(structure, 'atom_sites', None))
    }
    for family in ('B', 'U'):
        rows = [
            _atom_site_aniso_row(aniso_site)
            for aniso_site in aniso_sites
            if _adp_family(_atom_site_for_aniso(atom_site_by_label, aniso_site)) == family
        ]
        if not rows:
            continue
        _section(lines, f'Anisotropic ADP ({family})')
        _write_loop(lines, _atom_site_aniso_tags(family), rows)


def _write_sc_refinement_section(
    lines: list[str],
    project: object,
    experiment: object,
) -> None:
    """Append single-crystal refinement statistics."""
    fit_result = _fit_result(project)
    _section(lines, 'Refinement')
    for tag, attr_name in (
        ('_refine_ls.R_factor_all', 'r_factor_all'),
        ('_refine_ls.wR_factor_all', 'wr_factor_all'),
        ('_refine_ls.R_factor_gt', 'r_factor_gt'),
        ('_refine_ls.wR_factor_gt', 'wr_factor_gt'),
        ('_refine_ls.number_parameters', 'n_parameters'),
        ('_refine_ls.number_restraints', 'number_restraints'),
        ('_refine_ls.number_constraints', 'number_constraints'),
    ):
        _write_item(lines, tag, _attribute_value(fit_result, attr_name))
    for item in _extinction_items(experiment, extension=False):
        _write_item(lines, item.tag, item.value)


def _write_reflns_section(
    lines: list[str],
    project: object,
    experiment: object,
) -> None:
    """Append reflection-set aggregate statistics."""
    fit_result = _fit_result(project)
    reflns = list(_collection_values(getattr(experiment, 'refln', None)))
    _section(lines, 'Reflection summary')
    _write_item(
        lines,
        '_reflns.number_total',
        _attribute_value(fit_result, 'number_reflns_total') or len(reflns),
    )
    _write_item(
        lines,
        '_reflns.number_gt',
        _attribute_value(fit_result, 'number_reflns_gt'),
    )
    _write_item(
        lines,
        '_reflns.threshold_expression',
        _attribute_value(fit_result, 'threshold_expression'),
    )


def _write_sc_refln_loop(lines: list[str], experiment: object) -> None:
    """Append the single-crystal reflection loop."""
    rows = [
        _sc_refln_row(refln) for refln in _collection_values(getattr(experiment, 'refln', None))
    ]
    if not rows:
        return

    _section(lines, 'Reflections')
    _write_loop(
        lines,
        (
            '_refln.index_h',
            '_refln.index_k',
            '_refln.index_l',
            '_refln.F_squared_meas',
            '_refln.F_squared_calc',
            '_refln.F_squared_meas_su',
            '_refln.include_status',
        ),
        rows,
    )


def _write_sc_project_extensions(lines: list[str], experiment: object) -> None:
    """
    Append EasyDiffraction extension values for a single-crystal block.
    """
    extension_rows = [
        *_sc_extension_items(experiment),
        *[(item.tag, item.value) for item in _extinction_items(experiment, extension=True)],
    ]
    if not extension_rows:
        return

    _section(lines, 'EasyDiffraction project extensions')
    for tag, value in extension_rows:
        _write_item(lines, tag, value)


def _write_rietveld_blocks(project: object) -> list[str]:
    """Render powder Rietveld overall, phase, and pattern blocks."""
    experiments = _powder_rietveld_experiments(project)
    if not experiments:
        return []

    phases = _powder_phases(project, experiments)
    patterns = _powder_patterns(project, experiments)
    return [
        _write_rietveld_overall_block(project, phases, patterns),
        *[_write_powder_phase_block(phase) for phase in phases],
        *[_write_powder_pattern_block(project, pattern, phases) for pattern in patterns],
    ]


def _write_rietveld_overall_block(
    project: object,
    phases: list[_PowderPhase],
    patterns: list[_PowderPattern],
) -> str:
    """Render the powder Rietveld overall block."""
    lines = [f'data_{_block_name(project.name)}_overall']
    fit_result = _fit_result(project)

    _section(lines, 'Rietveld overall')
    _write_item(lines, '_pd_calc.method', 'Rietveld Refinement')
    _write_item(
        lines,
        '_pd_block_id',
        _pipe_ids([phase.block_name for phase in phases]),
    )
    _write_item(
        lines,
        '_pd_block_diffractogram_id',
        _pipe_ids([pattern.block_name for pattern in patterns]),
    )

    _section(lines, 'Powder refinement')
    for tag, attr_name in (
        ('_pd_proc_ls.prof_R_factor', 'prof_r_factor'),
        ('_pd_proc_ls.prof_wR_factor', 'prof_wr_factor'),
        ('_pd_proc_ls.prof_wR_expected', 'prof_wr_expected'),
        ('_pd_proc_ls.profile_function', 'profile_function'),
        ('_pd_proc_ls.background_function', 'background_function'),
        ('_refine_ls.number_parameters', 'n_parameters'),
        ('_refine_ls.number_restraints', 'number_restraints'),
        ('_refine_ls.number_constraints', 'number_constraints'),
    ):
        _write_item(lines, tag, _attribute_value(fit_result, attr_name))

    return '\n'.join(lines)


def _write_powder_phase_block(phase: _PowderPhase) -> str:
    """Render one powder phase block."""
    lines = [f'data_{phase.block_name}']
    _write_chemical_formula_section(lines, _structure_formula_values(phase.structure))
    _write_cell_section(lines, phase.structure)
    _write_space_group_section(lines, phase.structure)
    _write_symmetry_operations_section(lines, phase.structure)
    _write_atom_site_sections(lines, phase.structure)
    _write_atom_site_aniso_sections(lines, phase.structure)
    _write_powder_phase_reference_section(lines, phase)
    return '\n'.join(lines)


def _write_powder_phase_reference_section(
    lines: list[str],
    phase: _PowderPhase,
) -> None:
    """Append phase-block cross-reference values."""
    _section(lines, 'Powder phase')
    _write_item(lines, '_pd_phase_block.id', phase.block_name)
    _write_item(
        lines,
        '_pd_phase_block.scale',
        _attribute_value(phase.linked_phase, 'scale'),
    )


def _write_powder_pattern_block(
    project: object,
    pattern: _PowderPattern,
    phases: list[_PowderPhase],
) -> str:
    """Render one powder pattern block."""
    experiment = pattern.experiment
    lines = [f'data_{pattern.block_name}']
    _write_powder_pattern_reference_section(lines, project, pattern, phases)
    _write_powder_measurement_section(lines, experiment)
    _write_diffrn_section(lines, experiment)
    _write_wavelength_section(lines, experiment)
    _write_powder_proc_section(lines, experiment)
    _write_powder_pattern_refinement_section(lines, project)
    _write_powder_profile_loop(lines, experiment)
    _write_powder_refln_loop(lines, experiment)
    _write_powder_project_extensions(lines, experiment)
    return '\n'.join(lines)


def _write_powder_pattern_reference_section(
    lines: list[str],
    project: object,
    pattern: _PowderPattern,
    phases: list[_PowderPhase],
) -> None:
    """Append powder pattern cross-reference values."""
    phase_ids = _phase_block_names_for_experiment(
        project,
        pattern.experiment,
        phases,
    )
    _section(lines, 'Powder pattern')
    _write_item(lines, '_pd_block_id', _pipe_ids(phase_ids))
    _write_item(lines, '_pd_block_diffractogram_id', pattern.block_name)


def _write_powder_measurement_section(
    lines: list[str],
    experiment: object,
) -> None:
    """Append powder measurement metadata."""
    data_items = list(_collection_values(getattr(experiment, 'data', None)))
    expt_type = getattr(experiment, 'type', None)
    _section(lines, 'Powder measurement')
    _write_item(lines, '_pd_meas.scan_method', _attribute_value(expt_type, 'beam_mode'))
    _write_item(lines, '_pd_meas.number_of_points', len(data_items))
    _write_item(lines, '_pd_meas.info_author_name', '?')
    _write_item(lines, '_pd_meas.info_author_email', '?')
    _write_item(lines, '_pd_meas.info_author_phone', '?')


def _write_powder_proc_section(lines: list[str], experiment: object) -> None:
    """Append powder processing metadata."""
    _section(lines, 'Powder processing')
    _write_item(lines, '_pd_proc.info_data_reduction', '?')
    _write_item(lines, '_pd_proc.info_datetime', _iso_creation_datetime())
    transformer = IucrCategoryTransformer.create('excluded_regions')
    for item in transformer.items(experiment):
        _write_item(lines, item.tag, item.value)

    if _is_tof_experiment(experiment):
        _write_tof_calibration_loop(lines, experiment)


def _write_powder_pattern_refinement_section(
    lines: list[str],
    project: object,
) -> None:
    """Append powder pattern refinement statistics."""
    fit_result = _fit_result(project)
    _section(lines, 'Powder pattern refinement')
    for tag, attr_name in (
        ('_pd_proc_ls.prof_R_factor', 'prof_r_factor'),
        ('_pd_proc_ls.prof_wR_factor', 'prof_wr_factor'),
        ('_pd_proc_ls.prof_wR_expected', 'prof_wr_expected'),
    ):
        _write_item(lines, tag, _attribute_value(fit_result, attr_name))


def _write_powder_profile_loop(lines: list[str], experiment: object) -> None:
    """Append powder profile data."""
    rows = [
        _powder_profile_row(experiment, data_point)
        for data_point in _collection_values(getattr(experiment, 'data', None))
    ]
    if not rows:
        return

    _section(lines, 'Profile data')
    _write_loop(
        lines,
        (
            _powder_x_tag(experiment),
            '_pd_meas.intensity_total',
            '_pd_calc.intensity_total',
            '_pd_proc.intensity_bkg_calc',
            '_pd_proc_ls.weight',
        ),
        rows,
    )


def _write_powder_refln_loop(lines: list[str], experiment: object) -> None:
    """Append powder reflection data."""
    rows = [
        _powder_refln_row(refln)
        for refln in _collection_values(getattr(experiment, 'refln', None))
    ]
    if not rows:
        return

    _section(lines, 'Powder reflections')
    _write_loop(
        lines,
        (
            '_refln.index_h',
            '_refln.index_k',
            '_refln.index_l',
            '_refln.F_squared_meas',
            '_refln.F_squared_calc',
            '_pd_refln.phase_id',
            '_refln.d_spacing',
        ),
        rows,
    )


def _write_powder_project_extensions(lines: list[str], experiment: object) -> None:
    """Append powder EasyDiffraction extension values."""
    extension_rows = _powder_extension_items(experiment)
    if not extension_rows:
        return

    _section(lines, 'EasyDiffraction project extensions')
    for tag, value in extension_rows:
        _write_item(lines, tag, value)


def _write_tof_calibration_loop(lines: list[str], experiment: object) -> None:
    """Append TOF calibration rows for a powder pattern."""
    transformer = IucrCategoryTransformer.create('tof_calibration')
    loop = transformer.loop(experiment)
    if loop is None:
        return

    _section(lines, 'TOF calibration')
    _write_loop(lines, loop.tags, loop.rows)


def _write_publication_item_section(
    lines: list[str],
    title: str,
    category: object,
    items: Iterable[tuple[str, str]],
) -> None:
    """Append one scalar publication metadata section."""
    _section(lines, title)
    for tag, attr_name in items:
        _write_item(lines, tag, _attribute_value(category, attr_name))


def _write_publication_body_section(lines: list[str], body: object) -> None:
    """Append publication body metadata."""
    _section(lines, 'Publication body')
    for tag, attr_name in _PUBL_BODY_ITEMS:
        _write_item(lines, tag, _publication_body_value(body, attr_name))


def _publication_body_value(body: object, attr_name: str) -> object:
    """Return one publication-body value."""
    if attr_name != 'contents':
        return _attribute_value(body, attr_name)

    return _publication_body_contents(body)


def _publication_body_contents(body: object) -> str | None:
    """Return IUCr publication body contents from discrete fields."""
    if body is None:
        return None

    sections = []
    for attr_name in ('synopsis', 'abstract'):
        value = _attribute_value(body, attr_name)
        if value not in {None, ''}:
            sections.append(str(value))

    keywords = getattr(body, 'keywords', [])
    if keywords:
        sections.append(f'Keywords: {", ".join(keywords)}')

    if not sections:
        return None
    return '\n\n'.join(sections)


def _publication_author_rows(publication: object) -> list[tuple[object, ...]]:
    """Return publication author rows or one empty placeholder row."""
    authors = getattr(publication, 'authors', None)
    rows = [
        tuple(_attribute_value(author, attr_name) for _, attr_name in _PUBL_AUTHOR_ITEMS)
        for author in _collection_values(authors)
    ]
    if rows:
        return rows
    return [tuple(None for _ in _PUBL_AUTHOR_ITEMS)]


def _write_loop(
    lines: list[str],
    tags: Iterable[str],
    rows: Iterable[tuple[object, ...]],
) -> None:
    """Append a CIF loop with compact data rows."""
    tag_list = list(tags)
    formatted_rows = [tuple(_format_loop_value(value) for value in row) for row in rows]

    lines.append('loop_')
    lines.extend(tag_list)
    lines.extend(f'  {" ".join(row)}' for row in formatted_rows)


def _write_item(lines: list[str], tag: str, value: object) -> None:
    """Append one tag-value item."""
    formatted = _format_item_value(value)
    if formatted.startswith(';\n'):
        lines.append(tag)
        lines.extend(formatted.splitlines())
        return
    lines.append(f'{tag.ljust(_ITEM_WIDTH)} {formatted}')


def _section(lines: list[str], title: str) -> None:
    """Append a logical section header."""
    if lines and lines[-1]:
        lines.append('')
    lines.append(f'# ---- {title} ----')


def _format_item_value(value: object) -> str:
    """Format a CIF item value for report output."""
    if _is_cif_descriptor(value):
        formatted = _format_descriptor_value(value)
    elif not isinstance(value, str):
        formatted = format_value(value)
    elif value in {'?', '.'}:
        formatted = value
    elif '\n' in value or len(value) > _TEXT_WRAP_WIDTH:
        formatted = _format_text_field(value)
    elif not value.strip():
        formatted = '?'
    elif _needs_quotes(value):
        formatted = _quote_string(value)
    else:
        formatted = value
    return formatted


def _format_descriptor_value(value: object) -> str:
    """Format a descriptor while preserving parameter uncertainty."""
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    if isinstance(value, Parameter):
        return format_param_value(value)
    return _format_item_value(_descriptor_value(value))


def _format_loop_value(value: object) -> str:
    """Format a loop value."""
    formatted = _format_item_value(value)
    if formatted.startswith(';\n'):
        msg = 'Long text fields are not supported in IUCr report loops.'
        raise ValueError(msg)
    return formatted


def _format_text_field(value: str) -> str:
    """Format a long string as a CIF text field."""
    wrapped_lines: list[str] = []
    for line in value.splitlines():
        wrapped_lines.extend(textwrap.wrap(line, width=_TEXT_WRAP_WIDTH) or [''])
    return ';\n' + '\n'.join(wrapped_lines) + '\n;'


def _needs_quotes(value: str) -> bool:
    """Return whether *value* needs CIF quotes."""
    return any(char.isspace() for char in value) or value.startswith(('_', '#'))


def _quote_string(value: str) -> str:
    """Quote a CIF string using the shortest safe delimiter."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    return _format_text_field(value)


def _report_path(
    project: object,
    path: str | pathlib.Path | None,
) -> pathlib.Path:
    """Return the target report path."""
    if path is not None:
        return pathlib.Path(path)

    project_path = getattr(getattr(project, 'info', None), 'path', None)
    if project_path is None:
        msg = 'Project has no saved path. Save the project first.'
        raise FileNotFoundError(msg)

    project_name = getattr(project, 'name', 'project')
    return pathlib.Path(project_path) / 'reports' / f'{project_name}.cif'


def _iso_creation_datetime() -> str:
    """Return an ISO-8601 UTC timestamp for report creation."""
    return datetime.now(tz=UTC).isoformat(timespec='seconds')


def _software_label(name: str, *, package_name: str | None = None) -> str:
    """Return a software label with an installed version when known."""
    normalized = _base_engine_name(name)
    package = package_name or _PACKAGE_BY_ENGINE.get(normalized)
    version = package_version(package) if package is not None else None
    return f'{name} {version}' if version else name


def _analysis_software(project: object) -> object | None:
    """Return the project's persisted software snapshot."""
    analysis = getattr(project, 'analysis', None)
    return getattr(analysis, 'software', None)


def _role_descriptor_value(role: object, attr_name: str) -> object:
    """Return one software-role descriptor value."""
    return _descriptor_value(getattr(role, attr_name, None))


def _software_role_label(project: object, role_name: str) -> str:
    """Return a persisted software role label or CIF unknown."""
    software = _analysis_software(project)
    role = getattr(software, role_name, None)
    name = _role_descriptor_value(role, 'name')
    if name in {None, ''}:
        return '?'

    version = _role_descriptor_value(role, 'version')
    if version in {None, ''}:
        return str(name)
    return f'{name} {version}'


def _software_fit_datetime(project: object) -> object | None:
    """Return the persisted fit timestamp, if available."""
    software = _analysis_software(project)
    timestamp = _descriptor_value(getattr(software, 'timestamp', None))
    if timestamp in {None, ''}:
        return None
    return timestamp


def _framework_refinement_label(framework: str) -> str:
    """Return framework label for ``_computing`` fallback text."""
    if framework == '?':
        return _software_label('EasyDiffraction', package_name='easydiffraction')
    return framework


def _structure_refinement_label(
    framework: str,
    calculator: str,
    minimizer: str,
) -> str:
    """Return the free-text refinement software label."""
    framework_label = _framework_refinement_label(framework)
    if calculator == '?' or minimizer == '?':
        return framework_label
    return f'{framework_label} with {minimizer} minimizer and {calculator} calculator'


def _base_engine_name(name: str) -> str:
    """Return the package-key part of a software label."""
    return name.split(' ', maxsplit=1)[0].split('(', maxsplit=1)[0].lower()


def _single_crystal_experiments(project: object) -> list[object]:
    """Return single-crystal Bragg experiments in project order."""
    experiments = _collection_values(getattr(project, 'experiments', None))
    return [
        experiment
        for experiment in experiments
        if (
            _attribute_value(getattr(experiment, 'type', None), 'sample_form') == 'single crystal'
            and _attribute_value(
                getattr(experiment, 'type', None),
                'scattering_type',
            )
            == 'bragg'
        )
    ]


def _linked_structure(project: object, experiment: object) -> object:
    """Return the structure linked to a single-crystal experiment."""
    structures = getattr(project, 'structures', None)
    names = getattr(structures, 'names', ())
    linked_id = _attribute_value(getattr(experiment, 'linked_crystal', None), 'id')
    if linked_id in names:
        return structures[linked_id]

    structure_values = list(_collection_values(structures))
    if len(structure_values) == 1:
        return structure_values[0]

    experiment_name = getattr(experiment, 'name', type(experiment).__name__)
    msg = (
        f"Experiment '{experiment_name}' links crystal '{linked_id}', "
        f'but project structures are {list(names)}.'
    )
    raise ValueError(msg)


def _block_name(value: object) -> str:
    """Return a CIF-safe data-block code."""
    raw_name = str(value or 'I').strip()
    block_name = re.sub(r'[^A-Za-z0-9_]+', '_', raw_name).strip('_')
    if not block_name:
        return 'I'
    if block_name[0].isdigit():
        return f'block_{block_name}'
    return block_name


def _attribute_value(owner: object, attr_name: str) -> object:
    """Return ``owner.<attr_name>.value`` when available."""
    if owner is None:
        return None
    return _descriptor_value(getattr(owner, attr_name, None))


def _attribute_descriptor(owner: object, attr_name: str) -> object:
    """Return raw owner attr; preserve descriptor metadata."""
    if owner is None:
        return None
    return getattr(owner, attr_name, None)


def _fit_result(project: object) -> object:
    """Return the persisted fit-result category."""
    analysis = getattr(project, 'analysis', None)
    return getattr(analysis, 'fit_result', None)


def _atom_site_tags(family: str) -> tuple[str, ...]:
    """Return atom-site loop tags for one ADP family."""
    return (
        '_atom_site.label',
        '_atom_site.type_symbol',
        '_atom_site.fract_x',
        '_atom_site.fract_y',
        '_atom_site.fract_z',
        '_atom_site.occupancy',
        '_atom_site.ADP_type',
        f'_atom_site.{family}_iso_or_equiv',
        '_atom_site.Wyckoff_symbol',
    )


def _atom_site_row(atom_site: object) -> tuple[object, ...]:
    """Return one atom-site loop row."""
    return (
        _attribute_descriptor(atom_site, 'label'),
        _attribute_descriptor(atom_site, 'type_symbol'),
        _attribute_descriptor(atom_site, 'fract_x'),
        _attribute_descriptor(atom_site, 'fract_y'),
        _attribute_descriptor(atom_site, 'fract_z'),
        _attribute_descriptor(atom_site, 'occupancy'),
        _attribute_descriptor(atom_site, 'adp_type'),
        _attribute_descriptor(atom_site, 'adp_iso'),
        _attribute_descriptor(atom_site, 'wyckoff_letter'),
    )


def _atom_site_aniso_tags(family: str) -> tuple[str, ...]:
    """Return atom-site-aniso loop tags for one ADP family."""
    return (
        '_atom_site_aniso.label',
        f'_atom_site_aniso.{family}_11',
        f'_atom_site_aniso.{family}_22',
        f'_atom_site_aniso.{family}_33',
        f'_atom_site_aniso.{family}_12',
        f'_atom_site_aniso.{family}_13',
        f'_atom_site_aniso.{family}_23',
    )


def _atom_site_aniso_row(aniso_site: object) -> tuple[object, ...]:
    """Return one anisotropic-ADP loop row."""
    return (
        _attribute_descriptor(aniso_site, 'label'),
        _attribute_descriptor(aniso_site, 'adp_11'),
        _attribute_descriptor(aniso_site, 'adp_22'),
        _attribute_descriptor(aniso_site, 'adp_33'),
        _attribute_descriptor(aniso_site, 'adp_12'),
        _attribute_descriptor(aniso_site, 'adp_13'),
        _attribute_descriptor(aniso_site, 'adp_23'),
    )


def _atom_site_for_aniso(
    atom_site_by_label: dict[str, object],
    aniso_site: object,
) -> object | None:
    """Return the atom-site row that owns an anisotropic-ADP row."""
    label = str(_attribute_value(aniso_site, 'label'))
    return atom_site_by_label.get(label)


def _adp_family(atom_site: object) -> str:
    """Return ``B`` or ``U`` for an atom-site ADP convention."""
    adp_type = _attribute_value(atom_site, 'adp_type')
    return 'B' if str(adp_type).lower().startswith('b') else 'U'


def _sc_refln_row(refln: object) -> tuple[object, ...]:
    """Return one single-crystal reflection loop row."""
    return (
        _attribute_value(refln, 'index_h'),
        _attribute_value(refln, 'index_k'),
        _attribute_value(refln, 'index_l'),
        _attribute_value(refln, 'intensity_meas'),
        _attribute_value(refln, 'intensity_calc'),
        _attribute_value(refln, 'intensity_meas_su'),
        _include_status(refln),
    )


def _include_status(refln: object) -> str:
    """Return the IUCr include status for one reflection."""
    measured = _finite_number(_attribute_value(refln, 'intensity_meas'))
    sigma = _finite_number(_attribute_value(refln, 'intensity_meas_su'))
    if measured is None or sigma is None:
        return '?'
    if sigma <= 0:
        return 'o'
    return 'o' if measured > 3 * sigma else '<'


def _finite_number(value: object) -> float | None:
    """Return *value* as a finite float when possible."""
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _sc_extension_items(experiment: object) -> list[tuple[str, object]]:
    """Return EasyDiffraction extension items for a SC block."""
    linked_crystal = getattr(experiment, 'linked_crystal', None)
    diffrn = getattr(experiment, 'diffrn', None)
    expt_type = getattr(experiment, 'type', None)
    calculator = getattr(experiment, 'calculator', None)
    items: list[tuple[str, object]] = []
    items.extend(_iucr_items(linked_crystal, ('id', 'scale')))
    items.extend(
        _iucr_items(
            diffrn,
            ('ambient_magnetic_field', 'ambient_electric_field'),
        )
    )
    items.extend(
        _iucr_items(
            expt_type,
            ('sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'),
        )
    )
    items.extend(_iucr_items(calculator, ('type',)))
    return items


def _extinction_items(experiment: object, *, extension: bool) -> list[IucrItem]:
    """Return transformed extinction items filtered by namespace."""
    transformer = IucrCategoryTransformer.create('extinction')
    items = [
        item
        for item in transformer.items(experiment)
        if item.tag.startswith('_easydiffraction_') == extension
    ]
    if not extension:
        return items
    return [_with_extension_descriptor(experiment, item) for item in items]


def _with_extension_descriptor(experiment: object, item: IucrItem) -> IucrItem:
    """Return an extension item with its descriptor when available."""
    extinction = getattr(experiment, 'extinction', None)
    descriptor = _iucr_descriptor_for_tag(extinction, item.tag)
    if descriptor is None:
        return item
    return IucrItem(item.tag, descriptor)


def _powder_rietveld_experiments(project: object) -> list[object]:
    """Return powder Bragg experiments in project order."""
    experiments = _collection_values(getattr(project, 'experiments', None))
    return [
        experiment
        for experiment in experiments
        if (
            _attribute_value(getattr(experiment, 'type', None), 'sample_form') == 'powder'
            and _attribute_value(
                getattr(experiment, 'type', None),
                'scattering_type',
            )
            == 'bragg'
        )
    ]


def _powder_phases(
    project: object,
    experiments: list[object],
) -> list[_PowderPhase]:
    """Return unique powder phase blocks for the given experiments."""
    phases: list[_PowderPhase] = []
    seen_structure_names: set[str] = set()
    for experiment in experiments:
        for structure, linked_phase in _linked_powder_structures(project, experiment):
            structure_name = str(getattr(structure, 'name', len(phases) + 1))
            if structure_name in seen_structure_names:
                continue
            seen_structure_names.add(structure_name)
            block_name = f'{_block_name(project.name)}_phase_{len(phases) + 1}'
            phases.append(
                _PowderPhase(
                    block_name=block_name,
                    structure=structure,
                    linked_phase=linked_phase,
                )
            )
    return phases


def _powder_patterns(
    project: object,
    experiments: list[object],
) -> list[_PowderPattern]:
    """Return powder pattern blocks for the given experiments."""
    return [
        _PowderPattern(
            block_name=f'{_block_name(project.name)}_pwd_{index}',
            experiment=experiment,
        )
        for index, experiment in enumerate(experiments, start=1)
    ]


def _linked_powder_structures(
    project: object,
    experiment: object,
) -> list[tuple[object, object | None]]:
    """Return structures linked to a powder experiment."""
    structures = getattr(project, 'structures', None)
    names = getattr(structures, 'names', ())
    linked_phases = list(_collection_values(getattr(experiment, 'linked_phases', None)))
    linked_structures: list[tuple[object, object | None]] = []

    for linked_phase in linked_phases:
        phase_id = _attribute_value(linked_phase, 'id')
        if phase_id in names:
            linked_structures.append((structures[phase_id], linked_phase))

    if linked_structures:
        return linked_structures

    structure_values = list(_collection_values(structures))
    if len(structure_values) == 1:
        return [(structure_values[0], linked_phases[0] if linked_phases else None)]

    experiment_name = getattr(experiment, 'name', type(experiment).__name__)
    linked_ids = [_attribute_value(linked_phase, 'id') for linked_phase in linked_phases]
    msg = (
        f"Experiment '{experiment_name}' links phases {linked_ids}, "
        f'but project structures are {list(names)}.'
    )
    raise ValueError(msg)


def _pipe_ids(values: list[str]) -> str:
    """Return pipe-delimited block identifiers."""
    if not values:
        return '?'
    return '|' + '|'.join(values) + '|'


def _phase_block_names_for_experiment(
    project: object,
    experiment: object,
    phases: list[_PowderPhase],
) -> list[str]:
    """Return phase block names linked to one powder pattern."""
    linked_structures = _linked_powder_structures(project, experiment)
    linked_names = {
        getattr(structure, 'name', None) for structure, _linked_phase in linked_structures
    }
    return [
        phase.block_name
        for phase in phases
        if getattr(phase.structure, 'name', None) in linked_names
    ]


def _is_tof_experiment(experiment: object) -> bool:
    """Return whether a pattern uses time-of-flight x coordinates."""
    return _attribute_value(getattr(experiment, 'type', None), 'beam_mode') == 'time-of-flight'


def _powder_x_tag(experiment: object) -> str:
    """Return the powder profile-data x-axis tag."""
    if _is_tof_experiment(experiment):
        return '_pd_meas.time_of_flight'
    return '_pd_meas.2theta_scan'


def _powder_profile_row(
    experiment: object,
    data_point: object,
) -> tuple[object, ...]:
    """Return one powder profile-data row."""
    return (
        _powder_x_value(experiment, data_point),
        _attribute_value(data_point, 'intensity_meas'),
        _attribute_value(data_point, 'intensity_calc'),
        _attribute_value(data_point, 'intensity_bkg'),
        _powder_weight(data_point),
    )


def _powder_x_value(experiment: object, data_point: object) -> object:
    """Return the x coordinate for one powder data row."""
    if _is_tof_experiment(experiment):
        return _attribute_value(data_point, 'time_of_flight')
    return _attribute_value(data_point, 'two_theta')


def _powder_weight(data_point: object) -> object:
    """
    Return least-squares weight from intensity standard uncertainty.
    """
    sigma = _finite_number(_attribute_value(data_point, 'intensity_meas_su'))
    if sigma is None or sigma <= 0:
        return '?'
    return 1.0 / sigma**2


def _powder_refln_row(refln: object) -> tuple[object, ...]:
    """Return one powder reflection row."""
    return (
        _attribute_value(refln, 'index_h'),
        _attribute_value(refln, 'index_k'),
        _attribute_value(refln, 'index_l'),
        '?',
        _attribute_value(refln, 'f_squared_calc'),
        _attribute_value(refln, 'phase_id'),
        _attribute_value(refln, 'd_spacing'),
    )


def _powder_extension_items(experiment: object) -> list[tuple[str, object]]:
    """Return EasyDiffraction extension items for a powder block."""
    expt_type = getattr(experiment, 'type', None)
    calculator = getattr(experiment, 'calculator', None)
    peak = getattr(experiment, 'peak', None)
    background = getattr(experiment, 'background', None)
    items: list[tuple[str, object]] = []
    items.extend(
        _iucr_items(
            expt_type,
            ('sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'),
        )
    )
    items.extend(_iucr_items(calculator, ('type',)))
    items.extend(_iucr_items(peak, ('type',)))
    items.extend(_iucr_items(background, ('type',)))
    return items


@dataclass(frozen=True)
class _FormulaValues:
    """Chemical formula fields for global report metadata."""

    sum_formula: str
    moiety: str
    weight: str
    iupac: str


@dataclass(frozen=True)
class _PowderPhase:
    """One phase block in a Rietveld report."""

    block_name: str
    structure: object
    linked_phase: object | None


@dataclass(frozen=True)
class _PowderPattern:
    """One powder pattern block in a Rietveld report."""

    block_name: str
    experiment: object


def _chemical_formula_values(project: object) -> _FormulaValues:
    """Derive chemical formula values from atom sites where possible."""
    return _formula_values_from_structures(
        _collection_values(getattr(project, 'structures', None))
    )


def _structure_formula_values(structure: object) -> _FormulaValues:
    """Derive chemical formula values from one structure."""
    return _formula_values_from_structures((structure,))


def _formula_values_from_structures(structures: Iterable[object]) -> _FormulaValues:
    """Derive chemical formula values from structure atom sites."""
    counts: dict[str, float] = {}
    for structure in structures:
        for atom_site in _collection_values(getattr(structure, 'atom_sites', None)):
            symbol = _descriptor_value(getattr(atom_site, 'type_symbol', None))
            if not symbol:
                continue
            occupancy = _descriptor_value(getattr(atom_site, 'occupancy', None))
            counts[str(symbol)] = counts.get(str(symbol), 0.0) + _formula_count(occupancy)

    if not counts:
        return _FormulaValues(
            sum_formula='?',
            moiety='?',
            weight='?',
            iupac='?',
        )

    sum_formula = _format_formula(counts)
    return _FormulaValues(
        sum_formula=sum_formula,
        moiety=sum_formula,
        weight='?',
        iupac='?',
    )


def _formula_count(occupancy: object) -> float:
    """Return the site contribution for formula derivation."""
    if isinstance(occupancy, (int, float)):
        return float(occupancy)
    return 1.0


def _format_formula(counts: dict[str, float]) -> str:
    """Return a compact formula string."""
    parts: list[str] = []
    for symbol in sorted(counts, key=_formula_sort_key):
        count = counts[symbol]
        parts.append(f'{symbol}{_format_formula_suffix(count)}')
    return ' '.join(parts)


def _formula_sort_key(symbol: str) -> tuple[int, str]:
    """Return a Hill-style formula sort key."""
    if symbol == 'C':
        return (0, symbol)
    if symbol == 'H':
        return (1, symbol)
    return (2, symbol)


def _format_formula_suffix(count: float) -> str:
    """Return the formula count suffix."""
    if math.isclose(count, 1.0):
        return ''
    if math.isclose(count, round(count)):
        return str(round(count))
    return f'{count:.4g}'


def _descriptor_value(value: object) -> object:
    """Return ``value.value`` for descriptors, otherwise *value*."""
    return getattr(value, 'value', value)


def _is_cif_descriptor(value: object) -> bool:
    """Return whether value is a CIF descriptor or parameter."""
    return hasattr(value, 'value') and hasattr(value, '_cif_handler')


def _iucr_items(owner: object, attr_names: tuple[str, ...]) -> list[tuple[str, object]]:
    """Return IUCr-tagged descriptor values from *owner*."""
    if owner is None:
        return []
    return [_iucr_item(owner, attr_name) for attr_name in attr_names]


def _iucr_item(owner: object, attr_name: str) -> tuple[str, object]:
    """Return one ``(iucr_name, value)`` pair for a descriptor."""
    descriptor = _iucr_descriptor(owner, attr_name)
    return descriptor._cif_handler.iucr_name, descriptor


def _iucr_descriptor(owner: object, attr_name: str) -> object:
    """Return the descriptor carrying CIF metadata for *attr_name*."""
    descriptor = getattr(owner, attr_name)
    if hasattr(descriptor, '_cif_handler'):
        return descriptor

    for descriptor in _owner_descriptors(owner):
        if getattr(descriptor, 'name', None) == attr_name:
            return descriptor

    msg = f'{type(owner).__name__}.{attr_name} has no CIF handler.'
    raise AttributeError(msg)


def _iucr_descriptor_for_tag(owner: object, tag: str) -> object | None:
    """Return the descriptor carrying one IUCr tag."""
    if owner is None:
        return None

    private_type = getattr(owner, '_type', None)
    if _descriptor_iucr_name(private_type) == tag:
        return private_type

    for descriptor in _owner_descriptors(owner):
        if _descriptor_iucr_name(descriptor) == tag:
            return descriptor
    return None


def _descriptor_iucr_name(descriptor: object) -> str | None:
    """Return a descriptor's IUCr tag name, if present."""
    handler = getattr(descriptor, '_cif_handler', None)
    if handler is None:
        return None
    return handler.iucr_name


def _owner_descriptors(owner: object) -> Iterable[object]:
    """Yield descriptors exposed by category-style containers."""
    for source_name in ('parameters', 'scalar_descriptors'):
        yield from getattr(owner, source_name, ())


def _collection_values(collection: object) -> Iterable[object]:
    """Return collection values for project containers."""
    if collection is None:
        return ()
    values = getattr(collection, 'values', None)
    if callable(values):
        return values()
    if isinstance(collection, Iterable):
        return collection
    return (collection,)
