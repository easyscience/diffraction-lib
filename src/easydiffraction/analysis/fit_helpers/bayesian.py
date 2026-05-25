# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit result models and posterior data containers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from easydiffraction.analysis.fit_helpers._diagnostics import compute_ess_bulk
from easydiffraction.analysis.fit_helpers._diagnostics import compute_r_hat
from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_r_factor_squared
from easydiffraction.analysis.fit_helpers.metrics import calculate_rb_factor
from easydiffraction.analysis.fit_helpers.metrics import calculate_weighted_r_factor
from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.fit_helpers.reporting import _build_parameter_row
from easydiffraction.analysis.fit_helpers.reporting import _overall_status_row_label
from easydiffraction.core.posterior import PosteriorParameterSummary
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import print_metrics_table
from easydiffraction.utils.utils import print_table_footnote
from easydiffraction.utils.utils import render_table

R_HAT_CONVERGENCE_THRESHOLD = 1.01
ESS_BULK_CONVERGENCE_THRESHOLD = 400.0
POSTERIOR_SAMPLE_NDIM = 3
DEFAULT_CI_LEVELS = (0.68, 0.95)
DEFAULT_CREDIBLE_INTERVAL_LEVELS = DEFAULT_CI_LEVELS
IntervalLevels = tuple[float, ...]
SettingsMap = dict[str, object] | None
DiagnosticsMap = dict[str, object] | None


def posterior_predictive_cache_key(
    experiment_name: str,
    x_axis_name: str,
    *,
    include_draws: bool = True,
) -> str:
    """Return the cache key for one posterior predictive summary."""
    key_suffix = 'draws' if include_draws else 'band'
    return f'{experiment_name}:{x_axis_name}:{key_suffix}'


@dataclass(slots=True)
class PosteriorPredictiveSummary:
    """
    Posterior predictive summaries for one experiment.

    Attributes
    ----------
    experiment_name : str
        Experiment identifier.
    x_axis_name : str
        Name of the x-axis used for the predictive arrays.
    x : np.ndarray
        X-axis values for the predictive curves.
    best_sample_prediction : np.ndarray
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
    best_sample_prediction: np.ndarray
    lower_95: np.ndarray | None = None
    upper_95: np.ndarray | None = None
    lower_68: np.ndarray | None = None
    upper_68: np.ndarray | None = None
    draws: np.ndarray | None = None


@dataclass(slots=True)
class PosteriorSamples:
    """
    Posterior samples and sample statistics from a Bayesian fit.

    Attributes
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
        """
        Return flattened posterior samples by parameter.

        Returns
        -------
        np.ndarray
            Array with shape ``(n_draws * n_chains, n_parameters)``.
        """
        return np.asarray(self.parameter_samples).reshape(-1, len(self.parameter_names))

    def validate_shapes(self) -> tuple[int, int, int]:
        """
        Validate stored sample shapes and return ``(n_draws, n_chains, n_parameters)``.

        Returns
        -------
        tuple[int, int, int]
            Tuple ``(n_draws, n_chains, n_parameters)``.

        Raises
        ------
        ValueError
            If the sample array is not 3-D, the parameter axis does
            not match ``parameter_names``, or ``log_posterior`` (when
            present) does not match the first two sample axes.
        """
        posterior_array = np.asarray(self.parameter_samples, dtype=float)
        if posterior_array.ndim != POSTERIOR_SAMPLE_NDIM:
            msg = 'Posterior sample array must have shape (n_draws, n_chains, n_parameters).'
            raise ValueError(msg)

        n_draws, n_chains, n_parameters = posterior_array.shape
        if n_parameters != len(self.parameter_names):
            msg = 'Posterior sample array does not match the parameter name list length.'
            raise ValueError(msg)

        if self.log_posterior is not None:
            log_posterior = np.asarray(self.log_posterior, dtype=float)
            if log_posterior.shape != (n_draws, n_chains):
                msg = 'Log-posterior array must match the first two posterior sample axes.'
                raise ValueError(msg)

        return n_draws, n_chains, n_parameters


SummaryList = list[PosteriorParameterSummary] | None
PredictiveMap = dict[str, PosteriorPredictiveSummary] | None
ArrayPayloadMap = dict[str, dict[str, np.ndarray]] | None


@dataclass(kw_only=True)
class BayesianFitResults(FitResults):
    """
    Container for Bayesian fit results and posterior summaries.

    Attributes
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
    point_estimate_name : str, default='best_sample'
        Name of the point estimate committed back to the project.
    posterior_samples : PosteriorSamples | None, default=None
        Stored posterior samples.
    posterior_parameter_summaries : SummaryList, default=None
        Posterior summaries for each sampled parameter.
    posterior_predictive : PredictiveMap, default=None
        Posterior predictive summaries keyed by experiment name.
    posterior_distribution_caches : ArrayPayloadMap, default=None
        Cached posterior density arrays keyed by parameter name.
    posterior_pair_caches : ArrayPayloadMap, default=None
        Cached posterior pair-density arrays keyed by cache id.
    credible_interval_levels : IntervalLevels, default=DEFAULT_CI_LEVELS
        Interval levels available in the summaries.
    sampler_settings : SettingsMap, default=None
        Sampler settings recorded for reproducibility.
    convergence_diagnostics : DiagnosticsMap, default=None
        Convergence diagnostics and status metadata.
    sampler_completed : bool, default=False
        Whether the sampler completed a run and returned posterior data.
    best_log_posterior : float | None, default=None
        Best log-posterior value reported by the sampler.
    """

    success: bool = False
    parameters: list[object] | None = None
    reduced_chi_square: float | None = None
    engine_result: object | None = None
    starting_parameters: list[object] | None = None
    fitting_time: float | None = None
    sampler_name: str = 'dream'
    point_estimate_name: str = 'best_sample'
    posterior_samples: PosteriorSamples | None = None
    posterior_parameter_summaries: SummaryList = None
    posterior_predictive: PredictiveMap = None
    posterior_distribution_caches: ArrayPayloadMap = None
    posterior_pair_caches: ArrayPayloadMap = None
    credible_interval_levels: IntervalLevels = DEFAULT_CI_LEVELS
    sampler_settings: SettingsMap = None
    convergence_diagnostics: DiagnosticsMap = None
    sampler_completed: bool = False
    best_log_posterior: float | None = None

    def __post_init__(self) -> None:
        """
        Initialize inherited FitResults state and normalize containers.
        """
        super().__init__(
            success=self.success,
            parameters=self.parameters,
            reduced_chi_square=self.reduced_chi_square,
            engine_result=self.engine_result,
            starting_parameters=self.starting_parameters,
            fitting_time=self.fitting_time,
        )
        self.posterior_parameter_summaries = (
            list(self.posterior_parameter_summaries)
            if self.posterior_parameter_summaries is not None
            else []
        )
        self.posterior_predictive = (
            dict(self.posterior_predictive) if self.posterior_predictive is not None else {}
        )
        self.posterior_distribution_caches = (
            dict(self.posterior_distribution_caches)
            if self.posterior_distribution_caches is not None
            else {}
        )
        self.posterior_pair_caches = (
            dict(self.posterior_pair_caches) if self.posterior_pair_caches is not None else {}
        )
        self.sampler_settings = dict(self.sampler_settings) if self.sampler_settings else {}
        self.convergence_diagnostics = (
            dict(self.convergence_diagnostics) if self.convergence_diagnostics is not None else {}
        )

    def display_results(
        self,
        y_obs: list[float] | None = None,
        y_calc: list[float] | None = None,
        y_err: list[float] | None = None,
        f_obs: list[float] | None = None,
        f_calc: list[float] | None = None,
    ) -> None:
        """
        Render a Bayesian fit summary with posterior diagnostics.

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
        metrics = _calculate_fit_quality_metrics(
            y_obs=y_obs,
            y_calc=y_calc,
            y_err=y_err,
            f_obs=f_obs,
            f_calc=f_calc,
        )

        console.print('📋 Bayesian fit results:')
        print_metrics_table(self._build_fit_results_rows(metrics))

        console.print('📈 Committed parameters:')
        _render_committed_parameter_table(self.parameters)
        print_table_footnote(_COMMITTED_PARAMETERS_FOOTNOTE)

        console.print('📊 Posterior distribution:')
        _render_posterior_summary_table(
            parameters=self.parameters,
            posterior_parameter_summaries=self.posterior_parameter_summaries,
        )
        print_table_footnote(_POSTERIOR_DISTRIBUTION_FOOTNOTE)

        self._print_table_notes()

    def _build_fit_results_rows(self, metrics: dict[str, float | None]) -> list[list[str]]:
        """Return the rows for the 'Bayesian fit results' table."""
        overall_status = _bayesian_overall_status(
            success=self.success,
            sampler_completed=self.sampler_completed,
            convergence_diagnostics=self.convergence_diagnostics,
        )

        rows: list[list[str]] = []
        sampler_label = self.minimizer_type or self.sampler_name
        if sampler_label:
            rows.append(['🧪 Sampler', str(sampler_label)])
        rows.append([_overall_status_row_label(overall_status), overall_status])
        if self.message:
            rows.append(['💬 Engine message', self.message])
        if self.fitting_time is not None:
            rows.append(['⏱️ Fitting time (seconds)', f'{self.fitting_time:.2f}'])
        if self.reduced_chi_square is not None:
            rows.append(['📏 Goodness-of-fit (reduced χ²)', f'{self.reduced_chi_square:.2f}'])
        rf = metrics.get('rf')
        rf2 = metrics.get('rf2')
        wr = metrics.get('wr')
        br = metrics.get('br')
        if rf is not None:
            rows.append(['📏 R-factor (Rf, %)', f'{rf:.2f}'])
        if rf2 is not None:
            rows.append(['📏 R-factor squared (Rf², %)', f'{rf2:.2f}'])
        if wr is not None:
            rows.append(['📏 Weighted R-factor (wR, %)', f'{wr:.2f}'])
        if br is not None:
            rows.append(['📏 Bragg R-factor (BR, %)', f'{br:.2f}'])
        if self.best_log_posterior is not None:
            rows.append(['📉 Best log-posterior', f'{self.best_log_posterior:.2f}'])

        diagnostics = self.convergence_diagnostics or {}
        converged = diagnostics.get('converged')
        if converged is not None:
            rows.append(['📊 Convergence status', 'passed' if converged else 'failed'])
        max_r_hat = diagnostics.get('max_r_hat')
        if max_r_hat is not None:
            rows.append(['📊 Max r-hat', f'{max_r_hat:.3f}'])
        min_ess_bulk = diagnostics.get('min_ess_bulk')
        if min_ess_bulk is not None:
            rows.append(['📊 Min ess bulk', f'{min_ess_bulk:.1f}'])
        n_draws = diagnostics.get('n_draws')
        if n_draws is not None:
            rows.append(['📊 Draws per chain', str(n_draws)])
        n_chains = diagnostics.get('n_chains')
        if n_chains is not None:
            rows.append(['📊 Chains', str(n_chains)])
        return rows

    def _print_table_notes(self) -> None:
        """
        Print parameter and posterior-diagnostic notes below tables.
        """
        super()._print_table_notes()
        notes = _posterior_table_notes(self.posterior_parameter_summaries)
        if notes:
            console.small(*notes)


def compute_convergence_diagnostics(posterior_samples: PosteriorSamples) -> dict[str, object]:
    """
    Compute convergence diagnostics from posterior samples.

    Parameters
    ----------
    posterior_samples : PosteriorSamples
        Posterior samples container.

    Returns
    -------
    dict[str, object]
        Convergence metrics keyed by diagnostic name.
    """
    n_draws, n_chains, _n_parameters = posterior_samples.validate_shapes()
    parameter_samples = np.asarray(posterior_samples.parameter_samples, dtype=float)

    r_hat_by_parameter: dict[str, float | None] = {}
    ess_bulk_by_parameter: dict[str, float | None] = {}
    for index, name in enumerate(posterior_samples.parameter_names):
        per_parameter = parameter_samples[:, :, index]
        r_hat_by_parameter[name] = _maybe_scalar(compute_r_hat(per_parameter))
        ess_bulk_by_parameter[name] = _maybe_scalar(compute_ess_bulk(per_parameter))

    finite_r_hat = [value for value in r_hat_by_parameter.values() if value is not None]
    finite_ess_bulk = [value for value in ess_bulk_by_parameter.values() if value is not None]

    max_r_hat = max(finite_r_hat, default=None)
    min_ess_bulk = min(finite_ess_bulk, default=None)

    converged = len(finite_r_hat) == len(r_hat_by_parameter) and len(finite_ess_bulk) == len(
        ess_bulk_by_parameter
    )
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
        'n_draws': n_draws,
        'n_chains': n_chains,
        'n_parameters': len(posterior_samples.parameter_names),
    }


def summarize_posterior_parameters(
    parameter_names: list[str],
    posterior_samples: PosteriorSamples,
    best_sample_values: np.ndarray,
    parameter_display_names: list[str] | None = None,
    convergence_diagnostics: dict[str, object] | None = None,
) -> list[PosteriorParameterSummary]:
    """
    Build posterior parameter summaries in EasyDiffraction order.

    Parameters
    ----------
    parameter_names : list[str]
        Sampled parameter names in EasyDiffraction order.
    posterior_samples : PosteriorSamples
        Posterior sample container.
    best_sample_values : np.ndarray
        Best posterior sample values in the same order.
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
        If the posterior sample array is incompatible with the parameter
        name list.
    """
    flattened = posterior_samples.flattened()
    if flattened.shape[1] != len(parameter_names):
        msg = 'Posterior samples do not match the sampled parameter name list length.'
        raise ValueError(msg)
    if parameter_display_names is not None and len(parameter_display_names) != len(
        parameter_names
    ):
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
                best_sample_value=float(best_sample_values[index]),
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
    """
    Return posterior standard deviations in summary order.

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


def _maybe_scalar(value: object) -> float | None:
    if value is None:
        return None
    scalar = float(value)
    if not np.isfinite(scalar):
        return None
    return scalar


def _calculate_fit_quality_metrics(
    *,
    y_obs: list[float] | None,
    y_calc: list[float] | None,
    y_err: list[float] | None,
    f_obs: list[float] | None,
    f_calc: list[float] | None,
) -> dict[str, float | None]:
    """Compute optional fit-quality metrics for summary rendering."""
    metrics: dict[str, float | None] = {
        'rf': None,
        'rf2': None,
        'wr': None,
        'br': None,
    }
    if y_obs is not None and y_calc is not None:
        metrics['rf'] = calculate_r_factor(y_obs, y_calc) * 100
        metrics['rf2'] = calculate_r_factor_squared(y_obs, y_calc) * 100
    if y_obs is not None and y_calc is not None and y_err is not None:
        metrics['wr'] = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
    if f_obs is not None and f_calc is not None:
        metrics['br'] = calculate_rb_factor(f_obs, f_calc) * 100
    return metrics


def _bayesian_overall_status(
    *,
    success: bool,
    sampler_completed: bool,
    convergence_diagnostics: dict[str, object],
) -> str:
    """
    Return ``'success'`` or ``'failed'`` for the Bayesian run.

    Bayesian success requires both the sampler to have completed and
    the convergence diagnostics to have passed. Anything else is
    rendered as ``failed`` in the overall row; the per-metric
    convergence rows below carry the detail.
    """
    if not success or not sampler_completed:
        return 'failed'
    converged = convergence_diagnostics.get('converged') if convergence_diagnostics else None
    if converged is False:
        return 'failed'
    return 'success'


_COMMITTED_PARAMETERS_FOOTNOTE: list[tuple[str, str]] = [
    ('start', 'parameter value before sampling'),
    ('value', 'estimate written back to the project (best posterior sample)'),
    ('s.u.', 'standard uncertainty (1σ), the posterior standard deviation'),
    ('change', 'relative change from start, in %; ↑ = increase, ↓ = decrease'),
]

_POSTERIOR_DISTRIBUTION_FOOTNOTE: list[tuple[str, str]] = [
    ('median', '50th percentile of the marginal posterior'),
    ('95% CI', '95% credible interval (2.5%–97.5%, asymmetric)'),
    ('r-hat', 'Gelman–Rubin diagnostic R̂ (good convergence: r-hat ≤ 1.01)'),
    ('ess bulk', 'bulk effective sample size (typically ≥ 400)'),
]


def _render_committed_parameter_table(parameters: list[object]) -> None:
    headers = [
        'datablock',
        'category',
        'entry',
        'parameter',
        'units',
        'start',
        'value',
        's.u.',
        'change',
    ]
    alignments = [
        'left',
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
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
        'units',
        'median',
        '95% CI',
        'r-hat',
        'ess bulk',
    ]
    alignments = [
        'left',
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'right',
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
    parameter_name = getattr(parameter, 'name', summary.display_name)
    units = getattr(parameter, 'units', 'N/A')

    return [
        datablock,
        category,
        entry,
        parameter_name,
        units,
        f'{summary.median:.4f}',
        _format_interval(summary.interval_95),
        _format_r_hat(summary.r_hat),
        _format_ess_bulk(summary.ess_bulk),
    ]


def _format_interval(interval: tuple[float, float]) -> str:
    return f'[{interval[0]:.4f}, {interval[1]:.4f}]'


def _format_r_hat(value: float | None) -> str:
    if value is None or not np.isfinite(value):
        return 'N/A'
    formatted = f'{value:.3f}'
    if value > R_HAT_CONVERGENCE_THRESHOLD:
        return f'[red]{formatted}[/red]'
    return formatted


def _format_ess_bulk(value: float | None) -> str:
    if value is None or not np.isfinite(value):
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

    notes: list[str] = []
    if has_failed_r_hat:
        notes.append(
            f'⚠️ [red]r-hat > {R_HAT_CONVERGENCE_THRESHOLD:.2f}[/red]: '
            'Consider longer sampling, better initialization, or '
            'reparameterization.'
        )
    if has_failed_ess_bulk:
        notes.append(
            f'⚠️ [red]ess bulk < {ESS_BULK_CONVERGENCE_THRESHOLD:.0f}[/red]: '
            'Consider longer sampling or reparameterization.'
        )
    return notes
