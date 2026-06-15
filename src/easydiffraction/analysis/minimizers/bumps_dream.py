# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bumps minimizer variant using the DREAM sampler."""

from __future__ import annotations

import math
import multiprocessing
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from bumps.fitproblem import FitProblem
from bumps.fitters import FITTERS
from bumps.fitters import FitDriver
from bumps.fitters import monitor as bumps_monitor
from bumps.mapper import MPMapper
from bumps.mapper import can_pickle
from scipy.optimize import OptimizeResult

from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
from easydiffraction.analysis.fit_helpers.bayesian import compute_convergence_diagnostics
from easydiffraction.analysis.fit_helpers.bayesian import standard_deviations_from_summaries
from easydiffraction.analysis.fit_helpers.bayesian import summarize_posterior_parameters
from easydiffraction.analysis.fit_helpers.tracking import SamplerProgressUpdate
from easydiffraction.analysis.minimizers.base import MinimizerFitOptions
from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
from easydiffraction.analysis.minimizers.bumps import _EasyDiffractionFitness
from easydiffraction.analysis.minimizers.enums import DreamPopulationInitializationEnum
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import log

_BUMPS_DREAM_LOG = log

DEFAULT_METHOD = 'dream'
DEFAULT_MAX_ITERATIONS = 3000
DEFAULT_BURN_FRACTION = 0.2
DEFAULT_MIN_BURN = 50
DEFAULT_THIN = 1
DEFAULT_POP = 4
DEFAULT_PARALLEL = 0
DEFAULT_INIT = DreamPopulationInitializationEnum.LHS
DEFAULT_ALPHA = 0.0
DEFAULT_OUTLIER_TEST = 'none'
DEFAULT_TRIM = False
MAX_RANDOM_SEED = int(np.iinfo(np.uint32).max)
TOTAL_PROGRESS_POINTS = 25
DREAM_SAMPLE_ARRAY_NDIM = 3
DREAM_DRIVER_FAILURES = (ArithmeticError, RuntimeError, TypeError, ValueError)

# Top-level HDF5 group in the MCMC sidecar (mcmc.h5) holding the
# resumable bumps-DREAM sampler state, alongside emcee's emcee_chain.
DREAM_STATE_GROUP = 'dream_state'


def _write_dream_state_sidecar(
    sidecar_path: Path,
    state: object,
    parameter_names: list[str],
) -> None:
    """
    Persist a DREAM ``MCMCDraw`` state into the MCMC sidecar.

    The state is written under ``/dream_state/state`` via the bumps
    ``DreamFit.h5dump`` contract, with the fitted-parameter names stored
    in a sibling ``/dream_state/param_names`` dataset so resume can
    match by name (bumps does not preserve labels through its own
    save/load).

    Parameters
    ----------
    sidecar_path : Path
        Path to the ``mcmc.h5`` sidecar file.
    state : object
        The bumps ``MCMCDraw`` object captured from ``driver.fitter``.
    parameter_names : list[str]
        Fitted-parameter names, in sampling order.
    """
    import h5py  # noqa: PLC0415
    from bumps.fitters import DreamFit  # noqa: PLC0415

    sidecar_path = Path(sidecar_path)
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(str(sidecar_path), 'a') as handle:
        if DREAM_STATE_GROUP in handle:
            del handle[DREAM_STATE_GROUP]
        group = handle.create_group(DREAM_STATE_GROUP)
        DreamFit.h5dump(group.create_group('state'), state)
        group.create_dataset(
            'param_names',
            data=np.array(parameter_names, dtype=h5py.string_dtype(encoding='utf-8')),
        )


def _read_dream_state_sidecar(sidecar_path: Path) -> tuple[object, list[str]] | None:
    """
    Read a persisted DREAM state from the MCMC sidecar.

    Returns the bumps ``MCMCDraw`` state and the stored fitted-parameter
    names, or ``None`` when the sidecar or its ``dream_state`` group is
    absent.

    Parameters
    ----------
    sidecar_path : Path
        Path to the ``mcmc.h5`` sidecar file.

    Returns
    -------
    tuple[object, list[str]] | None
        ``(state, param_names)`` when present, otherwise ``None``.

    Raises
    ------
    ValueError
        If the ``dream_state`` group is present but malformed.
    """
    import h5py  # noqa: PLC0415
    from bumps.fitters import DreamFit  # noqa: PLC0415

    sidecar_path = Path(sidecar_path)
    if not sidecar_path.is_file():
        return None
    with h5py.File(str(sidecar_path), 'r') as handle:
        if DREAM_STATE_GROUP not in handle:
            return None
        group = handle[DREAM_STATE_GROUP]
        if 'state' not in group or 'param_names' not in group:
            msg = f"Malformed '{DREAM_STATE_GROUP}' group in '{sidecar_path}'."
            raise ValueError(msg)
        state = DreamFit.h5load(group['state'])
        param_names = [
            name.decode('utf-8') if isinstance(name, bytes) else str(name)
            for name in group['param_names'][()]
        ]
    return state, param_names


@dataclass(slots=True)
class _DreamRunContext:
    """Prepared driver state and metadata for one DREAM run."""

    driver: FitDriver
    parameter_names: list[str]
    parameter_display_names: list[str]
    parameter_uids: list[str]
    sampler_settings: dict[str, object]
    starting_values: np.ndarray
    starting_uncertainties: list[float | None]


@dataclass(slots=True)
class _DreamDriverResult:
    """
    Raw driver outcome captured before EasyDiffraction normalization.
    """

    best_values: object | None
    best_nllf: float | None
    raw_state: object | None
    error: Exception | None = None


class _DreamProgressMonitor(bumps_monitor.Monitor):
    """
    Progress monitor translating DREAM updates into chi-square rows.
    """

    def __init__(
        self,
        *,
        tracker: object,
        n_points: int,
        n_parameters: int,
        total_generations: int,
        burn_steps: int,
    ) -> None:
        """Precompute per-phase progress targets for reporting."""
        self._tracker = tracker
        self._n_points = n_points
        self._n_parameters = n_parameters
        self._total_generations = max(1, total_generations)
        self._burn_steps = max(0, burn_steps)
        burn_target_count, sampling_target_count = self._phase_progress_point_counts(
            total_generations=self._total_generations,
            burn_steps=self._burn_steps,
        )
        self._burn_targets = self._progress_targets(
            start=1,
            stop=self._burn_steps,
            target_count=burn_target_count,
        )
        self._sampling_targets = self._progress_targets(
            start=self._burn_steps + 1,
            stop=self._total_generations,
            target_count=sampling_target_count,
        )
        self._next_burn_target_index = 0
        self._next_sampling_target_index = 0

    @staticmethod
    def config_history(history: object) -> None:
        """Declare the history fields needed for progress updates."""
        history.requires(time=1, step=1, value=1, population_values=1)

    def __call__(self, history: object) -> None:
        """Forward sampler progress to the shared fit tracker."""
        step = int(history.step[0]) if history.step else 0
        generation = max(1, step)
        if not self._should_report(generation):
            return
        nllf = float(history.value[0])
        reduced_chi2 = self._reduced_chi_square_from_nllf(nllf)
        log_posterior = self._population_mean_log_posterior(history)
        self._tracker.track_sampler_progress(
            SamplerProgressUpdate(
                iteration=generation,
                total_iterations=self._total_generations,
                phase=self._phase_name(generation),
                progress_percent=self._progress_percent(generation),
                log_posterior=log_posterior,
                reduced_chi2=reduced_chi2,
                elapsed_time=float(history.time[0]),
                force_report=True,
            )
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
            SamplerProgressUpdate(
                iteration=generation,
                total_iterations=self._total_generations,
                phase=self._phase_name(generation),
                progress_percent=self._progress_percent(generation),
                log_posterior=self._population_mean_log_posterior(history),
                reduced_chi2=reduced_chi2,
                elapsed_time=float(history.time[0]),
                force_report=True,
            )
        )

    @staticmethod
    def _progress_targets(
        *,
        start: int,
        stop: int,
        target_count: int,
    ) -> list[int]:
        """
        Return monotonically increasing reporting targets for one phase.
        """
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

    @staticmethod
    def _phase_progress_point_counts(
        *,
        total_generations: int,
        burn_steps: int,
    ) -> tuple[int, int]:
        """Return proportional burn and sampling progress counts."""
        total_points = min(TOTAL_PROGRESS_POINTS, max(1, total_generations))
        burn_generations = min(max(0, burn_steps), total_generations)
        sampling_generations = max(total_generations - burn_generations, 0)

        if burn_generations == 0:
            return 0, total_points
        if sampling_generations == 0:
            return total_points, 0

        burn_target_count = round(total_points * burn_generations / total_generations)
        burn_target_count = min(
            max(burn_target_count, 1),
            burn_generations,
            total_points - 1,
        )
        sampling_target_count = min(
            max(total_points - burn_target_count, 1),
            sampling_generations,
        )
        return burn_target_count, sampling_target_count

    def _should_report(self, generation: int) -> bool:
        """Return whether the current generation should be rendered."""
        clamped_generation = min(max(1, generation), self._total_generations)
        if self._phase_name(clamped_generation) == 'burn-in':
            return self._consume_progress_target(
                clamped_generation,
                phase_targets=self._burn_targets,
                target_index_name='_next_burn_target_index',
            )

        return self._consume_progress_target(
            clamped_generation,
            phase_targets=self._sampling_targets,
            target_index_name='_next_sampling_target_index',
        )

    def _consume_progress_target(
        self,
        generation: int,
        *,
        phase_targets: list[int],
        target_index_name: str,
    ) -> bool:
        """
        Advance a phase target pointer when the generation reaches it.
        """
        target_index = getattr(self, target_index_name)
        should_report = False
        while target_index < len(phase_targets) and generation >= phase_targets[target_index]:
            target_index += 1
            should_report = True
        setattr(self, target_index_name, target_index)
        return should_report

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
        """Return the mean log-posterior across the population."""
        population_values = history.population_values[0] if history.population_values else None
        if population_values is None:
            return -float(history.value[0])

        nllf_values = np.asarray(population_values, dtype=float)
        finite_mask = np.isfinite(nllf_values)
        if not np.any(finite_mask):
            return -float(history.value[0])
        return float(np.mean(-nllf_values[finite_mask]))

    def _reduced_chi_square_from_nllf(self, nllf: float) -> float:
        """
        Convert DREAM's negative log-likelihood to reduced chi-square.
        """
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

    # Set by Fitter._set_minimizer_sidecar_path when a project path is
    # known; enables persisting/resuming the DREAM state in mcmc.h5.
    _sidecar_path: Path | None = None

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS_DREAM,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        """Initialize the DREAM minimizer with sampler defaults."""
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
        self._burn: int | None = None
        self._thin: int = DEFAULT_THIN
        self._pop: int = DEFAULT_POP
        self._parallel: int = DEFAULT_PARALLEL
        self._init: DreamPopulationInitializationEnum = DEFAULT_INIT

    @property
    def max_iterations(self) -> int:
        """DREAM exposes sampler length through ``steps`` instead."""
        sampler_name = self.type_info.description.partition('with ')[2].split()[0]
        msg = f"{sampler_name} sampler uses 'steps' instead of 'max_iterations'."
        raise AttributeError(msg)

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        """Reject ``max_iterations``; DREAM uses ``steps`` instead."""
        del value
        sampler_name = self.type_info.description.partition('with ')[2].split()[0]
        msg = f"{sampler_name} sampler uses 'steps' instead of 'max_iterations'."
        raise AttributeError(msg)

    @property
    def steps(self) -> int:
        """Number of DREAM generations retained after burn-in."""
        return self._validated_positive_integer('steps', self._max_iterations)

    @steps.setter
    def steps(self, value: int) -> None:
        """Set the number of DREAM generations after burn-in."""
        self._max_iterations = self._validated_positive_integer('steps', value)

    @property
    def burn(self) -> int | None:
        """Explicit DREAM burn-in generations or ``None`` for auto."""
        return self._burn

    @burn.setter
    def burn(self, value: int | None) -> None:
        """Set explicit DREAM burn-in generations, or ``None``."""
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
        """Set the DREAM thinning interval."""
        self._thin = self._validated_positive_integer('thin', value)

    @property
    def pop(self) -> int:
        """DREAM population multiplier."""
        return self._pop

    @pop.setter
    def pop(self, value: int) -> None:
        """Set the DREAM population multiplier."""
        self._pop = self._validated_positive_integer('pop', value)

    @property
    def chains(self) -> int:
        """
        Friendly alias for ``pop``, the DREAM population scale factor.

        DREAM runs ``ceil(chains * n_parameters)`` parallel chains, so
        ``chains`` is a per-parameter multiplier rather than an absolute
        chain count.
        """
        return self.pop

    @chains.setter
    def chains(self, value: int) -> None:
        """Set the DREAM population scale factor (alias for ``pop``)."""
        self.pop = value

    @property
    def parallel(self) -> int:
        """DREAM parallel worker count; ``0`` uses all CPUs."""
        return self._parallel

    @parallel.setter
    def parallel(self, value: int) -> None:
        """Set the DREAM parallel worker count."""
        self._parallel = self._validated_non_negative_integer('parallel', value)

    @property
    def init(self) -> DreamPopulationInitializationEnum:
        """DREAM population initializer."""
        return self._init

    @init.setter
    def init(self, value: DreamPopulationInitializationEnum | str) -> None:
        """Set the DREAM population initializer."""
        self._init = self._validated_init(value)

    def _resolve_random_seed(self, random_seed: int | None) -> int:
        """
        Return a user-provided or generated random seed.

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

        integer_seed = self._validated_random_seed_value(random_seed)

        self._resolved_random_seed = integer_seed
        return self._resolved_random_seed

    @staticmethod
    def _validated_random_seed_value(random_seed: object) -> int:
        """Validate and normalize a DREAM random seed."""
        if isinstance(random_seed, bool):
            msg = f'DREAM random_seed must be an integer between 0 and {MAX_RANDOM_SEED}.'
            raise TypeError(msg)

        integer_seed = int(random_seed)
        if integer_seed != random_seed or integer_seed < 0 or integer_seed > MAX_RANDOM_SEED:
            msg = f'DREAM random_seed must be an integer between 0 and {MAX_RANDOM_SEED}.'
            raise ValueError(msg)
        return integer_seed

    @staticmethod
    def _tracking_mode() -> str:
        """Use sampler-style progress reporting for DREAM runs."""
        return 'sampling'

    def _prepare_solver_args(
        self,
        parameters: list[object],
    ) -> dict[str, object]:
        """
        Prepare DREAM solver arguments in EasyDiffraction order.

        Parameters
        ----------
        parameters : list[object]
            List of parameters to be sampled.

        Returns
        -------
        dict[str, object]
            BUMPS parameters plus EasyDiffraction parameter metadata.
        """
        self._validate_sampled_parameter_bounds(parameters)
        solver_args = super()._prepare_solver_args(parameters)
        solver_args['parameter_names'] = [parameter.unique_name for parameter in parameters]
        solver_args['parameter_display_names'] = [
            getattr(parameter, 'name', parameter.unique_name) for parameter in parameters
        ]
        solver_args['parameter_uids'] = [parameter._minimizer_uid for parameter in parameters]
        solver_args['starting_uncertainties'] = [parameter.uncertainty for parameter in parameters]
        return solver_args

    @classmethod
    def _validate_sampled_parameter_bounds(
        cls,
        parameters: list[object],
    ) -> None:
        """
        Validate finite ordered bounds for sampled DREAM parameters.
        """
        issues: list[str] = []
        for parameter in parameters:
            parameter_name = cls._parameter_name_for_bound_validation(parameter)
            parameter_issues = cls._parameter_bound_issues(parameter)
            if parameter_issues:
                issues.append(f'- {parameter_name}: {"; ".join(parameter_issues)}')

        if not issues:
            return

        message = 'DREAM requires finite valid bounds for every sampled parameter:\n' + '\n'.join(
            issues
        )
        raise ValueError(message)

    @staticmethod
    def _parameter_name_for_bound_validation(parameter: object) -> str:
        """Return the user-facing name for DREAM bound validation."""
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
        """Validate a DREAM setting that must be a positive integer."""
        if isinstance(value, bool):
            msg = f"DREAM setting '{name}' must be a positive integer."
            raise TypeError(msg)

        integer_value = int(value)
        if integer_value != value or integer_value < 1:
            msg = f"DREAM setting '{name}' must be a positive integer."
            raise ValueError(msg)
        return integer_value

    @staticmethod
    def _validated_non_negative_integer(name: str, value: float) -> int:
        """
        Validate a DREAM setting that must be a non-negative integer.
        """
        if isinstance(value, bool):
            msg = f"DREAM setting '{name}' must be a non-negative integer."
            raise TypeError(msg)

        integer_value = int(value)
        if integer_value != value or integer_value < 0:
            msg = f"DREAM setting '{name}' must be a non-negative integer."
            raise ValueError(msg)
        return integer_value

    @staticmethod
    def _validated_init(
        value: DreamPopulationInitializationEnum | str,
    ) -> DreamPopulationInitializationEnum:
        """Validate a DREAM population initializer."""
        try:
            return DreamPopulationInitializationEnum(value)
        except ValueError:
            valid_values = ', '.join(
                initialization.value for initialization in DreamPopulationInitializationEnum
            )
            msg = f"DREAM setting 'init' must be one of: {valid_values}."
            raise ValueError(msg) from None

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
        n_parameters: int,
        samples_override: int | None = None,
        pop_override: int | None = None,
    ) -> dict[str, object]:
        """Build the sampler settings dictionary recorded in results."""
        pop = self.pop if pop_override is None else int(pop_override)
        samples = steps * pop * n_parameters if samples_override is None else int(samples_override)
        return {
            'random_seed': int(random_seed),
            'steps': int(steps),
            'burn': int(burn),
            'thin': int(self.thin),
            'pop': int(pop),
            'parallel': int(self.parallel),
            'init': self.init.value,
            'samples': int(samples),
            'alpha': float(DEFAULT_ALPHA),
            'outliers': DEFAULT_OUTLIER_TEST,
            'trim': DEFAULT_TRIM,
        }

    def fit(
        self,
        parameters: list[object],
        objective_function: object,
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
        *,
        options: MinimizerFitOptions | None = None,
    ) -> BayesianFitResults:
        """
        Run DREAM sampling and return Bayesian fit results.

        Overrides the base ``fit`` so bumps-DREAM supports resume:
        ``resume`` and ``extra_steps`` are threaded into the solver,
        which extends the saved chain instead of starting cold.
        """
        fit_options = options or MinimizerFitOptions()
        if fit_options.use_physical_limits:
            self._apply_physical_limits(parameters)

        resolved_random_seed = self._resolve_random_seed(fit_options.random_seed)
        minimizer_name = self.name or 'Unnamed Minimizer'
        if self.method is not None and f'({self.method})' not in minimizer_name:
            minimizer_name += f' ({self.method})'
        self._start_tracking(minimizer_name, verbosity=verbosity)

        try:
            solver_args = self._prepare_solver_args(parameters)
            solver_args['random_seed'] = resolved_random_seed
            solver_args['resume'] = fit_options.resume
            solver_args['extra_steps'] = fit_options.extra_steps
            raw_result = self._run_solver(objective_function, **solver_args)
            return self._finalize_fit(parameters, raw_result)
        finally:
            if fit_options.finalize_tracking:
                self._stop_tracking()

    def _run_solver(
        self,
        objective_function: object,
        **kwargs: object,
    ) -> object:
        """
        Run the DREAM sampler and normalize its posterior outputs.

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
        resume = bool(kwargs.get('resume'))
        resume_overrides: dict[str, object] = {}
        fit_state = None
        if resume:
            resume_overrides, fit_state = self._prepare_dream_resume(
                kwargs=kwargs,
                extra_steps=kwargs.get('extra_steps'),
            )
            total_iterations = int(resume_overrides['steps_override'] + 1)
        else:
            total_iterations = int(self.steps + self._resolved_burn(self.steps) + 1)
        self.tracker.start_sampler_pre_processing(total_iterations=total_iterations)
        context = self._prepare_run_context(
            objective_function=objective_function,
            kwargs=kwargs,
            **resume_overrides,
        )
        driver_result = self._execute_driver(
            driver=context.driver,
            random_seed=int(context.sampler_settings['random_seed']),
            fit_state=fit_state,
        )
        if driver_result.error is not None:
            return self._failure_result(
                context=context,
                message=f'DREAM sampling failed: {driver_result.error}',
                raw_state=driver_result.raw_state,
                sampler_completed=False,
            )
        if driver_result.best_values is None or driver_result.raw_state is None:
            return self._failure_result(
                context=context,
                message='DREAM sampling did not produce usable posterior samples.',
                raw_state=driver_result.raw_state,
                sampler_completed=False,
            )

        self.tracker.start_sampler_post_processing()

        self._persist_dream_state(
            raw_state=driver_result.raw_state,
            parameter_names=context.parameter_names,
        )

        return self._build_success_result(
            context=context,
            raw_state=driver_result.raw_state,
            best_nllf=driver_result.best_nllf,
        )

    def _persist_dream_state(self, *, raw_state: object, parameter_names: object) -> None:
        """
        Write the DREAM sampler state to the sidecar when configured.
        """
        if self._sidecar_path is None:
            return
        _write_dream_state_sidecar(
            Path(self._sidecar_path),
            raw_state,
            [str(name) for name in parameter_names],
        )

    def _prepare_dream_resume(
        self,
        *,
        kwargs: dict[str, object],
        extra_steps: object,
    ) -> tuple[dict[str, object], object]:
        """
        Load and validate saved DREAM state for a resume run.

        Returns the driver overrides (extending the chain by
        ``extra_steps`` generations via the ring-buffer contract) and a
        deep-copied ``fit_state`` for ``FitDriver.fit``. The deep copy
        is required because bumps mutates the state in place.
        """
        import copy  # noqa: PLC0415

        if not isinstance(extra_steps, int) or isinstance(extra_steps, bool) or extra_steps <= 0:
            msg = 'Resuming a bumps-dream fit requires a positive integer extra_steps.'
            raise ValueError(msg)
        if self._sidecar_path is None:
            msg = 'bumps-dream resume requires a saved project; no sidecar path is set.'
            raise ValueError(msg)
        loaded = _read_dream_state_sidecar(Path(self._sidecar_path))
        if loaded is None:
            msg = 'No saved bumps-dream chain to resume; run a fresh fit first.'
            raise ValueError(msg)
        state, saved_names = loaded

        parameter_names = [str(name) for name in kwargs.get('parameter_names')]
        n_parameters = len(parameter_names)
        pop_scale = int(self.pop)
        self._validate_dream_resume(
            state=state,
            saved_names=saved_names,
            names=parameter_names,
            pop_scale=pop_scale,
            n_parameters=n_parameters,
        )
        current_steps = self._state_generations(
            state=state, pop_scale=pop_scale, n_parameters=n_parameters
        )
        target_steps = current_steps + int(extra_steps)
        overrides = {
            'steps_override': target_steps,
            'burn_override': 0,
            'samples_override': target_steps * pop_scale * n_parameters,
            'pop_override': pop_scale,
        }
        return overrides, copy.deepcopy(state)

    @staticmethod
    def _validate_dream_resume(
        *,
        state: object,
        saved_names: list[str],
        names: list[str],
        pop_scale: int,
        n_parameters: int,
    ) -> None:
        """
        Reject a resume whose model does not match the saved chain.

        Mismatched free-parameter count, names/order, or population are
        all rejected — the population, in particular, cannot change on
        resume (bumps resumes positionally into a fixed chain count).
        """
        if int(state.Nvar) != len(names):
            msg = (
                f'Saved bumps-dream chain has {int(state.Nvar)} parameters but the current '
                f'model has {len(names)}. The free-parameter set must match to resume.'
            )
            raise ValueError(msg)
        if saved_names and list(saved_names) != list(names):
            msg = (
                'Parameter names/order differ between the current model and the saved '
                f'bumps-dream chain.\n  current: {names}\n  saved:   {list(saved_names)}'
            )
            raise ValueError(msg)
        expected_npop = math.ceil(pop_scale * n_parameters)
        if expected_npop != int(state.Npop):
            msg = (
                f'Requested population (chains={pop_scale}) would produce {expected_npop} '
                f'chains, but the saved bumps-dream chain has {int(state.Npop)}. The '
                'population cannot change on resume; reset chains/population_size to match '
                'the saved chain.'
            )
            raise ValueError(msg)

    @staticmethod
    def _state_generations(*, state: object, pop_scale: int, n_parameters: int) -> int:
        """Return the number of generations stored in a saved state."""
        total_draws = int(state.draw().points.shape[0])
        pop_size = max(pop_scale * n_parameters, 1)
        return max(total_draws // pop_size, 1)

    def _prepare_run_context(
        self,
        *,
        objective_function: object,
        kwargs: dict[str, object],
        steps_override: int | None = None,
        burn_override: int | None = None,
        samples_override: int | None = None,
        pop_override: int | None = None,
    ) -> _DreamRunContext:
        """
        Prepare a driver and metadata for one DREAM solver run.

        The ``*_override`` arguments are set only on a resume run, where
        they extend the saved chain (see ``_prepare_dream_resume``); a
        fresh run leaves them ``None`` and uses the configured settings.
        """
        bumps_params = kwargs.get('bumps_params')
        parameter_names = kwargs.get('parameter_names')
        parameter_display_names = kwargs.get('parameter_display_names')
        parameter_uids = kwargs.get('parameter_uids')
        random_seed = int(kwargs.get('random_seed'))
        starting_uncertainties = kwargs.get('starting_uncertainties')

        fitness = _EasyDiffractionFitness(bumps_params, objective_function)
        fitness.nllf()
        fitclass = next(cls for cls in FITTERS if cls.id == self.method)
        steps = self.steps if steps_override is None else int(steps_override)
        burn = self._resolved_burn(self.steps) if burn_override is None else int(burn_override)
        init = self.init
        sampler_settings = self._sampler_settings(
            random_seed=random_seed,
            steps=steps,
            burn=burn,
            n_parameters=len(bumps_params),
            samples_override=samples_override,
            pop_override=pop_override,
        )
        driver = self._build_driver(
            fitclass=fitclass,
            fitness=fitness,
            steps=steps,
            burn=burn,
            init=init,
            sampler_settings=sampler_settings,
            n_parameters=len(bumps_params),
        )
        starting_values = np.array([parameter.value for parameter in bumps_params], dtype=float)
        resolved_uncertainties = (
            list(starting_uncertainties)
            if starting_uncertainties is not None
            else [None] * len(bumps_params)
        )
        return _DreamRunContext(
            driver=driver,
            parameter_names=parameter_names,
            parameter_display_names=parameter_display_names,
            parameter_uids=parameter_uids,
            sampler_settings=sampler_settings,
            starting_values=starting_values,
            starting_uncertainties=resolved_uncertainties,
        )

    def _build_driver(
        self,
        *,
        fitclass: object,
        fitness: object,
        steps: int,
        burn: int,
        init: DreamPopulationInitializationEnum,
        sampler_settings: dict[str, object],
        n_parameters: int,
    ) -> FitDriver:
        """Build and clip the BUMPS DREAM driver."""
        total_generations = int(steps + burn + 1)
        problem = FitProblem(fitness)
        progress_monitor = _DreamProgressMonitor(
            tracker=self.tracker,
            n_points=fitness.numpoints(),
            n_parameters=n_parameters,
            total_generations=total_generations,
            burn_steps=int(burn),
        )
        mapper = self._build_mapper(problem)
        try:
            driver = FitDriver(
                fitclass=fitclass,
                problem=problem,
                monitors=[progress_monitor],
                mapper=mapper,
                steps=steps,
                burn=burn,
                thin=self.thin,
                pop=int(sampler_settings['pop']),
                init=init.value,
                samples=sampler_settings['samples'],
                alpha=DEFAULT_ALPHA,
                outliers=DEFAULT_OUTLIER_TEST,
                trim=DEFAULT_TRIM,
            )
            driver.clip()
        except KeyboardInterrupt:
            MPMapper.stop_mapper()
            raise
        except Exception:
            MPMapper.stop_mapper()
            raise
        else:
            return driver

    def _build_mapper(self, problem: FitProblem) -> object | None:
        """Return a DREAM mapper for the configured parallel setting."""
        if self.parallel == 1:
            return None

        if self._requires_serial_mapper_for_spawn_main_module():
            self._warn_after_tracking(
                'DREAM parallel evaluation requires an import-safe main '
                'module on spawn-based multiprocessing; falling back to '
                'serial execution.'
            )
            return None

        shared_display_handle = getattr(self.tracker, '_shared_display_handle', None)
        activity_indicator = getattr(self.tracker, '_activity_indicator', None)
        if shared_display_handle is not None:
            self.tracker._set_shared_display_handle(None)
        if activity_indicator is not None:
            self.tracker._activity_indicator = None

        try:
            if not can_pickle(problem):
                self._warn_after_tracking(
                    'DREAM parallel evaluation requires a picklable '
                    'problem; falling back to serial execution.'
                )
                return None

            return MPMapper.start_mapper(problem, [], cpus=self.parallel)
        except RuntimeError as error:
            message = str(error)
            if 'bootstrapping phase' not in message:
                raise
            self._warn_after_tracking(
                'DREAM parallel evaluation requires an import-safe main '
                'module on spawn-based multiprocessing; falling back to '
                'serial execution.'
            )
            return None
        finally:
            if activity_indicator is not None:
                self.tracker._activity_indicator = activity_indicator
            if shared_display_handle is not None:
                self.tracker._set_shared_display_handle(shared_display_handle)

    @staticmethod
    def _requires_serial_mapper_for_spawn_main_module() -> bool:
        """
        Return whether direct-script spawn startup should stay serial.
        """
        start_method = multiprocessing.get_start_method(allow_none=True)
        if start_method is None:
            start_method = multiprocessing.get_start_method()
        if start_method != 'spawn':
            return False

        main_module = sys.modules.get('__main__')
        if main_module is None:
            return False

        return (
            getattr(main_module, '__file__', None) is not None
            and getattr(main_module, '__spec__', None) is None
        )

    @staticmethod
    def _execute_driver(
        *, driver: FitDriver, random_seed: int, fit_state: object | None = None
    ) -> _DreamDriverResult:
        """
        Run the DREAM driver under a deterministic RNG-state guard.

        ``fit_state`` is a deep-copied saved ``MCMCDraw`` on a resume
        run (``None`` for a fresh run); it is passed to
        ``FitDriver.fit`` so DREAM continues the existing chain.
        """
        numpy_rng = np.random.mtrand._rand
        numpy_state = numpy_rng.get_state()
        python_state = random.getstate()
        try:
            validated_seed = BumpsDreamMinimizer._validated_random_seed_value(random_seed)
            numpy_rng.seed(validated_seed)
            random.seed(validated_seed)
            fit_kwargs = {} if fit_state is None else {'fit_state': fit_state}
            best_values, best_nllf = driver.fit(**fit_kwargs)
        except DREAM_DRIVER_FAILURES as error:  # pragma: no cover - backend-specific
            return _DreamDriverResult(
                best_values=None,
                best_nllf=None,
                raw_state=getattr(driver.fitter, 'state', None),
                error=error,
            )
        finally:
            MPMapper.stop_mapper()
            numpy_rng.set_state(numpy_state)
            random.setstate(python_state)

        return _DreamDriverResult(
            best_values=best_values,
            best_nllf=float(best_nllf),
            raw_state=getattr(driver.fitter, 'state', None),
        )

    @staticmethod
    def _failure_result(
        *,
        context: _DreamRunContext,
        message: str,
        raw_state: object,
        sampler_completed: bool,
    ) -> OptimizeResult:
        """
        Build a normalized failure result for an incomplete DREAM run.
        """
        return OptimizeResult(
            x=context.starting_values,
            dx=None,
            fun=None,
            success=False,
            status=-1,
            message=message,
            var_names=context.parameter_names,
            posterior_samples=None,
            posterior_parameter_summaries=[],
            convergence_diagnostics={},
            sampler_settings=context.sampler_settings,
            sampler_completed=sampler_completed,
            raw_state=raw_state,
            best_log_posterior=None,
            starting_values=context.starting_values,
            starting_uncertainties=context.starting_uncertainties,
        )

    def _build_success_result(
        self,
        *,
        context: _DreamRunContext,
        raw_state: object,
        best_nllf: float | None,
    ) -> OptimizeResult:
        """Normalize a completed DREAM run into an OptimizeResult."""
        draw_index, parameter_samples_array, log_posterior = raw_state.chains()
        if (
            parameter_samples_array.ndim != DREAM_SAMPLE_ARRAY_NDIM
            or parameter_samples_array.size == 0
        ):
            return self._failure_result(
                context=context,
                message='DREAM sampling did not return a usable posterior sample array.',
                raw_state=raw_state,
                sampler_completed=True,
            )

        state_best_values, best_log_posterior = raw_state.best()
        best_by_name = dict(zip(raw_state.labels, state_best_values, strict=True))
        label_to_index = {label: index for index, label in enumerate(raw_state.labels)}
        ordered_indices = [label_to_index[uid] for uid in context.parameter_uids]
        ordered_samples = np.asarray(parameter_samples_array, dtype=float)[:, :, ordered_indices]
        best_sample_values = np.array(
            [best_by_name[uid] for uid in context.parameter_uids],
            dtype=float,
        )
        posterior_samples = PosteriorSamples(
            parameter_names=context.parameter_names,
            parameter_samples=ordered_samples,
            log_posterior=np.asarray(log_posterior, dtype=float),
            draw_index=np.asarray(draw_index, dtype=float),
        )
        convergence_diagnostics = compute_convergence_diagnostics(posterior_samples)
        if not convergence_diagnostics.get('converged', True):
            self._warn_after_tracking(
                'Convergence diagnostics indicate the posterior may be poorly mixed.'
            )
        posterior_parameter_summaries = summarize_posterior_parameters(
            parameter_names=context.parameter_names,
            posterior_samples=posterior_samples,
            best_sample_values=best_sample_values,
            parameter_display_names=context.parameter_display_names,
            convergence_diagnostics=convergence_diagnostics,
        )
        posterior_standard_deviations = standard_deviations_from_summaries(
            posterior_parameter_summaries
        )

        return OptimizeResult(
            x=best_sample_values,
            dx=posterior_standard_deviations,
            fun=float(best_nllf),
            success=True,
            status=0,
            message='DREAM sampling completed',
            var_names=context.parameter_names,
            posterior_samples=posterior_samples,
            posterior_parameter_summaries=posterior_parameter_summaries,
            convergence_diagnostics=convergence_diagnostics,
            sampler_settings=context.sampler_settings,
            sampler_completed=True,
            raw_state=raw_state,
            best_log_posterior=float(best_log_posterior),
            starting_values=context.starting_values,
            starting_uncertainties=context.starting_uncertainties,
        )

    @staticmethod
    def _sync_result_to_parameters(
        parameters: list[object],
        raw_result: object,
    ) -> None:
        """
        Sync best posterior values or restore starts.

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
        """
        Build the Bayesian fit result container.

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
        fit_results.iterations = int(fit_results.sampler_settings.get('steps', self.steps))
        fit_results.result = raw_result
        return fit_results
