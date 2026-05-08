# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit result models and posterior data containers."""

from __future__ import annotations

from dataclasses import dataclass

import arviz as az
import numpy as np

from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor_squared
from easydiffraction.analysis.fit_helpers.metrics import calculate_rb_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_weighted_r_factor
from easydiffraction.analysis.fit_helpers.reporting import _build_parameter_row
from easydiffraction.analysis.fit_helpers.reporting import _format_optional_float
from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table

R_HAT_CONVERGENCE_THRESHOLD = 1.01
ESS_BULK_CONVERGENCE_THRESHOLD = 400.0


@dataclass(slots=True)
class PosteriorParameterSummary:
    """Posterior summary statistics for one fitted parameter.

    Parameters
    ----------
    unique_name : str
        Unique parameter name used across EasyDiffraction.
    display_name : str
        Human-readable label used in plots and tables.
    map_value : float
        Maximum-a-posteriori or best-sampled parameter value.
    median : float
        Posterior median value.
    standard_deviation : float
        Posterior standard deviation.
    interval_68 : tuple[float, float]
        Central 68% interval.
    interval_95 : tuple[float, float]
        Central 95% interval.
    ess_bulk : float | None, default=None
        Bulk effective sample size when available.
    r_hat : float | None, default=None
        Rank-normalized split-$\\hat{R}$ when available.
    """

    unique_name: str
    display_name: str
    map_value: float
    median: float
    standard_deviation: float
    interval_68: tuple[float, float]
    interval_95: tuple[float, float]
    ess_bulk: float | None = None
    r_hat: float | None = None


@dataclass(slots=True)
class PosteriorPredictiveSummary:
    """Posterior predictive summaries for one experiment.

    Parameters
    ----------
    experiment_name : str
        Experiment identifier.
    x_axis_name : str
        Name of the x-axis used for the predictive arrays.
    x : np.ndarray
        X-axis values for the predictive curves.
    map_prediction : np.ndarray
        Prediction corresponding to the committed point estimate.
    lower_95 : np.ndarray | None, default=None
        Lower bound of the 95% credible interval.
    upper_95 : np.ndarray | None, default=None
        Upper bound of the 95% credible interval.
    lower_68 : np.ndarray | None, default=None
        Lower bound of the 68% credible interval.
    upper_68 : np.ndarray | None, default=None
        Upper bound of the 68% credible interval.
    draws : np.ndarray | None, default=None
        Optional capped predictive draws with shape ``(n_draws, n_x)``.
    """

    experiment_name: str
    x_axis_name: str
    x: np.ndarray
    map_prediction: np.ndarray
    lower_95: np.ndarray | None = None
    upper_95: np.ndarray | None = None
    lower_68: np.ndarray | None = None
    upper_68: np.ndarray | None = None
    draws: np.ndarray | None = None


@dataclass(slots=True)
class PosteriorSamples:
    """Posterior samples and sample statistics from a Bayesian fit.

    Parameters
    ----------
    parameter_names : list[str]
        Parameter names in the preserved EasyDiffraction order.
    parameter_samples : np.ndarray
        Sample array with shape ``(n_draws, n_chains, n_parameters)``.
    log_posterior : np.ndarray | None, default=None
        Log-posterior values with shape ``(n_draws, n_chains)`` when
        available.
    draw_index : np.ndarray | None, default=None
        Optional draw or generation indices associated with the first
        axis of ``parameter_samples``.
    """

    parameter_names: list[str]
    parameter_samples: np.ndarray
    log_posterior: np.ndarray | None = None
    draw_index: np.ndarray | None = None

    def flattened(self) -> np.ndarray:
        """Return flattened posterior samples by parameter.

        Returns
        -------
        np.ndarray
            Array with shape ``(n_draws * n_chains, n_parameters)``.
        """
        return np.asarray(self.parameter_samples).reshape(-1, len(self.parameter_names))

    def to_arviz(self) -> object:
        """Convert posterior samples to an ArviZ ``InferenceData`` object.

        Returns
        -------
        object
            ArviZ ``InferenceData`` instance built from the stored
            posterior samples.

        Raises
        ------
        ValueError
            If the stored arrays do not have the expected shapes.
        """
        import arviz as az

        posterior_array = np.asarray(self.parameter_samples, dtype=float)
        if posterior_array.ndim != 3:
            msg = 'Posterior sample array must have shape (n_draws, n_chains, n_parameters).'
            raise ValueError(msg)

        n_draws, n_chains, n_parameters = posterior_array.shape
        if n_parameters != len(self.parameter_names):
            msg = 'Posterior sample array does not match the parameter name list length.'
            raise ValueError(msg)

        posterior_dict = {
            name: np.transpose(posterior_array[:, :, index], (1, 0))
            for index, name in enumerate(self.parameter_names)
        }

        sample_stats: dict[str, np.ndarray] | None = None
        if self.log_posterior is not None:
            log_posterior = np.asarray(self.log_posterior, dtype=float)
            if log_posterior.shape != (n_draws, n_chains):
                msg = 'Log-posterior array must match the first two posterior sample axes.'
                raise ValueError(msg)
            sample_stats = {'lp': np.transpose(log_posterior, (1, 0))}

        data = {'posterior': posterior_dict}
        if sample_stats is not None:
            data['sample_stats'] = sample_stats

        return az.from_dict(data)


class BayesianFitResults(FitResults):
    """Container for Bayesian fit results and posterior summaries.

    Parameters
    ----------
    success : bool, default=False
        Whether the Bayesian fit produced usable posterior results.
    parameters : list[object] | None, default=None
        Final committed parameter objects.
    reduced_chi_square : float | None, default=None
        Reduced chi-square evaluated at the committed point estimate.
    engine_result : object | None, default=None
        Opaque backend result object.
    starting_parameters : list[object] | None, default=None
        Starting parameter objects or snapshots.
    fitting_time : float | None, default=None
        Total fitting time in seconds.
    sampler_name : str, default='dream'
        Sampler identifier.
    point_estimate_name : str, default='map'
        Name of the point estimate committed back to the project.
    posterior_samples : PosteriorSamples | None, default=None
        Stored posterior samples.
    posterior_parameter_summaries : list[PosteriorParameterSummary] | None, default=None
        Posterior summaries for each sampled parameter.
    posterior_predictive : dict[str, PosteriorPredictiveSummary] | None, default=None
        Posterior predictive summaries keyed by experiment name.
    credible_interval_levels : tuple[float, ...], default=(0.68, 0.95)
        Interval levels available in the summaries.
    sampler_settings : dict[str, object] | None, default=None
        Sampler settings recorded for reproducibility.
    convergence_diagnostics : dict[str, object] | None, default=None
        Convergence diagnostics and status metadata.
    sampler_completed : bool, default=False
        Whether the sampler completed a run and returned posterior data.
    best_log_posterior : float | None, default=None
        Best log-posterior value reported by the sampler.
    """

    def __init__(
        self,
        *,
        success: bool = False,
        parameters: list[object] | None = None,
        reduced_chi_square: float | None = None,
        engine_result: object | None = None,
        starting_parameters: list[object] | None = None,
        fitting_time: float | None = None,
        sampler_name: str = 'dream',
        point_estimate_name: str = 'map',
        posterior_samples: PosteriorSamples | None = None,
        posterior_parameter_summaries: list[PosteriorParameterSummary] | None = None,
        posterior_predictive: dict[str, PosteriorPredictiveSummary] | None = None,
        credible_interval_levels: tuple[float, ...] = (0.68, 0.95),
        sampler_settings: dict[str, object] | None = None,
        convergence_diagnostics: dict[str, object] | None = None,
        sampler_completed: bool = False,
        best_log_posterior: float | None = None,
    ) -> None:
        super().__init__(
            success=success,
            parameters=parameters,
            reduced_chi_square=reduced_chi_square,
            engine_result=engine_result,
            starting_parameters=starting_parameters,
            fitting_time=fitting_time,
        )
        self.sampler_name = sampler_name
        self.point_estimate_name = point_estimate_name
        self.posterior_samples = posterior_samples
        self.posterior_parameter_summaries = (
            posterior_parameter_summaries if posterior_parameter_summaries is not None else []
        )
        self.posterior_predictive = (
            posterior_predictive if posterior_predictive is not None else {}
        )
        self.credible_interval_levels = credible_interval_levels
        self.sampler_settings = sampler_settings if sampler_settings is not None else {}
        self.convergence_diagnostics = (
            convergence_diagnostics if convergence_diagnostics is not None else {}
        )
        self.sampler_completed = sampler_completed
        self.best_log_posterior = best_log_posterior

    def display_results(
        self,
        y_obs: list[float] | None = None,
        y_calc: list[float] | None = None,
        y_err: list[float] | None = None,
        f_obs: list[float] | None = None,
        f_calc: list[float] | None = None,
    ) -> None:
        """Render a Bayesian fit summary with posterior diagnostics.

        Parameters
        ----------
        y_obs : list[float] | None, default=None
            Observed intensities for pattern R-factor metrics.
        y_calc : list[float] | None, default=None
            Calculated intensities for pattern R-factor metrics.
        y_err : list[float] | None, default=None
            Standard deviations of observed intensities for wR.
        f_obs : list[float] | None, default=None
            Observed structure-factor magnitudes for Bragg R.
        f_calc : list[float] | None, default=None
            Calculated structure-factor magnitudes for Bragg R.
        """
        status_icon = '✅' if self.success else '❌'
        rf = rf2 = wr = br = None
        if y_obs is not None and y_calc is not None:
            rf = calculate_r_factor(y_obs, y_calc) * 100
            rf2 = calculate_r_factor_squared(y_obs, y_calc) * 100
        if y_obs is not None and y_calc is not None and y_err is not None:
            wr = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
        if f_obs is not None and f_calc is not None:
            br = calculate_rb_factor(f_obs, f_calc) * 100

        console.paragraph('Bayesian fit results')
        console.print(f'{status_icon} Success: {self.success}')
        if self.message:
            console.print(f'ℹ️ Status: {self.message}')
        console.print(f'🧪 Sampler: {self.sampler_name}')
        console.print(
            f'🎯 Committed point estimate: {_format_point_estimate_name(self.point_estimate_name)}'
        )
        console.print(f'🔁 Sampler completed: {self.sampler_completed}')
        console.print(f'⏱️ Fitting time: {_format_optional_float(self.fitting_time, suffix=" seconds")}')
        console.print(
            '📏 Goodness-of-fit (reduced χ²): '
            f'{_format_optional_float(self.reduced_chi_square)}'
        )
        if self.best_log_posterior is not None:
            console.print(f'📉 Best log-posterior: {self.best_log_posterior:.2f}')

        sampler_settings = _format_sampler_settings(self.sampler_settings)
        if sampler_settings is not None:
            console.print(f'⚙️ Sampler settings: {sampler_settings}')

        convergence_summary = _format_convergence_summary(self.convergence_diagnostics)
        if convergence_summary is not None:
            console.print(f'📊 Convergence: {convergence_summary}')

        if rf is not None:
            console.print(f'📏 R-factor (Rf): {rf:.2f}%')
        if rf2 is not None:
            console.print(f'📏 R-factor squared (Rf²): {rf2:.2f}%')
        if wr is not None:
            console.print(f'📏 Weighted R-factor (wR): {wr:.2f}%')
        if br is not None:
            console.print(f'📏 Bragg R-factor (BR): {br:.2f}%')

        console.print('📈 Committed parameters:')
        _render_committed_parameter_table(self.parameters)

        console.print('📊 Posterior parameter summaries:')
        _render_posterior_summary_table(
            parameters=self.parameters,
            posterior_parameter_summaries=self.posterior_parameter_summaries,
        )

        self._print_table_notes()

    def _print_table_notes(self) -> None:
        """Print parameter and posterior-diagnostic notes below tables."""
        super()._print_table_notes()
        for note in _posterior_table_notes(self.posterior_parameter_summaries):
            log.warning(note)


def compute_convergence_diagnostics(posterior_samples: PosteriorSamples) -> dict[str, object]:
    """Compute convergence diagnostics from posterior samples.

    Parameters
    ----------
    posterior_samples : PosteriorSamples
        Posterior samples container.

    Returns
    -------
    dict[str, object]
        Convergence metrics keyed by diagnostic name.
    """
    inference_data = posterior_samples.to_arviz()
    rhat_dataset = az.rhat(inference_data)
    ess_dataset = az.ess(inference_data, method='bulk')

    r_hat_by_parameter = _dataset_to_scalar_dict(rhat_dataset)
    ess_bulk_by_parameter = _dataset_to_scalar_dict(ess_dataset)

    max_r_hat = max(r_hat_by_parameter.values(), default=None)
    min_ess_bulk = min(ess_bulk_by_parameter.values(), default=None)

    converged = True
    if max_r_hat is not None and max_r_hat > R_HAT_CONVERGENCE_THRESHOLD:
        converged = False
    if min_ess_bulk is not None and min_ess_bulk < ESS_BULK_CONVERGENCE_THRESHOLD:
        converged = False

    return {
        'converged': converged,
        'r_hat_by_parameter': r_hat_by_parameter,
        'ess_bulk_by_parameter': ess_bulk_by_parameter,
        'max_r_hat': max_r_hat,
        'min_ess_bulk': min_ess_bulk,
        'n_draws': int(posterior_samples.parameter_samples.shape[0]),
        'n_chains': int(posterior_samples.parameter_samples.shape[1]),
        'n_parameters': len(posterior_samples.parameter_names),
    }


def summarize_posterior_parameters(
    parameter_names: list[str],
    posterior_samples: PosteriorSamples,
    map_values: np.ndarray,
    parameter_display_names: list[str] | None = None,
    convergence_diagnostics: dict[str, object] | None = None,
) -> list[PosteriorParameterSummary]:
    """Build posterior parameter summaries in EasyDiffraction order.

    Parameters
    ----------
    parameter_names : list[str]
        Sampled parameter names in EasyDiffraction order.
    posterior_samples : PosteriorSamples
        Posterior sample container.
    map_values : np.ndarray
        MAP or best-sampled parameter values in the same order.
    parameter_display_names : list[str] | None, default=None
        Human-readable parameter names in the same order.
    convergence_diagnostics : dict[str, object] | None, default=None
        Optional convergence diagnostics keyed by parameter name.

    Returns
    -------
    list[PosteriorParameterSummary]
        Summary rows matching the input parameter order.

    Raises
    ------
    ValueError
        If the posterior sample array is incompatible with the
        parameter name list.
    """
    flattened = posterior_samples.flattened()
    if flattened.shape[1] != len(parameter_names):
        msg = 'Posterior samples do not match the sampled parameter name list length.'
        raise ValueError(msg)
    if parameter_display_names is not None and len(parameter_display_names) != len(parameter_names):
        msg = 'Posterior display-name list must match the sampled parameter name list length.'
        raise ValueError(msg)

    r_hat_by_parameter = {}
    ess_bulk_by_parameter = {}
    if convergence_diagnostics is not None:
        r_hat_by_parameter = convergence_diagnostics.get('r_hat_by_parameter', {})
        ess_bulk_by_parameter = convergence_diagnostics.get('ess_bulk_by_parameter', {})

    summaries: list[PosteriorParameterSummary] = []
    for index, parameter_name in enumerate(parameter_names):
        values = flattened[:, index]
        interval_68 = tuple(np.quantile(values, [0.16, 0.84]).tolist())
        interval_95 = tuple(np.quantile(values, [0.025, 0.975]).tolist())
        display_name = (
            parameter_display_names[index]
            if parameter_display_names is not None
            else parameter_name
        )
        summaries.append(
            PosteriorParameterSummary(
                unique_name=parameter_name,
                display_name=display_name,
                map_value=float(map_values[index]),
                median=float(np.median(values)),
                standard_deviation=float(np.std(values, ddof=1)),
                interval_68=(float(interval_68[0]), float(interval_68[1])),
                interval_95=(float(interval_95[0]), float(interval_95[1])),
                ess_bulk=_maybe_scalar(ess_bulk_by_parameter.get(parameter_name)),
                r_hat=_maybe_scalar(r_hat_by_parameter.get(parameter_name)),
            )
        )

    return summaries


def standard_deviations_from_summaries(
    summaries: list[PosteriorParameterSummary],
) -> np.ndarray:
    """Return posterior standard deviations in summary order.

    Parameters
    ----------
    summaries : list[PosteriorParameterSummary]
        Posterior summaries in parameter order.

    Returns
    -------
    np.ndarray
        Standard deviations in the same order.
    """
    return np.array([summary.standard_deviation for summary in summaries], dtype=float)


def _dataset_to_scalar_dict(dataset: object) -> dict[str, float]:
    values: dict[str, float] = {}
    for name, data_array in dataset.data_vars.items():
        values[name] = float(np.asarray(data_array).reshape(-1)[0])
    return values


def _maybe_scalar(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _format_sampler_settings(sampler_settings: dict[str, object]) -> str | None:
    if not sampler_settings:
        return None

    parts: list[str] = []
    for key in ('random_seed', 'steps', 'burn', 'thin', 'pop', 'samples'):
        if key in sampler_settings:
            parts.append(f'{key}={sampler_settings[key]}')
    return ', '.join(parts) if parts else None


def _format_point_estimate_name(point_estimate_name: str) -> str:
    """Return a user-facing label for the committed point estimate."""
    normalized_name = point_estimate_name.strip().lower().replace('_', ' ')
    if normalized_name == 'map':
        return 'Max posterior'
    return point_estimate_name.replace('_', ' ').title()


def _format_convergence_summary(convergence_diagnostics: dict[str, object]) -> str | None:
    if not convergence_diagnostics:
        return None

    parts: list[str] = []
    converged = convergence_diagnostics.get('converged')
    if converged is not None:
        status = 'yes' if converged else '[red]failed[/red]'
        parts.append(f'converged={status}')

    max_r_hat = _maybe_scalar(convergence_diagnostics.get('max_r_hat'))
    if max_r_hat is not None:
        parts.append(f'max_r_hat={_format_r_hat(max_r_hat)}')

    min_ess_bulk = _maybe_scalar(convergence_diagnostics.get('min_ess_bulk'))
    if min_ess_bulk is not None:
        parts.append(f'min_ess_bulk={_format_ess_bulk(min_ess_bulk)}')

    n_draws = convergence_diagnostics.get('n_draws')
    n_chains = convergence_diagnostics.get('n_chains')
    if n_draws is not None and n_chains is not None:
        parts.append(f'draws={n_draws}, chains={n_chains}')

    return ', '.join(parts) if parts else None


def _render_committed_parameter_table(parameters: list[object]) -> None:
    headers = [
        'datablock',
        'category',
        'entry',
        'parameter',
        'start',
        'max posterior',
        'uncertainty',
        'units',
        'change',
    ]
    alignments = [
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'left',
        'right',
    ]
    rows = [_build_parameter_row(parameter) for parameter in parameters]
    render_table(
        columns_headers=headers,
        columns_alignment=alignments,
        columns_data=rows,
    )


def _render_posterior_summary_table(
    *,
    parameters: list[object],
    posterior_parameter_summaries: list[PosteriorParameterSummary],
) -> None:
    if not posterior_parameter_summaries:
        console.print('No posterior parameter summaries available.')
        return

    parameters_by_name = {parameter.unique_name: parameter for parameter in parameters}
    headers = [
        'datablock',
        'category',
        'entry',
        'parameter',
        'median',
        'std',
        '68% interval',
        '95% interval',
        'r_hat',
        'ess_bulk',
        'units',
    ]
    alignments = [
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'right',
        'right',
        'right',
        'left',
    ]
    rows = [
        _build_posterior_summary_row(summary, parameters_by_name)
        for summary in posterior_parameter_summaries
    ]
    render_table(
        columns_headers=headers,
        columns_alignment=alignments,
        columns_data=rows,
    )


def _build_posterior_summary_row(
    summary: PosteriorParameterSummary,
    parameters_by_name: dict[str, object],
) -> list[str]:
    parameter = parameters_by_name.get(summary.unique_name)
    identity = getattr(parameter, '_identity', None)
    datablock = getattr(identity, 'datablock_entry_name', 'N/A')
    category = getattr(identity, 'category_code', 'N/A')
    entry = getattr(identity, 'category_entry_name', '') or ''
    units = getattr(parameter, 'units', 'N/A')

    return [
        datablock,
        category,
        entry,
        summary.display_name,
        f'{summary.median:.4f}',
        f'{summary.standard_deviation:.4f}',
        _format_interval(summary.interval_68),
        _format_interval(summary.interval_95),
        _format_r_hat(summary.r_hat),
        _format_ess_bulk(summary.ess_bulk),
        units,
    ]


def _format_interval(interval: tuple[float, float]) -> str:
    return f'[{interval[0]:.4f}, {interval[1]:.4f}]'


def _format_r_hat(value: float | None) -> str:
    if value is None:
        return 'N/A'
    formatted = f'{value:.3f}'
    if value > R_HAT_CONVERGENCE_THRESHOLD:
        return f'[red]{formatted}[/red]'
    return formatted


def _format_ess_bulk(value: float | None) -> str:
    if value is None:
        return 'N/A'
    formatted = f'{value:.1f}'
    if value < ESS_BULK_CONVERGENCE_THRESHOLD:
        return f'[red]{formatted}[/red]'
    return formatted


def _posterior_table_notes(
    posterior_parameter_summaries: list[PosteriorParameterSummary],
) -> list[str]:
    """Return warning notes for posterior summary diagnostics."""
    if not posterior_parameter_summaries:
        return []

    has_failed_r_hat = any(
        summary.r_hat is not None and summary.r_hat > R_HAT_CONVERGENCE_THRESHOLD
        for summary in posterior_parameter_summaries
    )
    has_failed_ess_bulk = any(
        summary.ess_bulk is not None and summary.ess_bulk < ESS_BULK_CONVERGENCE_THRESHOLD
        for summary in posterior_parameter_summaries
    )

    if not has_failed_r_hat and not has_failed_ess_bulk:
        return []

    return [
        '[red]Convergence warning:[/red] posterior diagnostics failed '
        '(r_hat > 1.01 or ess_bulk < 400). Consider longer sampling, '
        'tighter bounds, or reparameterization.'
    ]