# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit result models and posterior data containers."""

from __future__ import annotations

from dataclasses import dataclass

import arviz as az
import numpy as np

from easydiffraction.analysis.fit_helpers.reporting import FitResults

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
        summaries.append(
            PosteriorParameterSummary(
                unique_name=parameter_name,
                display_name=parameter_name,
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