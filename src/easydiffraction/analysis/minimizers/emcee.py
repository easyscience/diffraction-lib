# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimizer using the emcee ensemble sampler."""

from __future__ import annotations

import multiprocessing
import os
import pickle  # noqa: S403 - used only to test whether multiprocessing can serialize a callable.
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import emcee
import numpy as np
from scipy.optimize import OptimizeResult

from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
from easydiffraction.analysis.fit_helpers.bayesian import compute_convergence_diagnostics
from easydiffraction.analysis.fit_helpers.bayesian import standard_deviations_from_summaries
from easydiffraction.analysis.fit_helpers.bayesian import summarize_posterior_parameters
from easydiffraction.analysis.fit_helpers.tracking import SamplerProgressUpdate
from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.enums import InitializationMethodEnum
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.utils.enums import VerbosityEnum

DEFAULT_METHOD = 'stretch'
DEFAULT_NSTEPS = 5000
DEFAULT_NBURN = 1000
DEFAULT_THIN = 5
DEFAULT_NWALKERS = 32
DEFAULT_PARALLEL_WORKERS = 0
DEFAULT_INITIALIZATION_METHOD = InitializationMethodEnum.BALL
DEFAULT_PROPOSAL_MOVES = 'stretch'
MAX_RANDOM_SEED = int(np.iinfo(np.uint32).max)
EMCEE_CHAIN_GROUP = 'emcee_chain'
EMCEE_FAILURES = (ArithmeticError, RuntimeError, TypeError, ValueError)
EMCEE_SAMPLE_ARRAY_NDIM = 3
TOTAL_PROGRESS_POINTS = 25
SUPPORTED_INITIALIZATION_METHODS = (
    InitializationMethodEnum.BALL,
    InitializationMethodEnum.UNIFORM,
    InitializationMethodEnum.PRIOR,
)
SUPPORTED_INITIALIZATION_METHOD_SET = frozenset(SUPPORTED_INITIALIZATION_METHODS)

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class _EmceePoolContext:
    """Resolved emcee pool and log-probability callable."""

    pool: object | None
    log_prob_fn: Callable[[np.ndarray], float]


class _EmceeLogProbability:
    """Pickle-aware emcee log-probability adapter."""

    def __init__(
        self,
        *,
        parameters: list[object],
        parameter_names: list[str],
        objective_function: Callable[[dict[str, object]], object],
    ) -> None:
        self._parameter_names = parameter_names
        self._objective_function = objective_function
        self._bounds = {
            name: (float(parameter.fit_min), float(parameter.fit_max))
            for name, parameter in zip(parameter_names, parameters, strict=True)
        }

    def __call__(self, theta: np.ndarray) -> float:
        """Return log posterior for one walker position."""
        for name, value in zip(self._parameter_names, theta, strict=True):
            lower_bound, upper_bound = self._bounds[name]
            if not lower_bound <= float(value) <= upper_bound:
                return -np.inf

        engine_params = {
            name: float(value) for name, value in zip(self._parameter_names, theta, strict=True)
        }
        try:
            residuals = np.asarray(self._objective_function(engine_params), dtype=float)
        except Exception:  # noqa: BLE001 - calculator failures make this proposal invalid.
            return -np.inf
        if residuals.size == 0 or not np.all(np.isfinite(residuals)):
            return -np.inf
        return -0.5 * float(np.sum(residuals**2))


_EMCEE_WORKER_LOG_PROB: _EmceeLogProbability | None = None


def _set_emcee_worker_log_prob(log_prob: _EmceeLogProbability | None) -> None:
    """Set the fork-inherited emcee worker log-probability callable."""
    global _EMCEE_WORKER_LOG_PROB  # noqa: PLW0603
    _EMCEE_WORKER_LOG_PROB = log_prob


def _emcee_log_prob_worker(theta: np.ndarray) -> float:
    """Evaluate log probability in an emcee multiprocessing worker."""
    if _EMCEE_WORKER_LOG_PROB is None:
        msg = 'emcee worker log-probability callable has not been initialized.'
        raise RuntimeError(msg)
    return _EMCEE_WORKER_LOG_PROB(theta)


class _EmceeProgressReporter:
    """
    Translate emcee iteration states into sampler progress rows.
    """

    def __init__(
        self,
        *,
        tracker: object,
        total_steps: int,
        burn_steps: int,
    ) -> None:
        self._tracker = tracker
        self._total_steps = max(1, total_steps)
        self._burn_steps = min(max(0, burn_steps), self._total_steps)
        burn_target_count, sampling_target_count = self._phase_progress_point_counts(
            total_steps=self._total_steps,
            burn_steps=self._burn_steps,
        )
        self._burn_targets = self._progress_targets(
            start=1,
            stop=self._burn_steps,
            target_count=burn_target_count,
        )
        self._sampling_targets = self._progress_targets(
            start=self._burn_steps + 1,
            stop=self._total_steps,
            target_count=sampling_target_count,
        )
        self._next_burn_target_index = 0
        self._next_sampling_target_index = 0

    def report(self, *, iteration: int, state: object) -> None:
        """
        Forward one emcee state when it reaches a report target.
        """
        clamped_iteration = min(max(1, iteration), self._total_steps)
        if not self._should_report(clamped_iteration):
            return

        self._tracker.track_sampler_progress(
            SamplerProgressUpdate(
                iteration=clamped_iteration,
                total_iterations=self._total_steps,
                phase=self._phase_name(clamped_iteration),
                progress_percent=self._progress_percent(clamped_iteration),
                log_posterior=self._log_posterior_from_state(state),
                reduced_chi2=self._reduced_chi2_from_tracker(),
                elapsed_time=self._tracker._current_elapsed_time(),
                force_report=True,
            )
        )

    @staticmethod
    def _phase_progress_point_counts(
        *,
        total_steps: int,
        burn_steps: int,
    ) -> tuple[int, int]:
        """Return proportional burn and sampling progress counts."""
        total_points = min(TOTAL_PROGRESS_POINTS, max(1, total_steps))
        burn_steps = min(max(0, burn_steps), total_steps)
        sampling_steps = max(total_steps - burn_steps, 0)

        if burn_steps == 0:
            return 0, total_points
        if sampling_steps == 0:
            return total_points, 0

        burn_target_count = round(total_points * burn_steps / total_steps)
        burn_target_count = min(
            max(burn_target_count, 1),
            burn_steps,
            total_points - 1,
        )
        sampling_target_count = min(
            max(total_points - burn_target_count, 1),
            sampling_steps,
        )
        return burn_target_count, sampling_target_count

    @staticmethod
    def _progress_targets(
        *,
        start: int,
        stop: int,
        target_count: int,
    ) -> list[int]:
        """Return monotonically increasing reporting targets."""
        if target_count < 1 or stop < start:
            return []

        targets = np.linspace(start, stop, num=target_count)
        rounded = np.rint(targets).astype(int)
        unique_targets = sorted({int(value) for value in rounded if start <= value <= stop})
        if start not in unique_targets:
            unique_targets.insert(0, start)
        if stop not in unique_targets:
            unique_targets.append(stop)
        return unique_targets

    def _should_report(self, iteration: int) -> bool:
        """Return whether this iteration should be rendered."""
        if self._phase_name(iteration) == 'burn-in':
            return self._consume_progress_target(
                iteration,
                phase_targets=self._burn_targets,
                target_index_name='_next_burn_target_index',
            )

        return self._consume_progress_target(
            iteration,
            phase_targets=self._sampling_targets,
            target_index_name='_next_sampling_target_index',
        )

    def _consume_progress_target(
        self,
        iteration: int,
        *,
        phase_targets: list[int],
        target_index_name: str,
    ) -> bool:
        """Advance a phase target pointer when iteration reaches it."""
        target_index = getattr(self, target_index_name)
        should_report = False
        while target_index < len(phase_targets) and iteration >= phase_targets[target_index]:
            target_index += 1
            should_report = True
        setattr(self, target_index_name, target_index)
        return should_report

    def _phase_name(self, iteration: int) -> str:
        """Return the current emcee phase name."""
        if iteration <= self._burn_steps:
            return 'burn-in'
        return 'sampling'

    def _progress_percent(self, iteration: int) -> float:
        """Return emcee progress as a percentage."""
        return 100.0 * min(iteration, self._total_steps) / self._total_steps

    @staticmethod
    def _log_posterior_from_state(state: object) -> float:
        """Return the best finite log posterior from an emcee state."""
        log_probability = getattr(state, 'log_prob', None)
        if log_probability is None:
            return float('-inf')

        values = np.asarray(log_probability, dtype=float)
        finite_values = values[np.isfinite(values)]
        if finite_values.size == 0:
            return float('-inf')
        return float(np.max(finite_values))

    def _reduced_chi2_from_tracker(self) -> float:
        """Return the current best reduced chi-square, if available."""
        best_chi2 = getattr(self._tracker, 'best_chi2', None)
        return float(best_chi2) if best_chi2 is not None else float('nan')


@MinimizerFactory.register
class EmceeMinimizer(MinimizerBase):
    """emcee affine-invariant ensemble Bayesian sampler."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.EMCEE,
        description='emcee affine-invariant ensemble Bayesian sampling',
    )

    _sidecar_path: Path | None = None

    def __init__(
        self,
        name: str = MinimizerTypeEnum.EMCEE,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_NSTEPS,
    ) -> None:
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
        self._nburn: int = DEFAULT_NBURN
        self._thin: int = DEFAULT_THIN
        self._nwalkers: int = DEFAULT_NWALKERS
        self._parallel_workers: int = DEFAULT_PARALLEL_WORKERS
        self._initialization_method: InitializationMethodEnum = DEFAULT_INITIALIZATION_METHOD
        self._proposal_moves: str = DEFAULT_PROPOSAL_MOVES
        self._sampler: emcee.EnsembleSampler | None = None
        self._backend: emcee.backends.HDFBackend | None = None

    @property
    def nsteps(self) -> int:
        """Number of emcee steps to run per walker."""
        return self._validated_positive_integer('nsteps', self._max_iterations)

    @nsteps.setter
    def nsteps(self, value: int) -> None:
        self._max_iterations = self._validated_positive_integer('nsteps', value)

    @property
    def nburn(self) -> int:
        """Number of initial emcee steps discarded as burn-in."""
        return self._nburn

    @nburn.setter
    def nburn(self, value: int) -> None:
        self._nburn = self._validated_non_negative_integer('nburn', value)

    @property
    def thin(self) -> int:
        """Emcee thinning interval."""
        return self._thin

    @thin.setter
    def thin(self, value: int) -> None:
        self._thin = self._validated_positive_integer('thin', value)

    @property
    def nwalkers(self) -> int:
        """Number of emcee walkers."""
        return self._nwalkers

    @nwalkers.setter
    def nwalkers(self, value: int) -> None:
        self._nwalkers = self._validated_positive_integer('nwalkers', value)

    @property
    def parallel_workers(self) -> int:
        """
        Worker count; ``0`` asks for all CPUs and ``1`` runs serially.
        """
        return self._parallel_workers

    @parallel_workers.setter
    def parallel_workers(self, value: int) -> None:
        self._parallel_workers = self._validated_non_negative_integer('parallel_workers', value)

    @property
    def initialization_method(self) -> InitializationMethodEnum:
        """Emcee walker initialization method."""
        return self._initialization_method

    @initialization_method.setter
    def initialization_method(self, value: InitializationMethodEnum | str) -> None:
        self._initialization_method = self._validated_initialization_method(value)

    @property
    def proposal_moves(self) -> str:
        """Emcee proposal move name."""
        return self._proposal_moves

    @proposal_moves.setter
    def proposal_moves(self, value: str) -> None:
        self._proposal_moves = self._validated_proposal_moves(value)

    def fit(  # noqa: PLR0913
        self,
        parameters: list[object],
        objective_function: Callable[..., object],
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
        *,
        finalize_tracking: bool = True,
        use_physical_limits: bool = False,
        random_seed: int | None = None,
        resume: bool = False,
        extra_steps: int | None = None,
    ) -> BayesianFitResults:
        """
        Run emcee sampling and return Bayesian fit results.
        """
        if use_physical_limits:
            self._apply_physical_limits(parameters)

        resolved_random_seed = self._resolve_random_seed(random_seed)
        minimizer_name = self.name or 'emcee'
        self._start_tracking(minimizer_name, verbosity=verbosity)

        try:
            solver_args = self._prepare_solver_args(parameters)
            solver_args['random_seed'] = resolved_random_seed
            solver_args['resume'] = resume
            solver_args['extra_steps'] = extra_steps
            raw_result = self._run_solver(objective_function, **solver_args)
            return self._finalize_fit(parameters, raw_result)
        finally:
            if finalize_tracking:
                self._stop_tracking()

    @staticmethod
    def _tracking_mode() -> str:
        """Use sampler-style progress reporting for emcee runs."""
        return 'sampling'

    def _resolve_random_seed(self, random_seed: int | None) -> int:
        """
        Return a user-provided or generated random seed.
        """
        if random_seed is None:
            generator = np.random.default_rng()
            random_seed = int(generator.integers(0, np.iinfo(np.int32).max))

        integer_seed = self._validated_random_seed_value(random_seed)
        self._resolved_random_seed = integer_seed
        return self._resolved_random_seed

    @staticmethod
    def _validated_random_seed_value(random_seed: object) -> int:
        """Validate and normalize an emcee random seed."""
        if isinstance(random_seed, bool):
            msg = f'emcee random_seed must be an integer between 0 and {MAX_RANDOM_SEED}.'
            raise TypeError(msg)

        integer_seed = int(random_seed)
        if integer_seed != random_seed or integer_seed < 0 or integer_seed > MAX_RANDOM_SEED:
            msg = f'emcee random_seed must be an integer between 0 and {MAX_RANDOM_SEED}.'
            raise ValueError(msg)
        return integer_seed

    def _prepare_solver_args(
        self,
        parameters: list[object],
    ) -> dict[str, object]:
        """
        Prepare emcee solver arguments in EasyDiffraction order.
        """
        self._validate_sampled_parameter_bounds(parameters)
        return {
            'parameters': parameters,
            'parameter_names': [parameter.unique_name for parameter in parameters],
            'parameter_display_names': [
                getattr(parameter, 'name', parameter.unique_name) for parameter in parameters
            ],
            'starting_values': np.array(
                [parameter.value for parameter in parameters],
                dtype=float,
            ),
            'starting_uncertainties': [parameter.uncertainty for parameter in parameters],
        }

    @classmethod
    def _validate_sampled_parameter_bounds(
        cls,
        parameters: list[object],
    ) -> None:
        """
        Validate finite ordered bounds for sampled emcee parameters.
        """
        issues: list[str] = []
        for parameter in parameters:
            parameter_name = cls._parameter_name_for_bound_validation(parameter)
            parameter_issues = cls._parameter_bound_issues(parameter)
            if parameter_issues:
                issues.append(f'- {parameter_name}: {"; ".join(parameter_issues)}')

        if not issues:
            return

        message = 'emcee requires finite valid bounds for every sampled parameter:\n' + '\n'.join(
            issues
        )
        raise ValueError(message)

    @staticmethod
    def _parameter_name_for_bound_validation(parameter: object) -> str:
        """Return the user-facing name for emcee bound validation."""
        unique_name = getattr(parameter, 'unique_name', None)
        if unique_name:
            return str(unique_name)

        parameter_name = getattr(parameter, 'name', None)
        if parameter_name:
            return str(parameter_name)
        return '<unknown parameter>'

    @classmethod
    def _parameter_bound_issues(
        cls,
        parameter: object,
    ) -> list[str]:
        """Return bound-validation issues for one sampled parameter."""
        lower_bound = getattr(parameter, 'fit_min', None)
        upper_bound = getattr(parameter, 'fit_max', None)
        value = getattr(parameter, 'value', None)
        issues: list[str] = []

        lower_is_finite = cls._is_finite_bound_value(lower_bound)
        upper_is_finite = cls._is_finite_bound_value(upper_bound)
        value_is_finite = cls._is_finite_bound_value(value)

        if not lower_is_finite:
            issues.append(f'fit_min must be finite (got {lower_bound!r})')
        if not upper_is_finite:
            issues.append(f'fit_max must be finite (got {upper_bound!r})')

        bounds_are_ordered = lower_is_finite and upper_is_finite and lower_bound < upper_bound
        if lower_is_finite and upper_is_finite and not bounds_are_ordered:
            issues.append(f'fit_min ({lower_bound}) must be smaller than fit_max ({upper_bound})')

        if not value_is_finite:
            issues.append(f'starting value must be finite (got {value!r})')
        elif bounds_are_ordered and not lower_bound <= value <= upper_bound:
            issues.append(f'starting value {value} is outside [{lower_bound}, {upper_bound}]')

        return issues

    @staticmethod
    def _is_finite_bound_value(value: object) -> bool:
        """Return whether a bound-validation value is finite."""
        try:
            return bool(np.isfinite(value))
        except TypeError:
            return False

    @staticmethod
    def _validated_positive_integer(name: str, value: float) -> int:
        """Validate an emcee setting that must be a positive integer."""
        if isinstance(value, bool):
            msg = f"emcee setting '{name}' must be a positive integer."
            raise TypeError(msg)

        try:
            integer_value = int(value)
        except (TypeError, ValueError):
            msg = f"emcee setting '{name}' must be a positive integer."
            raise TypeError(msg) from None
        if integer_value != value or integer_value < 1:
            msg = f"emcee setting '{name}' must be a positive integer."
            raise ValueError(msg)
        return integer_value

    @staticmethod
    def _validated_non_negative_integer(name: str, value: float) -> int:
        """
        Validate an emcee setting that must be a non-negative integer.
        """
        if isinstance(value, bool):
            msg = f"emcee setting '{name}' must be a non-negative integer."
            raise TypeError(msg)

        try:
            integer_value = int(value)
        except (TypeError, ValueError):
            msg = f"emcee setting '{name}' must be a non-negative integer."
            raise TypeError(msg) from None
        if integer_value != value or integer_value < 0:
            msg = f"emcee setting '{name}' must be a non-negative integer."
            raise ValueError(msg)
        return integer_value

    @staticmethod
    def _validated_initialization_method(
        value: InitializationMethodEnum | str,
    ) -> InitializationMethodEnum:
        """Validate an emcee initialization method."""
        try:
            method = InitializationMethodEnum(value)
        except ValueError:
            valid_values = ', '.join(
                initialization.value for initialization in SUPPORTED_INITIALIZATION_METHODS
            )
            msg = f"emcee setting 'initialization_method' must be one of: {valid_values}."
            raise ValueError(msg) from None

        if method not in SUPPORTED_INITIALIZATION_METHOD_SET:
            valid_values = ', '.join(
                initialization.value for initialization in SUPPORTED_INITIALIZATION_METHODS
            )
            msg = f"emcee setting 'initialization_method' must be one of: {valid_values}."
            raise ValueError(msg)
        return method

    @staticmethod
    def _validated_proposal_moves(value: str) -> str:
        """Validate an emcee proposal move name."""
        valid_values = ('stretch', 'de', 'de_snooker', 'walk')
        if value not in valid_values:
            choices = ', '.join(valid_values)
            msg = f"emcee setting 'proposal_moves' must be one of: {choices}."
            raise ValueError(msg)
        return value

    def _run_solver(
        self,
        objective_function: Callable[[dict[str, object]], object],
        **kwargs: object,
    ) -> object:
        """
        Run emcee and normalize its posterior outputs.
        """
        parameters = list(kwargs['parameters'])
        parameter_names = list(kwargs['parameter_names'])
        random_seed = int(kwargs['random_seed'])
        resume = bool(kwargs.get('resume'))
        extra_steps = kwargs.get('extra_steps')

        self._validate_walker_count(n_parameters=len(parameter_names))
        sidecar_path = self._resolved_sidecar_path()
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)

        total_iterations = self._resolved_total_iterations(
            resume=resume,
            extra_steps=extra_steps,
        )
        self.tracker.start_sampler_pre_processing(total_iterations=total_iterations)

        backend = emcee.backends.HDFBackend(
            str(sidecar_path),
            name=EMCEE_CHAIN_GROUP,
            read_only=False,
        )
        self._backend = backend

        log_prob = self._build_log_probability(
            parameters=parameters,
            parameter_names=parameter_names,
            objective_function=objective_function,
        )
        pool_context = self._build_pool_context(log_prob)
        try:
            sampler = self._run_sampler(
                backend=backend,
                log_prob=pool_context.log_prob_fn,
                pool=pool_context.pool,
                parameters=parameters,
                n_parameters=len(parameter_names),
                random_seed=random_seed,
                resume=resume,
                extra_steps=extra_steps,
                total_iterations=total_iterations,
            )
        except EMCEE_FAILURES as error:
            return self._failure_result(
                message=f'emcee sampling failed: {error}',
                starting_values=kwargs['starting_values'],
                starting_uncertainties=kwargs['starting_uncertainties'],
                sampler_settings=self._sampler_settings(
                    random_seed=random_seed,
                    total_steps=self._backend_iteration(backend),
                    n_parameters=len(parameter_names),
                ),
                raw_state=getattr(self._sampler, 'random_state', None),
                sampler_completed=False,
            )
        finally:
            self._close_pool_context(pool_context)

        self.tracker.start_sampler_post_processing()
        return self._build_success_result(
            sampler=sampler,
            backend=backend,
            parameter_names=parameter_names,
            parameter_display_names=list(kwargs['parameter_display_names']),
            random_seed=random_seed,
            starting_values=kwargs['starting_values'],
            starting_uncertainties=kwargs['starting_uncertainties'],
        )

    def _run_sampler(  # noqa: PLR0913
        self,
        *,
        backend: emcee.backends.HDFBackend,
        log_prob: Callable[[np.ndarray], float],
        pool: object | None,
        parameters: list[object],
        n_parameters: int,
        random_seed: int,
        resume: bool,
        extra_steps: object,
        total_iterations: int,
    ) -> emcee.EnsembleSampler:
        """Configure emcee, run sampling, and return the sampler."""
        if resume:
            self._validate_resume(
                backend=backend,
                n_parameters=n_parameters,
                extra_steps=extra_steps,
            )
        else:
            backend.reset(self.nwalkers, n_parameters)

        sampler = emcee.EnsembleSampler(
            nwalkers=self.nwalkers,
            ndim=n_parameters,
            log_prob_fn=log_prob,
            pool=pool,
            moves=self._resolve_moves(self.proposal_moves),
            backend=backend,
        )
        self._sampler = sampler

        reporter = _EmceeProgressReporter(
            tracker=self.tracker,
            total_steps=total_iterations,
            burn_steps=0 if resume else self.nburn,
        )
        if resume:
            self._sample_with_progress(
                sampler=sampler,
                initial_state=None,
                iterations=int(extra_steps),
                reporter=reporter,
                skip_initial_state_check=True,
            )
            return sampler

        initial_state = self._initial_state(parameters, random_seed=random_seed)
        self._sample_with_progress(
            sampler=sampler,
            initial_state=initial_state,
            iterations=self.nsteps,
            reporter=reporter,
            skip_initial_state_check=False,
        )
        return sampler

    @staticmethod
    def _sample_with_progress(
        *,
        sampler: emcee.EnsembleSampler,
        initial_state: object | None,
        iterations: int,
        reporter: _EmceeProgressReporter,
        skip_initial_state_check: bool,
    ) -> None:
        """
        Run emcee one iteration at a time and report sampler progress.
        """
        for iteration, state in enumerate(
            sampler.sample(
                initial_state,
                iterations=iterations,
                skip_initial_state_check=skip_initial_state_check,
                progress=False,
            ),
            start=1,
        ):
            reporter.report(iteration=iteration, state=state)

    @staticmethod
    def _backend_iteration(backend: object) -> int:
        """Return backend iteration count, or zero when unavailable."""
        try:
            return int(getattr(backend, 'iteration', 0))
        except (AttributeError, TypeError, ValueError):
            return 0

    @staticmethod
    def _build_log_probability(
        *,
        parameters: list[object],
        parameter_names: list[str],
        objective_function: Callable[[dict[str, object]], object],
    ) -> _EmceeLogProbability:
        """Return an emcee log-probability adapter."""
        return _EmceeLogProbability(
            parameters=parameters,
            parameter_names=parameter_names,
            objective_function=objective_function,
        )

    def _resolved_sidecar_path(self) -> Path:
        """Return the HDF sidecar path required by the emcee backend."""
        if self._sidecar_path is None:
            msg = 'emcee engine requires Fitter.fit to set _sidecar_path; was Analysis configured?'
            raise RuntimeError(msg)
        return Path(self._sidecar_path)

    def _resolved_total_iterations(
        self,
        *,
        resume: bool,
        extra_steps: object,
    ) -> int:
        """Return the total iterations expected for progress display."""
        if not resume:
            return self.nsteps
        return self._validated_positive_integer('extra_steps', extra_steps)

    def _validate_walker_count(self, *, n_parameters: int) -> None:
        """Validate emcee's minimum walker count for red-blue moves."""
        if n_parameters < 1:
            msg = 'emcee requires at least one sampled parameter.'
            raise ValueError(msg)
        minimum_walkers = 2 * n_parameters
        if self.nwalkers < minimum_walkers:
            msg = (
                f"emcee setting 'nwalkers' must be at least twice the sampled "
                f'parameter count ({minimum_walkers}).'
            )
            raise ValueError(msg)

    def _validate_resume(
        self,
        *,
        backend: object,
        n_parameters: int,
        extra_steps: object,
    ) -> None:
        """Validate that an existing emcee backend can be resumed."""
        self._validated_positive_integer('extra_steps', extra_steps)
        iteration = self._backend_iteration(backend)
        if iteration < 1:
            msg = 'No existing emcee chain was found; start a fresh run instead.'
            raise ValueError(msg)

        backend_shape = getattr(backend, 'shape', None)
        if backend_shape != (self.nwalkers, n_parameters):
            msg = (
                'Existing emcee chain shape does not match current parameters; '
                'start a fresh run.'
            )
            raise ValueError(msg)

    def _build_pool_context(self, log_prob: _EmceeLogProbability) -> _EmceePoolContext:
        """
        Build an emcee map pool for the configured parallel setting.
        """
        workers = self.parallel_workers
        if workers == 1:
            return _EmceePoolContext(pool=None, log_prob_fn=log_prob)

        worker_count = os.cpu_count() if workers == 0 else workers
        if worker_count is None or worker_count <= 1:
            return _EmceePoolContext(pool=None, log_prob_fn=log_prob)

        if self._can_pickle(log_prob):
            return _EmceePoolContext(
                pool=multiprocessing.Pool(worker_count),
                log_prob_fn=log_prob,
            )

        if self._fork_context_available():
            try:
                _set_emcee_worker_log_prob(log_prob)
                pool = multiprocessing.get_context('fork').Pool(worker_count)
            except (OSError, RuntimeError):
                _set_emcee_worker_log_prob(None)
            else:
                return _EmceePoolContext(
                    pool=pool,
                    log_prob_fn=_emcee_log_prob_worker,
                )

        self._warn_after_tracking(
            'emcee parallel evaluation requires either a picklable objective '
            'or fork-based multiprocessing; falling back to serial execution.'
        )
        return _EmceePoolContext(pool=None, log_prob_fn=log_prob)

    @staticmethod
    def _close_pool_context(pool_context: _EmceePoolContext) -> None:
        """
        Close a resolved emcee pool and clear inherited worker state.
        """
        pool = pool_context.pool
        try:
            if pool is not None:
                pool.close()
                pool.join()
        finally:
            _set_emcee_worker_log_prob(None)

    @staticmethod
    def _can_pickle(value: object) -> bool:
        """
        Return whether a value can be serialized by multiprocessing.
        """
        try:
            pickle.dumps(value)
        except (AttributeError, TypeError, pickle.PickleError):
            return False
        return True

    @staticmethod
    def _fork_context_available() -> bool:
        """Return whether fork-based multiprocessing is available."""
        return os.name != 'nt' and 'fork' in multiprocessing.get_all_start_methods()

    @staticmethod
    def _resolve_moves(proposal_moves: str) -> object:
        """Return the emcee move object for a persisted move name."""
        if proposal_moves == 'stretch':
            return emcee.moves.StretchMove()
        if proposal_moves == 'de':
            return emcee.moves.DEMove()
        if proposal_moves == 'de_snooker':
            return emcee.moves.DESnookerMove()
        if proposal_moves == 'walk':
            return emcee.moves.WalkMove()
        msg = f"Unsupported emcee proposal move '{proposal_moves}'."
        raise ValueError(msg)

    def _initial_state(
        self,
        parameters: list[object],
        *,
        random_seed: int,
    ) -> np.ndarray:
        """Build an initial walker state for emcee."""
        rng = np.random.default_rng(random_seed)
        lower = np.array([float(parameter.fit_min) for parameter in parameters], dtype=float)
        upper = np.array([float(parameter.fit_max) for parameter in parameters], dtype=float)
        center = np.array([float(parameter.value) for parameter in parameters], dtype=float)

        if self.initialization_method == InitializationMethodEnum.BALL:
            scale = np.maximum((upper - lower) * 1.0e-4, np.finfo(float).eps)
            initial = center + rng.normal(scale=scale, size=(self.nwalkers, len(parameters)))
            return np.clip(initial, lower, upper)

        return rng.uniform(lower, upper, size=(self.nwalkers, len(parameters)))

    def _sampler_settings(
        self,
        *,
        random_seed: int,
        total_steps: int,
        n_parameters: int,
    ) -> dict[str, object]:
        """Build sampler settings recorded in results."""
        samples = total_steps * self.nwalkers * n_parameters
        return {
            'random_seed': int(random_seed),
            'steps': int(total_steps),
            'burn': int(self.nburn),
            'thin': int(self.thin),
            'pop': int(self.nwalkers),
            'parallel': int(self.parallel_workers),
            'init': self.initialization_method.value,
            'proposal_moves': self.proposal_moves,
            'samples': int(samples),
            'nsteps': int(total_steps),
            'nburn': int(self.nburn),
            'nwalkers': int(self.nwalkers),
            'parallel_workers': int(self.parallel_workers),
            'initialization_method': self.initialization_method.value,
        }

    @staticmethod
    def _failure_result(
        *,
        message: str,
        starting_values: object,
        starting_uncertainties: object,
        sampler_settings: dict[str, object],
        raw_state: object,
        sampler_completed: bool,
    ) -> OptimizeResult:
        """
        Build a normalized failure result for an incomplete emcee run.
        """
        return OptimizeResult(
            x=np.asarray(starting_values, dtype=float),
            dx=None,
            fun=None,
            success=False,
            status=-1,
            message=message,
            var_names=[],
            posterior_samples=None,
            posterior_parameter_summaries=[],
            convergence_diagnostics={},
            sampler_settings=sampler_settings,
            sampler_completed=sampler_completed,
            raw_state=raw_state,
            best_log_posterior=None,
            starting_values=np.asarray(starting_values, dtype=float),
            starting_uncertainties=list(starting_uncertainties),
        )

    def _build_success_result(  # noqa: PLR0914
        self,
        *,
        sampler: emcee.EnsembleSampler,
        backend: emcee.backends.HDFBackend,
        parameter_names: list[str],
        parameter_display_names: list[str],
        random_seed: int,
        starting_values: object,
        starting_uncertainties: object,
    ) -> OptimizeResult:
        """Normalize a completed emcee run into an OptimizeResult."""
        total_steps = self._backend_iteration(backend)
        discard = min(self.nburn, max(total_steps - 1, 0))
        chain = np.asarray(sampler.get_chain(discard=discard, thin=self.thin), dtype=float)
        log_posterior = np.asarray(
            sampler.get_log_prob(discard=discard, thin=self.thin),
            dtype=float,
        )
        sampler_settings = self._sampler_settings(
            random_seed=random_seed,
            total_steps=total_steps,
            n_parameters=len(parameter_names),
        )

        if (
            chain.ndim != EMCEE_SAMPLE_ARRAY_NDIM
            or chain.size == 0
            or log_posterior.shape != chain.shape[:2]
        ):
            return self._failure_result(
                message='emcee sampling did not return usable posterior samples.',
                starting_values=starting_values,
                starting_uncertainties=starting_uncertainties,
                sampler_settings=sampler_settings,
                raw_state=sampler.get_last_sample(),
                sampler_completed=True,
            )

        finite_log_posterior = np.where(np.isfinite(log_posterior), log_posterior, -np.inf)
        if not np.any(np.isfinite(finite_log_posterior)):
            return self._failure_result(
                message='emcee sampling did not return any finite log-posterior values.',
                starting_values=starting_values,
                starting_uncertainties=starting_uncertainties,
                sampler_settings=sampler_settings,
                raw_state=sampler.get_last_sample(),
                sampler_completed=True,
            )

        best_flat_index = int(np.argmax(finite_log_posterior))
        best_draw_index, best_walker_index = np.unravel_index(
            best_flat_index,
            finite_log_posterior.shape,
        )
        best_sample_values = np.asarray(chain[best_draw_index, best_walker_index, :], dtype=float)
        draw_index = np.arange(chain.shape[0], dtype=float) * self.thin + discard + 1
        posterior_samples = PosteriorSamples(
            parameter_names=parameter_names,
            parameter_samples=chain,
            log_posterior=log_posterior,
            draw_index=draw_index,
        )
        convergence_diagnostics = self._convergence_diagnostics(
            posterior_samples=posterior_samples,
            sampler=sampler,
        )
        posterior_parameter_summaries = summarize_posterior_parameters(
            parameter_names=parameter_names,
            posterior_samples=posterior_samples,
            best_sample_values=best_sample_values,
            parameter_display_names=parameter_display_names,
            convergence_diagnostics=convergence_diagnostics,
        )
        posterior_standard_deviations = standard_deviations_from_summaries(
            posterior_parameter_summaries
        )
        best_log_posterior = float(finite_log_posterior[best_draw_index, best_walker_index])
        self._track_sampler_completion(
            total_steps=total_steps,
            best_log_posterior=best_log_posterior,
        )

        return OptimizeResult(
            x=best_sample_values,
            dx=posterior_standard_deviations,
            fun=-best_log_posterior,
            success=True,
            status=0,
            message='emcee sampling completed',
            var_names=parameter_names,
            posterior_samples=posterior_samples,
            posterior_parameter_summaries=posterior_parameter_summaries,
            convergence_diagnostics=convergence_diagnostics,
            sampler_settings=sampler_settings,
            sampler_completed=True,
            raw_state=sampler.get_last_sample(),
            best_log_posterior=best_log_posterior,
            starting_values=np.asarray(starting_values, dtype=float),
            starting_uncertainties=list(starting_uncertainties),
        )

    def _convergence_diagnostics(
        self,
        *,
        posterior_samples: PosteriorSamples,
        sampler: emcee.EnsembleSampler,
    ) -> dict[str, object]:
        """
        Compute convergence diagnostics and add emcee acceptance rate.
        """
        try:
            convergence_diagnostics = compute_convergence_diagnostics(posterior_samples)
        except (TypeError, ValueError, RuntimeError) as error:
            self._warn_after_tracking(
                f'emcee convergence diagnostics could not be computed: {error}'
            )
            convergence_diagnostics = {
                'converged': False,
                'r_hat_by_parameter': {},
                'ess_bulk_by_parameter': {},
                'max_r_hat': None,
                'min_ess_bulk': None,
                'n_draws': int(posterior_samples.parameter_samples.shape[0]),
                'n_chains': int(posterior_samples.parameter_samples.shape[1]),
                'n_parameters': len(posterior_samples.parameter_names),
            }

        acceptance_fraction = np.asarray(sampler.acceptance_fraction, dtype=float)
        finite_acceptance = acceptance_fraction[np.isfinite(acceptance_fraction)]
        convergence_diagnostics['acceptance_rate_mean'] = (
            float(np.mean(finite_acceptance)) if finite_acceptance.size else None
        )
        if not convergence_diagnostics.get('converged', True):
            self._warn_after_tracking(
                'Convergence diagnostics indicate the posterior may be poorly mixed.'
            )
        return convergence_diagnostics

    def _track_sampler_completion(
        self,
        *,
        total_steps: int,
        best_log_posterior: float,
    ) -> None:
        """Record one final sampler progress row."""
        reduced_chi2 = self.tracker.best_chi2
        if reduced_chi2 is None:
            reduced_chi2 = np.nan
        self.tracker.track_sampler_progress(
            SamplerProgressUpdate(
                iteration=max(1, total_steps),
                total_iterations=max(1, total_steps),
                phase='sampling',
                progress_percent=100.0,
                log_posterior=best_log_posterior,
                reduced_chi2=float(reduced_chi2),
                elapsed_time=self.tracker._current_elapsed_time(),
                force_report=True,
            )
        )

    @staticmethod
    def _sync_result_to_parameters(
        parameters: list[object],
        raw_result: object,
    ) -> None:
        """
        Sync proposed or best posterior values to live parameters.
        """
        if isinstance(raw_result, dict):
            for parameter in parameters:
                value = raw_result.get(parameter.unique_name)
                if value is None:
                    value = raw_result.get(getattr(parameter, '_minimizer_uid', ''))
                if value is not None:
                    parameter._set_value_from_minimizer(float(value))
            return

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
        """
        Build the Bayesian fit result container.
        """
        fit_results = BayesianFitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            engine_result=getattr(raw_result, 'raw_state', raw_result),
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time,
            sampler_name='emcee',
            point_estimate_name='best_sample',
            posterior_samples=getattr(raw_result, 'posterior_samples', None),
            posterior_parameter_summaries=getattr(raw_result, 'posterior_parameter_summaries', []),
            posterior_predictive={},
            credible_interval_levels=(0.68, 0.95),
            sampler_settings=getattr(raw_result, 'sampler_settings', {}),
            convergence_diagnostics=getattr(raw_result, 'convergence_diagnostics', {}),
            sampler_completed=getattr(raw_result, 'sampler_completed', False),
            best_log_posterior=getattr(raw_result, 'best_log_posterior', None),
        )
        fit_results.message = getattr(raw_result, 'message', '')
        fit_results.iterations = int(fit_results.sampler_settings.get('steps', self.nsteps))
        fit_results.result = raw_result
        return fit_results

    def _check_success(self, raw_result: object) -> bool:  # noqa: PLR6301
        """Determine success from normalized emcee result."""
        return bool(getattr(raw_result, 'success', False))
