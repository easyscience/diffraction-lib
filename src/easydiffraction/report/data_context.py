# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Build shared data for report renderers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC
from datetime import datetime

import numpy as np

from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.item.base import intensity_category_for
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
_EXPERIMENT_TYPE_FIELDS = (
    'sample_form',
    'beam_mode',
    'radiation_probe',
    'scattering_type',
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
            'figures': {
                'fit_per_experiment': self._fit_figure_context(experiments),
            },
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
        return {
            'id': _safe_attr(structure, 'name'),
            'space_group': _attr_value(space_group, 'name_h_m'),
            'crystal_system': _attr_value(space_group, 'crystal_system'),
            'cell': _display_field_values(
                _safe_attr(structure, 'cell'),
                _STRUCTURE_CELL_FIELDS,
            ),
            'atom_sites': [
                self._atom_site_context(atom_site)
                for atom_site in _collection_values(_safe_attr(structure, 'atom_sites'))
            ],
            'atom_site_aniso': [
                self._atom_site_aniso_context(aniso_site)
                for aniso_site in _collection_values(
                    _safe_attr(structure, 'atom_site_aniso')
                )
            ],
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
                    _safe_attr(experiment, 'diffrn'),
                    'ambient_temperature',
                ),
                'ambient_pressure': _attr_value(
                    _safe_attr(experiment, 'diffrn'),
                    'ambient_pressure',
                ),
            },
            'measured_range': _value(_safe_attr(experiment, 'measured_range')),
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

    def _fit_figure_context(
        self,
        experiments: list[object],
    ) -> dict[str, object]:
        """Return measured-vs-calculated figures by experiment id."""
        figures = {}
        for experiment in experiments:
            figure = _fit_figure(experiment)
            if figure is not None:
                figures[str(_safe_attr(experiment, 'name'))] = figure
        return figures


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


def _software_role_context(role: object) -> dict[str, object]:
    """Return one software role context."""
    return {
        'name': _attr_value(role, 'name'),
        'version': _attr_value(role, 'version'),
        'url': _attr_value(role, 'url'),
    }


def _fit_figure(experiment: object) -> object | None:
    """Return a measured-vs-calculated Plotly figure if data exist."""
    try:
        pattern = intensity_category_for(experiment)
    except AttributeError:
        return None

    y_meas = _numeric_array(_safe_attr(pattern, 'intensity_meas'))
    y_calc = _numeric_array(_safe_attr(pattern, 'intensity_calc'))
    if y_meas is None or y_calc is None:
        return None
    _validate_same_length(experiment, y_meas, y_calc)

    if _is_single_crystal(experiment):
        return _single_crystal_fit_figure(experiment, pattern, y_meas, y_calc)
    return _line_fit_figure(experiment, pattern, y_meas, y_calc)


def _single_crystal_fit_figure(
    experiment: object,
    pattern: object,
    y_meas: np.ndarray,
    y_calc: np.ndarray,
) -> object:
    """Return a single-crystal measured-vs-calculated figure."""
    go = _plotly_go()
    trace_kwargs = {
        'x': y_calc,
        'y': y_meas,
        'mode': 'markers',
        'name': 'Measured',
    }
    y_meas_su = _numeric_array(_safe_attr(pattern, 'intensity_meas_su'))
    if y_meas_su is not None and y_meas_su.size == y_meas.size:
        trace_kwargs['error_y'] = {
            'type': 'data',
            'array': y_meas_su,
            'visible': True,
        }

    fig = go.Figure()
    fig.add_trace(go.Scatter(**trace_kwargs))
    _add_diagonal_trace(fig, y_meas, y_calc)
    _configure_fit_figure(
        fig,
        experiment,
        x_title='I²calc',
        y_title='I²meas',
    )
    return fig


def _line_fit_figure(
    experiment: object,
    pattern: object,
    y_meas: np.ndarray,
    y_calc: np.ndarray,
) -> object | None:
    """Return a line measured-vs-calculated figure."""
    x_values, x_title = _line_fit_x_values(experiment, pattern)
    if x_values is None:
        return None
    _validate_same_length(experiment, x_values, y_meas)

    go = _plotly_go()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_meas,
            mode='markers',
            name='Measured',
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_calc,
            mode='lines',
            name='Calculated',
        )
    )
    y_bkg = _numeric_array(_safe_attr(pattern, 'intensity_bkg'))
    if y_bkg is not None and y_bkg.size == x_values.size:
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_bkg,
                mode='lines',
                name='Background',
            )
        )
    _configure_fit_figure(fig, experiment, x_title=x_title, y_title='Intensity')
    return fig


def _line_fit_x_values(
    experiment: object,
    pattern: object,
) -> tuple[np.ndarray | None, str]:
    """Return line-plot x values and axis title."""
    beam_mode = str(_attr_value(_safe_attr(experiment, 'type'), 'beam_mode')).lower()
    if beam_mode == 'time-of-flight':
        return _numeric_array(_safe_attr(pattern, 'time_of_flight')), 'Time of flight'
    return _numeric_array(_safe_attr(pattern, 'two_theta')), '2θ'


def _add_diagonal_trace(
    fig: object,
    y_meas: np.ndarray,
    y_calc: np.ndarray,
) -> None:
    """Add the y=x reference line to a scatter figure."""
    go = _plotly_go()
    lower = float(min(np.min(y_meas), np.min(y_calc)))
    upper = float(max(np.max(y_meas), np.max(y_calc)))
    fig.add_trace(
        go.Scatter(
            x=[lower, upper],
            y=[lower, upper],
            mode='lines',
            name='I²meas = I²calc',
        )
    )


def _configure_fit_figure(
    fig: object,
    experiment: object,
    *,
    x_title: str,
    y_title: str,
) -> None:
    """Apply shared report-figure layout."""
    experiment_id = _safe_attr(experiment, 'name') or 'experiment'
    fig.update_layout(
        template='plotly_white',
        title=f"Measured vs calculated: {experiment_id}",
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=440,
        margin={'l': 64, 'r': 24, 't': 64, 'b': 56},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02},
    )


def _validate_same_length(
    experiment: object,
    left: np.ndarray,
    right: np.ndarray,
) -> None:
    """Raise if report figure arrays have inconsistent lengths."""
    if left.size == right.size:
        return
    experiment_id = _safe_attr(experiment, 'name') or type(experiment).__name__
    msg = (
        f"Cannot build report figure for experiment '{experiment_id}': "
        f'intensity arrays have lengths {left.size} and {right.size}.'
    )
    raise ValueError(msg)


def _is_single_crystal(experiment: object) -> bool:
    """Return whether the experiment is single-crystal data."""
    expt_type = _safe_attr(experiment, 'type')
    return str(_attr_value(expt_type, 'sample_form')).lower() == 'single crystal'


def _numeric_array(value: object) -> np.ndarray | None:
    """Return a numeric one-dimensional array, if present."""
    if value is None:
        return None
    array = np.asarray(_value(value), dtype=float)
    if array.ndim != 1 or array.size == 0:
        return None
    return array


def _plotly_go() -> object:
    """Return Plotly graph objects for report figures."""
    import plotly.graph_objects as go  # noqa: PLC0415

    return go


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
