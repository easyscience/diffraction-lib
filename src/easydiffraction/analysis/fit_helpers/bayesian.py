# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit result models and posterior data containers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from easydiffraction.analysis.fit_helpers.reporting import FitResults


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
        Rank-normalized split-$\hat{R}$ when available.
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

        return az.from_dict(posterior=posterior_dict, sample_stats=sample_stats)


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