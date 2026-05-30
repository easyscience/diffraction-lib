# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project display facade grouping charts and reports."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING

from easydiffraction.analysis.fit_helpers.bayesian import posterior_predictive_cache_key
from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.display.plotting import PlotterEngineEnum
from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum
from easydiffraction.display.plotting import _MeasVsCalcPlotOptions
from easydiffraction.display.progress import ACTIVITY_LABEL_PROCESSING
from easydiffraction.display.progress import activity_indicator
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_object_help
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.project.project import Project


_PATTERN_OPTION_DESCRIPTIONS: dict[str, str] = {
    'auto': 'Show the most informative available pattern view.',
    'measured': 'Measured diffraction intensities.',
    'calculated': 'Calculated diffraction intensities.',
    'background': 'Calculated background intensities when present.',
    'residual': 'Measured minus calculated residuals when supported.',
    'bragg': 'Bragg reflection tick marks when reflection data exists.',
    'excluded': 'Excluded fitting regions when defined on the experiment.',
    'uncertainty': 'Posterior predictive uncertainty bands when available.',
}


_STRUCTURE_OPTION_DESCRIPTIONS: dict[str, str] = {
    'auto': 'Show the features the structure and engine support.',
    'atoms': 'Atoms as spheres, occupancy wedges, or ADP ellipsoids.',
    'bonds': 'Bonds between atoms within the per-structure cutoffs.',
    'cell': 'Unit-cell edges.',
    'axes': 'The a/b/c axis triad.',
    'moments': 'Magnetic-moment arrows (no moment data in version 1).',
    'labels': 'Atom labels at each site.',
}


@dataclass(frozen=True, slots=True)
class PatternOptionStatus:
    """Availability metadata for one ``display.pattern`` option."""

    name: str
    description: str
    available: bool
    auto_included: bool
    reason: str


class ParameterDisplay:
    """Parameter-table namespace under ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project

    def all(self) -> None:
        """Show all structure and experiment parameters."""
        self._project.analysis.display.all_params()

    def fittable(self) -> None:
        """Show all currently fittable parameters."""
        self._project.analysis.display.fittable_params()

    def free(self) -> None:
        """Show all currently free parameters."""
        self._project.analysis.display.free_params()

    def access(self) -> None:
        """Show Python access paths for all parameters."""
        self._project.analysis.display.how_to_access_parameters()

    def cif_uids(self) -> None:
        """Show CIF unique identifiers for all parameters."""
        self._project.analysis.display.parameter_cif_uids()

    def help(self) -> None:
        """Print available parameter-display methods."""
        render_object_help(self)


class FitDisplay:
    """Fit-report namespace under ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project

    def results(self) -> None:
        """Show the latest fit summary and fitted parameter table."""
        analysis = self._project.analysis
        if analysis.fit_results is None:
            analysis.display.fit_results()
            return

        self._show_settings_used()
        analysis.display.fit_results()

    def _show_settings_used(self) -> None:
        """Show minimizer settings used for the latest fit."""
        rows = self._settings_used_rows()
        if not rows:
            return

        console.print('⚙️ Settings used:')
        render_table(
            columns_headers=['Name', 'Value', 'Description'],
            columns_alignment=['left', 'right', 'left'],
            columns_data=rows,
        )

    def _settings_used_rows(self) -> list[list[str]]:
        """Return minimizer setting rows for display."""
        minimizer = self._project.analysis.minimizer
        rows: list[list[str]] = []
        for name in minimizer._setting_descriptor_names:
            descriptor = getattr(minimizer, name)
            rows.append([
                name,
                str(descriptor.value),
                descriptor.description or '',
            ])
        return rows

    def correlations(
        self,
        threshold: float | None = None,
        precision: int = 2,
        *,
        max_parameters: int = 6,
        show_diagonal: bool = True,
    ) -> None:
        """Show parameter correlations from the latest fit."""
        self._project.rendering_plot.plotter.plot_param_correlations(
            threshold=threshold,
            precision=precision,
            max_parameters=max_parameters,
            show_diagonal=show_diagonal,
        )

    def series(
        self,
        param: object | None = None,
        versus: str | None = None,
    ) -> None:
        """
        Plot fitted parameter(s) across sequential results.

            Use a persisted diffrn path such as
            ``'diffrn.ambient_temperature'`` for *versus*. When *param*
            is provided, plot that single parameter. When *param* is
            ``None`` (default), plot every fitted parameter, one after
            another.
        """
        if param is None:
            self._project.rendering_plot.plotter.plot_all_param_series(versus=versus)
        else:
            self._project.rendering_plot.plotter.plot_param_series(param=param, versus=versus)

    def help(self) -> None:
        """Print available fit-display methods."""
        render_object_help(self)


class PosteriorDisplay:
    """Posterior-plot namespace under ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project

    def _pairs_need_processing_indicator(
        self,
        *,
        parameters: list[object] | None,
    ) -> bool:
        """
        Return whether posterior pair plotting still needs processing.
        """
        if parameters is not None:
            return True

        analysis = self._project.analysis
        fit_results = getattr(analysis, 'fit_results', None)
        runtime_pair_caches = getattr(fit_results, 'posterior_pair_caches', None)
        if runtime_pair_caches:
            return False

        sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
        return not bool(sidecar_data.get('pair_caches', {}))

    def _predictive_needs_processing_indicator(
        self,
        *,
        expt_name: str,
        style: str,
        x: object | None,
    ) -> bool:
        """Return whether predictive plotting still needs processing."""
        analysis = self._project.analysis
        experiment = self._project.experiments[expt_name]
        plotter = self._project.rendering_plot.plotter
        _, x_axis_name, _, _, _ = plotter._resolve_x_axis(experiment.type, x)
        x_axis_name = str(x_axis_name)
        require_draws = plotter.engine == PlotterEngineEnum.PLOTLY.value and style in {
            'draws',
            'band+draws',
        }

        sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
        predictive_dataset = sidecar_data.get('predictive_datasets', {}).get(expt_name)
        if predictive_dataset is not None:
            dataset_axis_name = str(predictive_dataset.get('x_axis_name', ''))
            if dataset_axis_name in {'', x_axis_name}:
                return require_draws and predictive_dataset.get('draws') is None

        fit_results = getattr(analysis, 'fit_results', None)
        posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
        if not posterior_predictive:
            return True

        cache_keys = [
            posterior_predictive_cache_key(expt_name, x_axis_name, include_draws=True),
            posterior_predictive_cache_key(expt_name, x_axis_name, include_draws=False),
            expt_name,
        ]
        for cache_key in cache_keys:
            summary = posterior_predictive.get(cache_key)
            if summary is None or str(getattr(summary, 'x_axis_name', '')) != x_axis_name:
                continue
            return require_draws and getattr(summary, 'draws', None) is None

        return True

    def pairs(
        self,
        parameters: list[object] | None = None,
        style: PosteriorPairPlotStyleEnum | str = PosteriorPairPlotStyleEnum.AUTO,
        *,
        threshold: float | None = None,
        max_parameters: int = 6,
    ) -> None:
        """Plot posterior pair relationships for sampled parameters."""
        indicator_context = (
            activity_indicator(
                ACTIVITY_LABEL_PROCESSING,
                verbosity=VerbosityEnum(self._project.verbosity.fit.value),
            )
            if self._pairs_need_processing_indicator(parameters=parameters)
            else nullcontext()
        )
        with indicator_context:
            self._project.rendering_plot.plotter.plot_posterior_pairs(
                parameters=parameters,
                style=style,
                threshold=threshold,
                max_parameters=max_parameters,
            )

    def distribution(self, param: object | None = None) -> None:
        """
        Plot posterior distributions for one or all free parameters.
        """
        plotter = self._project.rendering_plot.plotter
        if param is not None:
            plotter.plot_param_distribution(param)
            return

        free_parameters = getattr(self._project, 'free_parameters', None)
        if not free_parameters:
            log.warning('No free parameters found.')
            return

        for free_parameter in free_parameters:
            plotter.plot_param_distribution(free_parameter)

    def predictive(
        self,
        expt_name: str,
        style: str = 'band',
        x_min: float | None = None,
        x_max: float | None = None,
        *,
        show_residual: bool | None = None,
        x: object | None = None,
    ) -> None:
        """Plot posterior predictive summaries for one experiment."""
        indicator_context = (
            activity_indicator(
                ACTIVITY_LABEL_PROCESSING,
                verbosity=VerbosityEnum(self._project.verbosity.fit.value),
            )
            if self._predictive_needs_processing_indicator(
                expt_name=expt_name,
                style=style,
                x=x,
            )
            else nullcontext()
        )
        with indicator_context:
            self._project.rendering_plot.plotter.plot_posterior_predictive(
                expt_name=expt_name,
                style=style,
                x_min=x_min,
                x_max=x_max,
                show_residual=show_residual,
                x=x,
            )

    def help(self) -> None:
        """Print available posterior-display methods."""
        render_object_help(self)


class ProjectDisplay:
    """Grouped display facade exposed as ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project
        self._parameters = ParameterDisplay(project)
        self._fit = FitDisplay(project)
        self._posterior = PosteriorDisplay(project)

    @property
    def parameters(self) -> ParameterDisplay:
        """Parameter-table namespace."""
        return self._parameters

    @property
    def fit(self) -> FitDisplay:
        """Fit-report namespace."""
        return self._fit

    @property
    def posterior(self) -> PosteriorDisplay:
        """Posterior-plot namespace."""
        return self._posterior

    def help(self) -> None:
        """Print display namespaces and methods."""
        render_object_help(self)

    def pattern(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        include: str | tuple[str, ...] = 'auto',
        *,
        x: object | None = None,
    ) -> None:
        """Show a pattern view for one experiment."""
        normalized_include = self._normalize_include(include)
        statuses = self._pattern_option_statuses(expt_name)

        if normalized_include == ('auto',):
            auto_include = self._auto_include(statuses)
            if x is not None:
                auto_include = tuple(option for option in auto_include if option != 'excluded')
            if not auto_include:
                msg = self._status_by_name(statuses, 'auto').reason
                raise ValueError(msg)
            if 'uncertainty' in auto_include:
                indicator_context = (
                    activity_indicator(
                        ACTIVITY_LABEL_PROCESSING,
                        verbosity=VerbosityEnum(self._project.verbosity.fit.value),
                    )
                    if self._posterior._predictive_needs_processing_indicator(
                        expt_name=expt_name,
                        style='band',
                        x=x,
                    )
                    else nullcontext()
                )
                with indicator_context:
                    self._project.rendering_plot.plotter._plot_posterior_predictive_request(
                        expt_name=expt_name,
                        style='band',
                        plot_options=_MeasVsCalcPlotOptions(
                            x_min=x_min,
                            x_max=x_max,
                            show_residual=True if 'residual' in auto_include else None,
                            show_background='background' in auto_include,
                            show_bragg='bragg' in auto_include,
                            show_excluded='excluded' in auto_include,
                            x=x,
                        ),
                    )
                return
            self._show_point_estimate_pattern(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                include=auto_include,
                statuses=statuses,
                x=x,
            )
            return

        self._validate_requested_include(statuses, normalized_include)
        if x is not None and 'excluded' in normalized_include:
            msg = "Excluded-region overlays currently require the experiment's default x-axis."
            raise ValueError(msg)

        if 'uncertainty' in normalized_include:
            indicator_context = (
                activity_indicator(
                    ACTIVITY_LABEL_PROCESSING,
                    verbosity=VerbosityEnum(self._project.verbosity.fit.value),
                )
                if self._posterior._predictive_needs_processing_indicator(
                    expt_name=expt_name,
                    style='band',
                    x=x,
                )
                else nullcontext()
            )
            with indicator_context:
                self._project.rendering_plot.plotter._plot_posterior_predictive_request(
                    expt_name=expt_name,
                    style='band',
                    plot_options=_MeasVsCalcPlotOptions(
                        x_min=x_min,
                        x_max=x_max,
                        show_residual=True if 'residual' in normalized_include else None,
                        show_background='background' in normalized_include,
                        show_bragg='bragg' in normalized_include,
                        show_excluded='excluded' in normalized_include,
                        x=x,
                    ),
                )
            return

        self._show_point_estimate_pattern(
            expt_name=expt_name,
            x_min=x_min,
            x_max=x_max,
            include=normalized_include,
            statuses=statuses,
            x=x,
        )

    def show_pattern_options(self, expt_name: str) -> None:
        """Show available ``pattern(include=...)`` options."""
        statuses = self._pattern_option_statuses(expt_name)
        render_table(
            columns_headers=['Option', 'Description', 'Available', 'Auto', 'Reason'],
            columns_alignment=['left', 'left', 'center', 'center', 'left'],
            columns_data=[
                [
                    status.name,
                    status.description,
                    'yes' if status.available else 'no',
                    'yes' if status.auto_included else 'no',
                    status.reason or '-',
                ]
                for status in statuses
            ],
        )

    def structure(
        self,
        struct_name: str,
        include: str | tuple[str, ...] = 'auto',
        range: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None = None,
        path: str | None = None,
    ) -> None:
        """
        Show a 3D structure view for one structure.

        Parallels :meth:`pattern`: it draws with the active
        ``project.rendering_structure`` engine and displays directly (no return value).
        Feature visibility is resolved per ADR section 8; the renderer
        announces and skips any feature it cannot draw.

        Parameters
        ----------
        struct_name : str
            Name of the structure to draw.
        include : str | tuple[str, ...]
            ``'auto'`` (default) resolves features from data availability,
            persisted ``project.rendering_structure`` flags, then built-in defaults; an
            explicit tuple of ``atoms``/``bonds``/``cell``/``axes``/
            ``moments``/``labels`` wins outright.
        range : tuple | None
            Optional per-axis ``((min, max), ...)`` window overriding the
            persisted ``project.rendering_structure`` range for this call only.
        path : str | None
            When given, write the rendered view to this path instead of
            displaying it (a standalone HTML file for the Three.js engine).
        """
        from easydiffraction.display.structure.builder import build_scene  # noqa: PLC0415
        from easydiffraction.display.structure.builder import (  # noqa: PLC0415
            structure_feature_availability,
        )

        structure = self._project.structures[struct_name]
        availability = structure_feature_availability(structure, style=self._project.style)
        features = self._resolve_structure_features(include, availability)
        window = range if range is not None else self._project.rendering_structure.view_range()
        scene = build_scene(
            structure,
            style=self._project.style,
            view_range=window,
            features=features,
        )
        output = self._project.rendering_structure.viewer.render(scene, features=features)
        if path is not None:
            import pathlib  # noqa: PLC0415

            pathlib.Path(path).write_text(output)
            return
        self._emit_structure_output(output)

    def show_structure_options(self, struct_name: str) -> None:
        """Show available ``structure(include=...)`` options with reasons."""
        from easydiffraction.display.structure.builder import (  # noqa: PLC0415
            structure_feature_availability,
        )

        structure = self._project.structures[struct_name]
        availability = structure_feature_availability(structure, style=self._project.style)
        supported = self._project.rendering_structure.viewer.supported_features()
        auto = self._resolve_structure_features('auto', availability)

        rows = []
        for option in ('atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'):
            in_data = option in availability.available
            in_engine = option in supported
            reason = self._structure_option_reason(option, in_data=in_data, in_engine=in_engine)
            rows.append([
                option,
                _STRUCTURE_OPTION_DESCRIPTIONS[option],
                'yes' if (in_data and in_engine) else 'no',
                'yes' if (option in auto and in_engine) else 'no',
                reason or '-',
            ])
        render_table(
            columns_headers=['Option', 'Description', 'Available', 'Auto', 'Reason'],
            columns_alignment=['left', 'left', 'center', 'center', 'left'],
            columns_data=rows,
        )
        if availability.radius_substitutions:
            console.paragraph('Radius substitutions (fell back to covalent)')
            console.print(', '.join(availability.radius_substitutions))

    def _resolve_structure_features(
        self,
        include: str | tuple[str, ...],
        availability: object,
    ) -> frozenset[str]:
        """Resolve the concrete feature set per ADR section 8 precedence."""
        normalized = self._normalize_structure_include(include)
        if normalized != ('auto',):
            return frozenset(normalized)
        view = self._project.rendering_structure
        resolved = {f for f in ('atoms', 'bonds', 'cell', 'axes') if f in availability.available}
        if 'labels' in availability.available and view.show_labels.value:
            resolved.add('labels')
        if 'moments' in availability.available and view.show_moments.value:
            resolved.add('moments')
        return frozenset(resolved)

    @staticmethod
    def _normalize_structure_include(include: str | tuple[str, ...]) -> tuple[str, ...]:
        """Validate and normalize a ``structure(include=...)`` value."""
        values = (include,) if isinstance(include, str) else include
        if not values:
            msg = 'include must contain at least one option.'
            raise ValueError(msg)
        normalized = tuple(dict.fromkeys(values))
        unknown = [value for value in normalized if value not in _STRUCTURE_OPTION_DESCRIPTIONS]
        if unknown:
            msg = f'Unknown structure include option(s): {unknown}.'
            raise ValueError(msg)
        if 'auto' in normalized and len(normalized) > 1:
            msg = "include='auto' cannot be combined with other options."
            raise ValueError(msg)
        return normalized

    @staticmethod
    def _structure_option_reason(option: str, *, in_data: bool, in_engine: bool) -> str:
        """Explain why a structure option is unavailable, if it is."""
        if not in_engine:
            return 'Shown only by the 3D engines.'
        if not in_data:
            if option == 'moments':
                return 'No moment data in version 1.'
            return 'No data for this structure.'
        return ''

    def _emit_structure_output(self, output: str) -> None:
        """Display ASCII text in the console or HTML in a notebook."""
        from easydiffraction.display.structure.enums import ViewerEngineEnum  # noqa: PLC0415
        from easydiffraction.utils.environment import in_jupyter  # noqa: PLC0415

        if self._project.rendering_structure.viewer.engine == ViewerEngineEnum.ASCII.value:
            console.print(output)
            return
        if in_jupyter():
            from IPython.display import HTML  # noqa: PLC0415
            from IPython.display import display  # noqa: PLC0415

            display(HTML(output))
            return
        console.print(
            'Three.js structure view generated as HTML. Pass path=... to save it, '
            "or set project.rendering_structure.type = 'ascii' for a terminal view.",
        )

    @staticmethod
    def _normalize_include(include: str | tuple[str, ...]) -> tuple[str, ...]:
        """Validate and normalize a ``pattern(include=...)`` value."""
        values = (include,) if isinstance(include, str) else include
        if not values:
            msg = 'include must contain at least one option.'
            raise ValueError(msg)

        normalized = tuple(dict.fromkeys(values))
        unknown = [value for value in normalized if value not in _PATTERN_OPTION_DESCRIPTIONS]
        if unknown:
            msg = f'Unknown pattern include option(s): {unknown}.'
            raise ValueError(msg)
        if 'auto' in normalized and len(normalized) > 1:
            msg = "include='auto' cannot be combined with other options."
            raise ValueError(msg)
        return normalized

    @staticmethod
    def _status_by_name(
        statuses: list[PatternOptionStatus],
        option_name: str,
    ) -> PatternOptionStatus:
        """Return one pattern option status by name."""
        for status in statuses:
            if status.name == option_name:
                return status
        msg = f'Unknown pattern option: {option_name}.'
        raise ValueError(msg)

    @staticmethod
    def _with_available_options(
        status_by_name: dict[str, PatternOptionStatus],
        required: tuple[str, ...],
        optional: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Return required options plus available optional ones."""
        include = list(required)
        include.extend(
            option_name for option_name in optional if status_by_name[option_name].available
        )
        return tuple(include)

    @classmethod
    def _auto_include(
        cls,
        statuses: list[PatternOptionStatus],
    ) -> tuple[str, ...]:
        """Return the effective include tuple for ``include='auto'``."""
        status_by_name = {status.name: status for status in statuses}
        optional_point_estimate = ('background', 'residual', 'bragg', 'excluded')

        if status_by_name['uncertainty'].available:
            return cls._with_available_options(
                status_by_name,
                ('measured', 'calculated', 'uncertainty'),
                optional_point_estimate,
            )
        if status_by_name['measured'].available and status_by_name['calculated'].available:
            return cls._with_available_options(
                status_by_name,
                ('measured', 'calculated'),
                optional_point_estimate,
            )
        if status_by_name['measured'].available:
            return cls._with_available_options(
                status_by_name,
                ('measured',),
                ('excluded',),
            )
        if status_by_name['calculated'].available:
            return cls._with_available_options(
                status_by_name,
                ('calculated',),
                ('excluded',),
            )
        return ()

    @classmethod
    def _validate_requested_include(
        cls,
        statuses: list[PatternOptionStatus],
        include: tuple[str, ...],
    ) -> None:
        """
        Raise a clear error when a requested include is unavailable.
        """
        status_by_name = {status.name: status for status in statuses}
        unavailable = [
            option_name
            for option_name in include
            if option_name != 'auto' and not status_by_name[option_name].available
        ]
        if unavailable:
            option_name = unavailable[0]
            msg = status_by_name[option_name].reason
            raise ValueError(msg)

        include_set = set(include)
        if 'background' in include_set and not {'measured', 'calculated'}.issubset(include_set):
            msg = 'background requires both measured and calculated data in the same view.'
            raise ValueError(msg)
        if 'bragg' in include_set and not {'measured', 'calculated'}.issubset(include_set):
            msg = 'bragg requires both measured and calculated data in the same view.'
            raise ValueError(msg)
        if 'residual' in include_set and not {'measured', 'calculated'}.issubset(include_set):
            msg = 'residual requires both measured and calculated data in the same view.'
            raise ValueError(msg)
        if 'excluded' in include_set and not include_set.intersection({
            'measured',
            'calculated',
            'uncertainty',
        }):
            msg = 'excluded requires measured, calculated, or uncertainty data in the same view.'
            raise ValueError(msg)

    def _show_point_estimate_pattern(
        self,
        *,
        expt_name: str,
        x_min: float | None,
        x_max: float | None,
        include: tuple[str, ...],
        statuses: list[PatternOptionStatus],
        x: object | None,
    ) -> None:
        """
        Dispatch a point-estimate pattern view to the live plotter.
        """
        self._validate_requested_include(statuses, include)
        include_set = set(include)
        if include_set == {'measured'}:
            self._project.rendering_plot.plotter.plot_meas(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
                show_excluded=False,
            )
            return
        if include_set == {'measured', 'excluded'}:
            self._project.rendering_plot.plotter.plot_meas(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
                show_excluded=True,
            )
            return
        if include_set == {'calculated'}:
            self._project.rendering_plot.plotter.plot_calc(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
                show_excluded=False,
            )
            return
        if include_set == {'calculated', 'excluded'}:
            self._project.rendering_plot.plotter.plot_calc(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
                show_excluded=True,
            )
            return
        if {'measured', 'calculated'}.issubset(include_set):
            self._project.rendering_plot.plotter._plot_meas_vs_calc_request(
                expt_name=expt_name,
                plot_options=_MeasVsCalcPlotOptions(
                    x_min=x_min,
                    x_max=x_max,
                    show_residual='residual' in include_set,
                    show_background='background' in include_set,
                    show_bragg='bragg' in include_set,
                    show_excluded='excluded' in include_set,
                    x=x,
                ),
            )
            return

        msg = (
            'Point-estimate pattern views currently support include values '
            "'measured', 'calculated', or combinations containing both."
        )
        raise ValueError(msg)

    def _pattern_option_statuses(self, expt_name: str) -> list[PatternOptionStatus]:
        """Return availability details for the requested experiment."""
        self._project.rendering_plot.plotter._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        pattern = intensity_category_for(experiment)
        sample_form = experiment.type.sample_form.value
        scattering_type = experiment.type.scattering_type.value
        has_linked_structure = self._has_linked_structure_for_calculation(experiment)

        measured_available = self._has_nonempty_value(getattr(pattern, 'intensity_meas', None))
        calculated_available = has_linked_structure and self._has_nonempty_value(
            getattr(pattern, 'intensity_calc', None)
        )
        background_available = (
            sample_form == SampleFormEnum.POWDER.value
            and scattering_type == ScatteringTypeEnum.BRAGG.value
            and measured_available
            and calculated_available
            and self._has_nonempty_value(getattr(experiment, 'background', None))
            and self._has_nonempty_value(getattr(pattern, 'intensity_bkg', None))
        )
        bragg_available = (
            measured_available
            and calculated_available
            and sample_form == SampleFormEnum.POWDER.value
            and scattering_type == ScatteringTypeEnum.BRAGG.value
            and self._has_nonempty_value(getattr(experiment, 'refln', None))
        )
        residual_available = (
            sample_form == SampleFormEnum.POWDER.value
            and measured_available
            and calculated_available
        )
        has_excluded_regions = self._has_nonempty_value(
            getattr(experiment, 'excluded_regions', None)
        )
        uncertainty_available, uncertainty_reason = self._uncertainty_status(
            measured_available=measured_available,
            sample_form=sample_form,
            scattering_type=scattering_type,
        )

        auto_include = self._auto_include([
            PatternOptionStatus(
                name='measured',
                description=_PATTERN_OPTION_DESCRIPTIONS['measured'],
                available=measured_available,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='calculated',
                description=_PATTERN_OPTION_DESCRIPTIONS['calculated'],
                available=calculated_available,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='background',
                description=_PATTERN_OPTION_DESCRIPTIONS['background'],
                available=background_available,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='residual',
                description=_PATTERN_OPTION_DESCRIPTIONS['residual'],
                available=residual_available,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='bragg',
                description=_PATTERN_OPTION_DESCRIPTIONS['bragg'],
                available=bragg_available,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='excluded',
                description=_PATTERN_OPTION_DESCRIPTIONS['excluded'],
                available=has_excluded_regions,
                auto_included=False,
                reason='',
            ),
            PatternOptionStatus(
                name='uncertainty',
                description=_PATTERN_OPTION_DESCRIPTIONS['uncertainty'],
                available=uncertainty_available,
                auto_included=False,
                reason='',
            ),
        ])

        return [
            PatternOptionStatus(
                name='auto',
                description=_PATTERN_OPTION_DESCRIPTIONS['auto'],
                available=bool(auto_include),
                auto_included=True,
                reason='' if auto_include else 'No supported pattern content is available.',
            ),
            PatternOptionStatus(
                name='measured',
                description=_PATTERN_OPTION_DESCRIPTIONS['measured'],
                available=measured_available,
                auto_included='measured' in auto_include,
                reason='' if measured_available else 'Measured intensities are unavailable.',
            ),
            PatternOptionStatus(
                name='calculated',
                description=_PATTERN_OPTION_DESCRIPTIONS['calculated'],
                available=calculated_available,
                auto_included='calculated' in auto_include,
                reason='' if calculated_available else 'Calculated intensities are unavailable.',
            ),
            PatternOptionStatus(
                name='background',
                description=_PATTERN_OPTION_DESCRIPTIONS['background'],
                available=background_available,
                auto_included='background' in auto_include,
                reason=''
                if background_available
                else (
                    'Background display currently requires powder Bragg '
                    'measured and calculated data plus defined '
                    'background points.'
                ),
            ),
            PatternOptionStatus(
                name='residual',
                description=_PATTERN_OPTION_DESCRIPTIONS['residual'],
                available=residual_available,
                auto_included='residual' in auto_include,
                reason=''
                if residual_available
                else ('Residuals currently require powder measured and calculated data.'),
            ),
            PatternOptionStatus(
                name='bragg',
                description=_PATTERN_OPTION_DESCRIPTIONS['bragg'],
                available=bragg_available,
                auto_included='bragg' in auto_include,
                reason=''
                if bragg_available
                else (
                    'Bragg tick marks require powder Bragg measured and '
                    'calculated data with reflection rows.'
                ),
            ),
            PatternOptionStatus(
                name='excluded',
                description=_PATTERN_OPTION_DESCRIPTIONS['excluded'],
                available=has_excluded_regions,
                auto_included='excluded' in auto_include,
                reason=''
                if has_excluded_regions
                else ('No excluded regions are defined for this experiment.'),
            ),
            PatternOptionStatus(
                name='uncertainty',
                description=_PATTERN_OPTION_DESCRIPTIONS['uncertainty'],
                available=uncertainty_available,
                auto_included='uncertainty' in auto_include,
                reason=uncertainty_reason,
            ),
        ]

    @staticmethod
    def _has_nonempty_value(value: object | None) -> bool:
        """Return whether a plotting input has content."""
        if value is None:
            return False

        try:
            return len(value) > 0
        except TypeError:
            return True

    def _has_linked_structure_for_calculation(self, experiment: object) -> bool:
        """Return whether the experiment links to a known structure."""
        structure_names = set(getattr(self._project.structures, 'names', ()))

        linked_phases = getattr(experiment, 'linked_phases', None)
        if self._has_nonempty_value(linked_phases):
            for linked_phase in linked_phases:
                identity = getattr(linked_phase, '_identity', None)
                category_entry_name = getattr(identity, 'category_entry_name', None)
                if category_entry_name in structure_names:
                    return True

        linked_crystal = getattr(experiment, 'linked_crystal', None)
        linked_crystal_id = getattr(getattr(linked_crystal, 'id', None), 'value', None)
        return linked_crystal_id in structure_names

    def _uncertainty_status(
        self,
        *,
        measured_available: bool,
        sample_form: str,
        scattering_type: str,
    ) -> tuple[bool, str]:
        """
        Return whether posterior predictive uncertainty is available.
        """
        if not measured_available:
            return False, 'Uncertainty bands require measured data.'

        supported_sample_form = sample_form == SampleFormEnum.POWDER.value or (
            sample_form == SampleFormEnum.SINGLE_CRYSTAL.value
            and scattering_type == ScatteringTypeEnum.BRAGG.value
        )
        if not supported_sample_form:
            return (
                False,
                ('Posterior predictive pattern views are unavailable for this experiment type.'),
            )

        fit_results = getattr(self._project.analysis, 'fit_results', None)
        if fit_results is None:
            return False, 'No fit results are available.'

        posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
        if not posterior_predictive:
            return False, 'Posterior predictive data is unavailable.'

        active_chart_engine = getattr(self._project.rendering_plot.plotter, 'engine', None)
        if active_chart_engine is None:
            active_chart_engine = self._project.rendering_plot.type

        if active_chart_engine != PlotterEngineEnum.PLOTLY.value:
            return False, 'Uncertainty bands currently require the Plotly chart engine.'

        return True, ''
