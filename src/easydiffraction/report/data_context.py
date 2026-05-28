# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Build shared data for report renderers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC
from datetime import datetime

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
_FIT_RESULT_FIELDS = (
    'result_kind',
    'success',
    'message',
    'iterations',
    'fitting_time',
    'reduced_chi_square',
    'n_data_points',
    'n_parameters',
    'n_free_parameters',
    'degrees_of_freedom',
    'r_factor_all',
    'wr_factor_all',
    'r_factor_gt',
    'wr_factor_gt',
    'prof_r_factor',
    'prof_wr_factor',
    'prof_wr_expected',
    'profile_function',
    'background_function',
)
_PUBLICATION_JOURNAL_FIELDS = (
    'name_full',
    'year',
    'volume',
    'issue',
    'page_first',
    'page_last',
    'paper_category',
    'paper_doi',
    'coden_astm',
    'suppl_publ_number',
)
_PUBLICATION_JOURNAL_DATE_FIELDS = (
    'accepted',
    'from_coeditor',
    'printers_final',
)
_PUBLICATION_JOURNAL_COEDITOR_FIELDS = (
    'code',
    'name',
    'notes',
)
_PUBLICATION_CONTACT_AUTHOR_FIELDS = (
    'name',
    'address',
    'email',
    'phone',
    'id_orcid',
    'id_iucr',
)
_PUBLICATION_BODY_FIELDS = (
    'title',
    'synopsis',
    'abstract',
)
_PUBLICATION_AUTHOR_FIELDS = (
    'name',
    'address',
    'footnote',
    'id_orcid',
    'id_iucr',
)


class ReportDataContext:
    """
    Build renderer-neutral report data from a project.

    Parameters
    ----------
    project : object
        Project facade that owns structures, experiments, analysis, and
        publication metadata.
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
            'experiments': [
                self._experiment_context(experiment) for experiment in experiments
            ],
            'refinement': self._refinement_context(),
            'software': self._software_context(),
            'publication': self._publication_context(),
            'metadata': {
                'easydiffraction_version': package_version('easydiffraction'),
                'generated_at': datetime.now(tz=UTC).isoformat(timespec='seconds'),
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
            'atom_sites': [
                self._atom_site_context(atom_site)
                for atom_site in atom_sites
            ],
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
                self._atom_site_aniso_context(aniso_site)
                for aniso_site in aniso_sites
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
        }

    def _atom_site_context(self, atom_site: object) -> dict[str, object]:
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

    def _atom_site_aniso_context(self, aniso_site: object) -> dict[str, object]:
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

    def _experiment_context(self, experiment: object) -> dict[str, object]:
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
        }

    def _refinement_context(self) -> dict[str, object]:
        """Return refinement summary data."""
        analysis = _safe_attr(self._project, 'analysis')
        fit_result = _safe_attr(analysis, 'fit_result')
        fields = _field_values(fit_result, _FIT_RESULT_FIELDS)
        total = fields.get('n_parameters')
        free = fields.get('n_free_parameters')
        fixed = total - free if isinstance(total, int) and isinstance(free, int) else None
        return {
            'fit_result': fields,
            'parameters': {
                'total': total,
                'free': free,
                'fixed': fixed,
            },
            'constraints': len(list(_collection_values(_safe_attr(analysis, 'constraints')))),
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

    def _publication_context(self) -> dict[str, object]:
        """Return journal-publication metadata."""
        publication = _safe_attr(self._project, 'publication')
        body = _safe_attr(publication, 'body')
        return {
            'journal': _field_values(
                _safe_attr(publication, 'journal'),
                _PUBLICATION_JOURNAL_FIELDS,
            ),
            'journal_date': _field_values(
                _safe_attr(publication, 'journal_date'),
                _PUBLICATION_JOURNAL_DATE_FIELDS,
            ),
            'journal_coeditor': _field_values(
                _safe_attr(publication, 'journal_coeditor'),
                _PUBLICATION_JOURNAL_COEDITOR_FIELDS,
            ),
            'contact_author': _field_values(
                _safe_attr(publication, 'contact_author'),
                _PUBLICATION_CONTACT_AUTHOR_FIELDS,
            ),
            'body': {
                **_field_values(body, _PUBLICATION_BODY_FIELDS),
                'keywords': list(_safe_attr(body, 'keywords') or []),
            },
            'authors': [
                _field_values(author, _PUBLICATION_AUTHOR_FIELDS)
                for author in _collection_values(_safe_attr(publication, 'authors'))
            ],
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
        field: _display_metadata(_safe_attr(owner, field), context=context)
        for field in fields
    }


def _display_metadata(value: object, *, context: str) -> dict[str, str]:
    """Return display label and units for one descriptor."""
    name_resolver = getattr(value, 'resolve_display_name', None)
    units_resolver = getattr(value, 'resolve_display_units', None)
    label = name_resolver(context) if callable(name_resolver) else ''
    units = units_resolver(context) if callable(units_resolver) else ''
    return {'label': label, 'units': units}


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
        return None

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
