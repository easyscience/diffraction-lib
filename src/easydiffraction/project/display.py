# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project display facade grouping charts and reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.display.plotting import PlotterEngineEnum
from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum
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


class FitDisplay:
    """Fit-report namespace under ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project

    def results(self) -> None:
        """Show the latest fit summary and fitted parameter table."""
        self._project.analysis.display.fit_results()

    def correlations(
        self,
        threshold: float | None = None,
        precision: int = 2,
        *,
        max_parameters: int = 6,
        show_diagonal: bool = True,
    ) -> None:
        """Show parameter correlations from the latest fit."""
        self._project.rendering.plotter.plot_param_correlations(
            threshold=threshold,
            precision=precision,
            max_parameters=max_parameters,
            show_diagonal=show_diagonal,
        )

    def series(
        self,
        param: object,
        versus: object | None = None,
    ) -> None:
        """Plot one fitted parameter across sequential results."""
        self._project.rendering.plotter.plot_param_series(param=param, versus=versus)


class PosteriorDisplay:
    """Posterior-plot namespace under ``project.display``."""

    def __init__(self, project: Project) -> None:
        self._project = project

    def pairs(
        self,
        parameters: list[object] | None = None,
        style: PosteriorPairPlotStyleEnum | str = PosteriorPairPlotStyleEnum.AUTO,
        *,
        threshold: float | None = None,
        max_parameters: int = 6,
    ) -> None:
        """Plot posterior pair relationships for sampled parameters."""
        self._project.rendering.plotter.plot_posterior_pairs(
            parameters=parameters,
            style=style,
            threshold=threshold,
            max_parameters=max_parameters,
        )

    def distribution(self, param: object) -> None:
        """Plot one sampled parameter's posterior distribution."""
        self._project.rendering.plotter.plot_param_distribution(param)

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
        self._project.rendering.plotter.plot_posterior_predictive(
            expt_name=expt_name,
            style=style,
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            x=x,
        )


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

        if normalized_include == ('auto',):
            auto_options = self._pattern_option_statuses(expt_name)
            if self._status_by_name(auto_options, 'uncertainty').available:
                self.posterior.predictive(
                    expt_name=expt_name,
                    style='band',
                    x_min=x_min,
                    x_max=x_max,
                    x=x,
                )
                return
            self._show_point_estimate_pattern(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                include=('measured', 'calculated'),
                x=x,
            )
            return

        if normalized_include == ('measured',):
            self._project.rendering.plotter.plot_meas(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
            )
            return

        if normalized_include == ('calculated',):
            self._project.rendering.plotter.plot_calc(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
            )
            return

        if 'uncertainty' in normalized_include:
            self.posterior.predictive(
                expt_name=expt_name,
                style='band',
                x_min=x_min,
                x_max=x_max,
                show_residual=True if 'residual' in normalized_include else None,
                x=x,
            )
            return

        self._show_point_estimate_pattern(
            expt_name=expt_name,
            x_min=x_min,
            x_max=x_max,
            include=normalized_include,
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

    def _show_point_estimate_pattern(
        self,
        *,
        expt_name: str,
        x_min: float | None,
        x_max: float | None,
        include: tuple[str, ...],
        x: object | None,
    ) -> None:
        """Dispatch a point-estimate pattern view to the live plotter."""
        include_set = set(include)
        if include_set == {'measured'}:
            self._project.rendering.plotter.plot_meas(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
            )
            return
        if include_set == {'calculated'}:
            self._project.rendering.plotter.plot_calc(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                x=x,
            )
            return
        if {'measured', 'calculated'}.issubset(include_set):
            self._project.rendering.plotter.plot_meas_vs_calc(
                expt_name=expt_name,
                x_min=x_min,
                x_max=x_max,
                show_residual='residual' in include_set,
                x=x,
            )
            return

        msg = (
            'Point-estimate pattern views currently support include values '
            "'measured', 'calculated', or combinations containing both."
        )
        raise ValueError(msg)

    def _pattern_option_statuses(self, expt_name: str) -> list[PatternOptionStatus]:
        """Return availability details for the requested experiment."""
        experiment = self._project.experiments[expt_name]
        pattern = intensity_category_for(experiment)
        sample_form = experiment.type.sample_form.value
        scattering_type = experiment.type.scattering_type.value

        measured_available = getattr(pattern, 'intensity_meas', None) is not None
        calculated_available = getattr(pattern, 'intensity_calc', None) is not None
        background_available = getattr(pattern, 'intensity_bkg', None) is not None
        bragg_available = (
            sample_form == SampleFormEnum.POWDER.value
            and scattering_type == ScatteringTypeEnum.BRAGG.value
            and getattr(experiment, 'refln', None) is not None
        )
        residual_available = (
            sample_form == SampleFormEnum.POWDER.value
            and measured_available
            and calculated_available
        )
        excluded_regions = getattr(experiment, 'excluded_regions', None)
        excluded_available = excluded_regions is not None and len(excluded_regions) > 0
        uncertainty_available, uncertainty_reason = self._uncertainty_status()

        auto_uses_uncertainty = uncertainty_available
        auto_measured = measured_available
        auto_calculated = calculated_available
        auto_background = background_available and calculated_available
        auto_residual = residual_available
        auto_bragg = bragg_available and measured_available and calculated_available

        return [
            PatternOptionStatus(
                name='auto',
                description=_PATTERN_OPTION_DESCRIPTIONS['auto'],
                available=measured_available or calculated_available or uncertainty_available,
                auto_included=True,
                reason='' if measured_available or calculated_available or uncertainty_available else (
                    'No measured, calculated, or posterior predictive data is available.'
                ),
            ),
            PatternOptionStatus(
                name='measured',
                description=_PATTERN_OPTION_DESCRIPTIONS['measured'],
                available=measured_available,
                auto_included=auto_measured,
                reason='' if measured_available else 'Measured intensities are unavailable.',
            ),
            PatternOptionStatus(
                name='calculated',
                description=_PATTERN_OPTION_DESCRIPTIONS['calculated'],
                available=calculated_available,
                auto_included=auto_calculated,
                reason='' if calculated_available else 'Calculated intensities are unavailable.',
            ),
            PatternOptionStatus(
                name='background',
                description=_PATTERN_OPTION_DESCRIPTIONS['background'],
                available=background_available,
                auto_included=auto_background,
                reason='' if background_available else 'Background intensities are unavailable.',
            ),
            PatternOptionStatus(
                name='residual',
                description=_PATTERN_OPTION_DESCRIPTIONS['residual'],
                available=residual_available,
                auto_included=auto_residual,
                reason='' if residual_available else 'Residuals currently require powder measured and calculated data.',
            ),
            PatternOptionStatus(
                name='bragg',
                description=_PATTERN_OPTION_DESCRIPTIONS['bragg'],
                available=bragg_available,
                auto_included=auto_bragg,
                reason='' if bragg_available else 'Bragg tick marks require powder Bragg reflection data.',
            ),
            PatternOptionStatus(
                name='excluded',
                description=_PATTERN_OPTION_DESCRIPTIONS['excluded'],
                available=excluded_available,
                auto_included=False,
                reason='' if excluded_available else 'No excluded regions are defined for this experiment.',
            ),
            PatternOptionStatus(
                name='uncertainty',
                description=_PATTERN_OPTION_DESCRIPTIONS['uncertainty'],
                available=uncertainty_available,
                auto_included=auto_uses_uncertainty,
                reason=uncertainty_reason,
            ),
        ]

    def _uncertainty_status(self) -> tuple[bool, str]:
        """Return whether posterior predictive uncertainty is available."""
        fit_results = getattr(self._project.analysis, 'fit_results', None)
        if fit_results is None:
            return False, 'No fit results are available.'

        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
        if posterior_samples is None or posterior_predictive is None:
            return False, 'Posterior predictive data is unavailable.'

        if self._project.rendering.chart_engine.value != PlotterEngineEnum.PLOTLY.value:
            return False, 'Uncertainty bands currently require the Plotly chart engine.'

        return True, ''