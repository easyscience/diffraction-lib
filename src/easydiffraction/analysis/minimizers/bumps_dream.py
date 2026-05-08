# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bumps minimizer variant using the DREAM sampler."""

from __future__ import annotations

import random

import numpy as np
from bumps.fitproblem import FitProblem
from bumps.fitters import FITTERS
from bumps.fitters import FitDriver
from bumps.fitters import monitor as bumps_monitor
from scipy.optimize import OptimizeResult

from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
from easydiffraction.analysis.fit_helpers.bayesian import compute_convergence_diagnostics
from easydiffraction.analysis.fit_helpers.bayesian import standard_deviations_from_summaries
from easydiffraction.analysis.fit_helpers.bayesian import summarize_posterior_parameters
from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness
from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.utils.logging import log

DEFAULT_METHOD = 'dream'
DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_BURN_FRACTION = 0.2
DEFAULT_MIN_BURN = 50
DEFAULT_THIN = 1
DEFAULT_POP = 4
DEFAULT_ALPHA = 0.0
DEFAULT_OUTLIER_TEST = 'none'
DEFAULT_TRIM = False


class _DreamProgressMonitor(bumps_monitor.Monitor):
    """Progress monitor translating DREAM updates into chi-square rows."""

    def __init__(
        self,
        *,
        tracker: object,
        n_points: int,
        n_parameters: int,
        total_generations: int,
        burn_steps: int,
    ) -> None:
        self._tracker = tracker
        self._n_points = n_points
        self._n_parameters = n_parameters
        self._total_generations = max(1, total_generations)
        self._burn_steps = max(0, burn_steps)

    def config_history(self, history: object) -> None:
        """Declare the history fields needed for progress updates."""
        history.requires(time=1, step=1, value=1, population_values=1)

    def __call__(self, history: object) -> None:
        """Forward sampler progress to the shared fit tracker."""
        step = int(history.step[0]) if history.step else 0
        generation = max(1, step)
        nllf = float(history.value[0])
        reduced_chi2 = self._reduced_chi_square_from_nllf(nllf)
        log_posterior = self._population_mean_log_posterior(history)
        self._tracker.track_sampler_progress(
            iteration=generation,
            total_iterations=self._total_generations,
            phase=self._phase_name(generation),
            progress_percent=self._progress_percent(generation),
            log_posterior=log_posterior,
            reduced_chi2=reduced_chi2,
            elapsed_time=float(history.time[0]),
        )

    def final(self, history: object, best: dict[str, object]) -> None:
        """Record the final DREAM state in the shared fit tracker."""
        if not history.time or best.get('value') is None:
            return
        step = int(history.step[0]) if history.step else 0
        generation = max(1, step)
        best_nllf = float(best['value'])
        reduced_chi2 = self._reduced_chi_square_from_nllf(best_nllf)
        self._tracker.track_sampler_progress(
            iteration=generation,
            total_iterations=self._total_generations,
            phase=self._phase_name(generation),
            progress_percent=self._progress_percent(generation),
            log_posterior=self._population_mean_log_posterior(history),
            reduced_chi2=reduced_chi2,
            elapsed_time=float(history.time[0]),
        )

    def _phase_name(self, generation: int) -> str:
        """Return the current sampler phase name."""
        clamped_generation = min(generation, self._total_generations)
        if clamped_generation <= self._burn_steps:
            return 'burn-in'
        return 'sampling'

    def _progress_percent(self, generation: int) -> float:
        """Return DREAM progress as a percentage."""
        clamped_generation = min(generation, self._total_generations)
        return 100.0 * clamped_generation / self._total_generations

    @staticmethod
    def _population_mean_log_posterior(history: object) -> float:
        """Return the current mean log-posterior across the walker population."""
        population_values = history.population_values[0] if history.population_values else None
        if population_values is None:
            return -float(history.value[0])

        nllf_values = np.asarray(population_values, dtype=float)
        finite_mask = np.isfinite(nllf_values)
        if not np.any(finite_mask):
            return -float(history.value[0])
        return float(np.mean(-nllf_values[finite_mask]))

    def _reduced_chi_square_from_nllf(self, nllf: float) -> float:
        """Convert DREAM's negative log-likelihood to reduced chi-square."""
        dof = self._n_points - self._n_parameters
        chi_square = 2.0 * nllf
        if dof <= 0:
            return chi_square
        return chi_square / dof


@MinimizerFactory.register
class BumpsDreamMinimizer(BumpsMinimizer):
    """Bumps minimizer using the DREAM Bayesian sampler."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_DREAM,
        description='Bumps library with DREAM Bayesian sampling',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS_DREAM,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
        self._burn: int | None = None
        self._thin: int = DEFAULT_THIN
        self._pop: int = DEFAULT_POP

    @property
    def steps(self) -> int:
        """Number of DREAM generations retained after burn-in."""
        return self._validated_positive_integer('steps', self.max_iterations)

    @steps.setter
    def steps(self, value: int) -> None:
        self.max_iterations = self._validated_positive_integer('steps', value)

    @property
    def burn(self) -> int | None:
        """Explicit DREAM burn-in generations or ``None`` for auto."""
        return self._burn

    @burn.setter
    def burn(self, value: int | None) -> None:
        if value is None:
            self._burn = None
            return
        self._burn = self._validated_non_negative_integer('burn', value)

    @property
    def thin(self) -> int:
        """DREAM thinning interval."""
        return self._thin

    @thin.setter
    def thin(self, value: int) -> None:
        self._thin = self._validated_positive_integer('thin', value)

    @property
    def pop(self) -> int:
        """DREAM population multiplier."""
        return self._pop

    @pop.setter
    def pop(self, value: int) -> None:
        self._pop = self._validated_positive_integer('pop', value)

    def _resolve_random_seed(self, random_seed: int | None) -> int:
        """Return a user-provided or generated random seed.

        Parameters
        ----------
        random_seed : int | None
            User-provided random seed.

        Returns
        -------
        int
            Seed to use for the DREAM run.
        """
        if random_seed is None:
            generator = np.random.default_rng()
            random_seed = int(generator.integers(0, np.iinfo(np.int32).max))

        self._resolved_random_seed = int(random_seed)
        return self._resolved_random_seed

    def _tracking_mode(self) -> str:
        """Use sampler-style progress reporting for DREAM runs."""
        return 'sampling'

    def _prepare_solver_args(
        self,
        parameters: list[object],
    ) -> dict[str, object]:
        """Prepare DREAM solver arguments in EasyDiffraction order.

        Parameters
        ----------
        parameters : list[object]
            List of parameters to be sampled.

        Returns
        -------
        dict[str, object]
            BUMPS parameters plus EasyDiffraction parameter metadata.
        """
        solver_args = super()._prepare_solver_args(parameters)
        solver_args['parameter_names'] = [parameter.unique_name for parameter in parameters]
        solver_args['parameter_display_names'] = [
            getattr(parameter, 'name', parameter.unique_name) for parameter in parameters
        ]
        solver_args['parameter_uids'] = [parameter._minimizer_uid for parameter in parameters]
        solver_args['starting_uncertainties'] = [parameter.uncertainty for parameter in parameters]
        return solver_args

    @staticmethod
    def _validated_positive_integer(name: str, value: int | float) -> int:
        """Validate a DREAM setting that must be a positive integer."""
        if isinstance(value, bool):
            msg = f"DREAM setting '{name}' must be a positive integer."
            raise ValueError(msg)

        integer_value = int(value)
        if integer_value != value or integer_value < 1:
            msg = f"DREAM setting '{name}' must be a positive integer."
            raise ValueError(msg)
        return integer_value

    @staticmethod
    def _validated_non_negative_integer(name: str, value: int | float) -> int:
        """Validate a DREAM setting that must be a non-negative integer."""
        if isinstance(value, bool):
            msg = f"DREAM setting '{name}' must be a non-negative integer."
            raise ValueError(msg)

        integer_value = int(value)
        if integer_value != value or integer_value < 0:
            msg = f"DREAM setting '{name}' must be a non-negative integer."
            raise ValueError(msg)
        return integer_value

    def _resolved_burn(self, steps: int) -> int:
        """Return the configured or automatic DREAM burn-in length."""
        if self.burn is None:
            proposed_burn = max(DEFAULT_MIN_BURN, int(steps * DEFAULT_BURN_FRACTION))
            return min(proposed_burn, max(steps - 1, 0))

        burn = self.burn
        if burn >= steps:
            msg = "DREAM setting 'burn' must be smaller than 'steps'."
            raise ValueError(msg)
        return burn

    def _sampler_settings(
        self,
        *,
        random_seed: int,
        steps: int,
        burn: int,
        thin: int,
        pop: int,
        n_parameters: int,
    ) -> dict[str, object]:
        """Build the sampler settings dictionary recorded in results."""
        samples = steps * pop * n_parameters
        return {
            'random_seed': int(random_seed),
            'steps': int(steps),
            'burn': int(burn),
            'thin': int(thin),
            'pop': int(pop),
            'samples': int(samples),
            'alpha': float(DEFAULT_ALPHA),
            'outliers': DEFAULT_OUTLIER_TEST,
            'trim': DEFAULT_TRIM,
        }

    def _run_solver(
        self,
        objective_function: object,
        **kwargs: object,
    ) -> object:
        """Run the DREAM sampler and normalize its posterior outputs.

        Parameters
        ----------
        objective_function : object
            Objective function returning residuals.
        **kwargs : object
            Solver arguments including BUMPS parameters and random seed.

        Returns
        -------
        object
            Normalized DREAM result stored in an ``OptimizeResult``.
        """
        bumps_params = kwargs.get('bumps_params')
        parameter_names = kwargs.get('parameter_names')
        parameter_display_names = kwargs.get('parameter_display_names')
        parameter_uids = kwargs.get('parameter_uids')
        random_seed = kwargs.get('random_seed')
        starting_uncertainties = kwargs.get('starting_uncertainties')
        fitness = _EasyDiffractionFitness(bumps_params, objective_function)
        fitness.nllf()
        problem = FitProblem(fitness)

        fitclass = next(cls for cls in FITTERS if cls.id == self.method)
        steps = self.steps
        burn = self._resolved_burn(steps)
        thin = self.thin
        pop = self.pop
        sampler_settings = self._sampler_settings(
            random_seed=int(random_seed),
            steps=steps,
            burn=burn,
            thin=thin,
            pop=pop,
            n_parameters=len(bumps_params),
        )
        total_generations = int(steps + burn + 1)
        progress_monitor = _DreamProgressMonitor(
            tracker=self.tracker,
            n_points=fitness.numpoints(),
            n_parameters=len(bumps_params),
            total_generations=total_generations,
            burn_steps=int(burn),
        )
        driver = FitDriver(
            fitclass=fitclass,
            problem=problem,
            monitors=[progress_monitor],
            steps=steps,
            burn=burn,
            thin=thin,
            pop=pop,
            samples=sampler_settings['samples'],
            alpha=DEFAULT_ALPHA,
            outliers=DEFAULT_OUTLIER_TEST,
            trim=DEFAULT_TRIM,
        )
        driver.clip()

        starting_values = np.array([parameter.value for parameter in bumps_params], dtype=float)
        if starting_uncertainties is None:
            starting_uncertainties = [None] * len(bumps_params)

        numpy_state = np.random.get_state()
        python_state = random.getstate()
        np.random.seed(random_seed)
        random.seed(random_seed)
        try:
            best_values, best_nllf = driver.fit()
        except Exception as error:  # pragma: no cover - defensive runtime path
            return OptimizeResult(
                x=starting_values,
                dx=None,
                fun=None,
                success=False,
                status=-1,
                message=f'DREAM sampling failed: {error}',
                var_names=parameter_names,
                posterior_samples=None,
                posterior_parameter_summaries=[],
                convergence_diagnostics={},
                sampler_settings=sampler_settings,
                sampler_completed=False,
                raw_state=None,
                best_log_posterior=None,
                starting_values=starting_values,
                starting_uncertainties=starting_uncertainties,
            )
        finally:
            np.random.set_state(numpy_state)
            random.setstate(python_state)

        state = getattr(driver.fitter, 'state', None)
        if best_values is None or state is None:
            return OptimizeResult(
                x=starting_values,
                dx=None,
                fun=None,
                success=False,
                status=-1,
                message='DREAM sampling did not produce usable posterior samples.',
                var_names=parameter_names,
                posterior_samples=None,
                posterior_parameter_summaries=[],
                convergence_diagnostics={},
                sampler_settings=sampler_settings,
                sampler_completed=False,
                raw_state=state,
                best_log_posterior=None,
                starting_values=starting_values,
                starting_uncertainties=starting_uncertainties,
            )

        draw_index, parameter_samples_array, log_posterior = state.chains()
        if parameter_samples_array.ndim != 3 or parameter_samples_array.size == 0:
            return OptimizeResult(
                x=starting_values,
                dx=None,
                fun=None,
                success=False,
                status=-1,
                message='DREAM sampling did not return a usable posterior sample array.',
                var_names=parameter_names,
                posterior_samples=None,
                posterior_parameter_summaries=[],
                convergence_diagnostics={},
                sampler_settings=sampler_settings,
                sampler_completed=True,
                raw_state=state,
                best_log_posterior=None,
                starting_values=starting_values,
                starting_uncertainties=starting_uncertainties,
            )

        state_best_values, best_log_posterior = state.best()
        best_by_name = dict(zip(state.labels, state_best_values, strict=True))
        label_to_index = {label: index for index, label in enumerate(state.labels)}
        ordered_indices = [label_to_index[uid] for uid in parameter_uids]
        ordered_samples = np.asarray(parameter_samples_array, dtype=float)[:, :, ordered_indices]
        map_values = np.array([best_by_name[uid] for uid in parameter_uids], dtype=float)

        posterior_samples = PosteriorSamples(
            parameter_names=parameter_names,
            parameter_samples=ordered_samples,
            log_posterior=np.asarray(log_posterior, dtype=float),
            draw_index=np.asarray(draw_index, dtype=float),
        )
        convergence_diagnostics = compute_convergence_diagnostics(posterior_samples)
        posterior_parameter_summaries = summarize_posterior_parameters(
            parameter_names=parameter_names,
            posterior_samples=posterior_samples,
            map_values=map_values,
            parameter_display_names=parameter_display_names,
            convergence_diagnostics=convergence_diagnostics,
        )
        posterior_standard_deviations = standard_deviations_from_summaries(
            posterior_parameter_summaries
        )

        if not convergence_diagnostics.get('converged', True):
            log.warning(
                'DREAM sampling completed, but convergence diagnostics indicate '
                'the posterior may be poorly mixed.'
            )

        return OptimizeResult(
            x=map_values,
            dx=posterior_standard_deviations,
            fun=float(best_nllf),
            success=True,
            status=0,
            message='DREAM sampling completed',
            var_names=parameter_names,
            posterior_samples=posterior_samples,
            posterior_parameter_summaries=posterior_parameter_summaries,
            convergence_diagnostics=convergence_diagnostics,
            sampler_settings=sampler_settings,
            sampler_completed=True,
            raw_state=state,
            best_log_posterior=float(best_log_posterior),
            starting_values=starting_values,
            starting_uncertainties=starting_uncertainties,
        )

    def _sync_result_to_parameters(
        self,
        parameters: list[object],
        raw_result: object,
    ) -> None:
        """Commit MAP values on success and restore starts on failure.

        Parameters
        ----------
        parameters : list[object]
            Parameters being optimized.
        raw_result : object
            DREAM result object.
        """
        if hasattr(raw_result, 'x'):
            if getattr(raw_result, 'success', False):
                values = raw_result.x
                uncertainties = getattr(raw_result, 'dx', None)
            else:
                values = getattr(raw_result, 'starting_values', raw_result.x)
                uncertainties = getattr(raw_result, 'starting_uncertainties', None)
        else:
            values = raw_result
            uncertainties = None

        if values is None:
            return

        for index, parameter in enumerate(parameters):
            parameter._set_value_from_minimizer(float(values[index]))
            if uncertainties is None:
                parameter.uncertainty = None
                continue

            uncertainty = uncertainties[index]
            parameter.uncertainty = None if uncertainty is None else float(uncertainty)

    def _build_fit_results(
        self,
        *,
        parameters: list[object],
        raw_result: object,
        success: bool,
    ) -> BayesianFitResults:
        """Build the Bayesian fit result container.

        Parameters
        ----------
        parameters : list[object]
            Parameters after the solver finished.
        raw_result : object
            Normalized DREAM solver output.
        success : bool
            Whether DREAM produced usable posterior samples.

        Returns
        -------
        BayesianFitResults
            Bayesian result object for the finished run.
        """
        fit_results = BayesianFitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            engine_result=getattr(raw_result, 'raw_state', raw_result),
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time,
            sampler_name='dream',
            point_estimate_name='map',
            posterior_samples=getattr(raw_result, 'posterior_samples', None),
            posterior_parameter_summaries=getattr(
                raw_result, 'posterior_parameter_summaries', []
            ),
            posterior_predictive={},
            credible_interval_levels=(0.68, 0.95),
            sampler_settings=getattr(raw_result, 'sampler_settings', {}),
            convergence_diagnostics=getattr(raw_result, 'convergence_diagnostics', {}),
            sampler_completed=getattr(raw_result, 'sampler_completed', False),
            best_log_posterior=getattr(raw_result, 'best_log_posterior', None),
        )
        fit_results.message = getattr(raw_result, 'message', '')
        fit_results.iterations = int(fit_results.sampler_settings.get('steps', self.steps))
        fit_results.result = raw_result
        return fit_results