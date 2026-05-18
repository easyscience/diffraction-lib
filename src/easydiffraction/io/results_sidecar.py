# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit sidecar read/write helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from easydiffraction.utils.logging import log

_DEFAULT_SIDECAR_FILE_NAME = 'results.h5'
_POSTERIOR_PARAMETER_SAMPLES_PATH = '/posterior/parameter_samples'
_POSTERIOR_LOG_POSTERIOR_PATH = '/posterior/log_posterior'
_POSTERIOR_DRAW_INDEX_PATH = '/posterior/draw_index'
_POSTERIOR_SAMPLE_NDIM = 3
_PREDICTIVE_DRAWS_NDIM = 2


def _normalized_hdf5_path(path: str) -> str:
    """Return an HDF5 path without a leading slash."""
    return path.lstrip('/')


def _sidecar_file_name(analysis: object) -> str:
    """Return the configured sidecar file name for an analysis."""
    bayesian_result = getattr(analysis, 'bayesian_result', None)
    if bayesian_result is None:
        return _DEFAULT_SIDECAR_FILE_NAME

    file_name = bayesian_result.sidecar_file.value
    if not isinstance(file_name, str) or not file_name.strip():
        return _DEFAULT_SIDECAR_FILE_NAME

    normalized_name = file_name.strip()
    normalized_path = Path(normalized_name)
    if (
        normalized_path.is_absolute()
        or normalized_path.name in {'', '.', '..'}
        or normalized_path.name != normalized_name
    ):
        log.warning(
            'Ignoring Bayesian sidecar file path outside the analysis directory: '
            f'{normalized_name!r}. Using {_DEFAULT_SIDECAR_FILE_NAME!r} instead.'
        )
        return _DEFAULT_SIDECAR_FILE_NAME

    return normalized_path.name


def _sidecar_path(*, analysis: object, analysis_dir: Path) -> Path:
    """Return the results sidecar path inside the analysis directory."""
    resolved_analysis_dir = analysis_dir.resolve()
    sidecar_path = (resolved_analysis_dir / _sidecar_file_name(analysis)).resolve()
    if sidecar_path.parent != resolved_analysis_dir:
        log.warning(
            'Resolved Bayesian sidecar file path escaped the analysis directory. '
            f'Using {_DEFAULT_SIDECAR_FILE_NAME!r} instead.'
        )
        return resolved_analysis_dir / _DEFAULT_SIDECAR_FILE_NAME
    return sidecar_path


def _should_use_sidecar(analysis: object) -> bool:
    """
    Return whether the analysis currently expects a Bayesian sidecar.
    """
    has_fit_state = getattr(analysis, '_has_persisted_fit_state', None)
    if not callable(has_fit_state) or not has_fit_state():
        return False

    if analysis.fit_result.result_kind.value != 'bayesian':
        return False

    return any((
        analysis.bayesian_result.has_posterior_samples.value,
        len(analysis.bayesian_distribution_caches) > 0,
        len(analysis.bayesian_pair_caches) > 0,
        len(analysis.bayesian_predictive_datasets) > 0,
    ))


def _delete_stale_sidecar(sidecar_path: Path) -> None:
    """
    Delete an existing sidecar when no persisted arrays should remain.
    """
    if sidecar_path.is_file():
        sidecar_path.unlink()


def _create_dataset(handle: object, path: str, data: np.ndarray) -> None:
    """Create or replace one dataset in an open HDF5 file."""
    normalized_path = _normalized_hdf5_path(path)
    group_name, _, dataset_name = normalized_path.rpartition('/')
    group = handle.require_group(group_name) if group_name else handle
    if dataset_name in group:
        del group[dataset_name]
    group.create_dataset(dataset_name, data=data)


def _read_dataset(handle: object, path: str) -> np.ndarray | None:
    """Read one dataset from an open HDF5 file when it exists."""
    normalized_path = _normalized_hdf5_path(path)
    if normalized_path not in handle:
        return None
    return np.asarray(handle[normalized_path])


def _posterior_payload_from_analysis(analysis: object) -> dict[str, np.ndarray | None]:
    """Return posterior arrays from runtime or restored data."""
    fit_results = getattr(analysis, 'fit_results', None)
    posterior_samples = getattr(fit_results, 'posterior_samples', None)
    if posterior_samples is not None:
        return {
            'parameter_samples': np.asarray(posterior_samples.parameter_samples, dtype=float),
            'log_posterior': (
                None
                if posterior_samples.log_posterior is None
                else np.asarray(posterior_samples.log_posterior, dtype=float)
            ),
            'draw_index': (
                None
                if posterior_samples.draw_index is None
                else np.asarray(posterior_samples.draw_index)
            ),
        }

    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('posterior', {}))


def _distribution_cache_payload(analysis: object) -> dict[str, dict[str, np.ndarray]]:
    """Return persisted distribution caches keyed by parameter name."""
    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('distribution_caches', {}))


def _pair_cache_payload(analysis: object) -> dict[str, dict[str, np.ndarray]]:
    """Return persisted pair-cache arrays keyed by cache id."""
    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('pair_caches', {}))


def _predictive_payload(analysis: object) -> dict[str, dict[str, np.ndarray]]:
    """Return persisted predictive arrays keyed by experiment name."""
    fit_results = getattr(analysis, 'fit_results', None)
    posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
    if posterior_predictive:
        payload: dict[str, dict[str, np.ndarray]] = {}
        for runtime_key, summary in posterior_predictive.items():
            experiment_name = getattr(summary, 'experiment_name', None)
            if not isinstance(experiment_name, str) or not experiment_name.strip():
                experiment_name = runtime_key

            dataset_payload = payload.setdefault(experiment_name, {})
            dataset_payload['x'] = np.asarray(summary.x, dtype=float)
            dataset_payload['best_sample_prediction'] = np.asarray(
                summary.best_sample_prediction,
                dtype=float,
            )
            if summary.lower_95 is not None:
                dataset_payload['lower_95'] = np.asarray(summary.lower_95, dtype=float)
            if summary.upper_95 is not None:
                dataset_payload['upper_95'] = np.asarray(summary.upper_95, dtype=float)
            if summary.lower_68 is not None:
                dataset_payload['lower_68'] = np.asarray(summary.lower_68, dtype=float)
            if summary.upper_68 is not None:
                dataset_payload['upper_68'] = np.asarray(summary.upper_68, dtype=float)
            if summary.draws is not None:
                dataset_payload['draws'] = np.asarray(summary.draws, dtype=float)
        return payload

    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('predictive_datasets', {}))


def _validate_posterior_payload(
    analysis: object,
    payload: dict[str, np.ndarray | None],
) -> bool:
    """Return whether posterior arrays match stored metadata."""
    parameter_samples = payload.get('parameter_samples')
    if parameter_samples is None:
        if analysis.bayesian_result.has_posterior_samples.value:
            log.warning('Bayesian fit-state expects posterior samples, but none are available.')
        return False

    parameter_samples = np.asarray(parameter_samples, dtype=float)
    if parameter_samples.ndim != _POSTERIOR_SAMPLE_NDIM:
        log.warning(
            'Posterior parameter samples must have shape (n_draws, n_chains, n_parameters).'
        )
        return False

    n_draws, n_chains, n_parameters = parameter_samples.shape
    if not _posterior_manifest_counts_match(
        analysis,
        n_draws=n_draws,
        n_chains=n_chains,
        n_parameters=n_parameters,
    ):
        return False

    return _posterior_aux_shapes_match(
        payload,
        n_draws=n_draws,
        n_chains=n_chains,
    )


def _posterior_manifest_counts_match(
    analysis: object,
    *,
    n_draws: int,
    n_chains: int,
    n_parameters: int,
) -> bool:
    """Return whether manifest counts match the sample shape."""
    if analysis.bayesian_convergence.n_draws.value not in {0, n_draws}:
        log.warning('Posterior sample draw count does not match bayesian_convergence.n_draws.')
        return False
    if analysis.bayesian_convergence.n_chains.value not in {0, n_chains}:
        log.warning('Posterior sample chain count does not match bayesian_convergence.n_chains.')
        return False
    if analysis.bayesian_convergence.n_parameters.value not in {0, n_parameters}:
        log.warning(
            'Posterior sample parameter count does not match bayesian_convergence.n_parameters.'
        )
        return False

    return True


def _posterior_aux_shapes_match(
    payload: dict[str, np.ndarray | None],
    *,
    n_draws: int,
    n_chains: int,
) -> bool:
    """Return whether auxiliary arrays match the sample shape."""
    log_posterior = payload.get('log_posterior')
    if log_posterior is not None and np.asarray(log_posterior).shape != (n_draws, n_chains):
        log.warning(
            'Posterior log-posterior array does not match posterior sample draw and chain axes.'
        )
        return False

    draw_index = payload.get('draw_index')
    if draw_index is not None and np.asarray(draw_index).shape != (n_draws,):
        log.warning('Posterior draw-index array does not match posterior sample draw count.')
        return False

    return True


def _write_posterior_payload(handle: object, analysis: object) -> bool:
    """Write canonical posterior arrays when they are available."""
    payload = _posterior_payload_from_analysis(analysis)
    if not _validate_posterior_payload(analysis, payload):
        return False

    parameter_samples = np.asarray(payload['parameter_samples'], dtype=float)
    _create_dataset(handle, _POSTERIOR_PARAMETER_SAMPLES_PATH, parameter_samples)

    log_posterior = payload.get('log_posterior')
    if log_posterior is not None:
        _create_dataset(handle, _POSTERIOR_LOG_POSTERIOR_PATH, np.asarray(log_posterior))

    draw_index = payload.get('draw_index')
    if draw_index is not None:
        _create_dataset(handle, _POSTERIOR_DRAW_INDEX_PATH, np.asarray(draw_index))

    return True


def _write_distribution_caches(handle: object, analysis: object) -> bool:
    """Write cached posterior distribution arrays for manifest rows."""
    payload = _distribution_cache_payload(analysis)
    wrote_any = False
    for cache in analysis.bayesian_distribution_caches:
        cache_data = payload.get(cache.param_unique_name.value)
        if cache_data is None:
            continue

        x_values = np.asarray(cache_data.get('x'))
        density_values = np.asarray(cache_data.get('density'))
        n_grid = int(cache.n_grid.value)
        if x_values.shape != (n_grid,) or density_values.shape != (n_grid,):
            log.warning(
                'Skipping Bayesian distribution cache with shape mismatch for '
                f'{cache.param_unique_name.value!r}.'
            )
            continue

        _create_dataset(handle, cache.x_path.value, x_values)
        _create_dataset(handle, cache.density_path.value, density_values)
        wrote_any = True

    return wrote_any


def _write_pair_caches(handle: object, analysis: object) -> bool:
    """Write cached posterior pair-density arrays for manifest rows."""
    payload = _pair_cache_payload(analysis)
    wrote_any = False
    for cache in analysis.bayesian_pair_caches:
        cache_data = payload.get(cache.id.value)
        if cache_data is None:
            continue

        x_values = np.asarray(cache_data.get('x'))
        y_values = np.asarray(cache_data.get('y'))
        density_values = np.asarray(cache_data.get('density'))
        contour_levels = np.asarray(cache_data.get('contour_levels'))
        n_grid_x = int(cache.n_grid_x.value)
        n_grid_y = int(cache.n_grid_y.value)

        valid_density_shape = density_values.shape in {
            (n_grid_y, n_grid_x),
            (n_grid_x, n_grid_y),
        }
        if (
            x_values.shape != (n_grid_x,)
            or y_values.shape != (n_grid_y,)
            or not valid_density_shape
        ):
            log.warning(
                f'Skipping Bayesian pair cache with shape mismatch for {cache.id.value!r}.'
            )
            continue

        _create_dataset(handle, cache.x_path.value, x_values)
        _create_dataset(handle, cache.y_path.value, y_values)
        _create_dataset(handle, cache.density_path.value, density_values)
        _create_dataset(handle, cache.contour_level_path.value, contour_levels)
        wrote_any = True

    return wrote_any


def _write_predictive_datasets(handle: object, analysis: object) -> bool:
    """Write cached posterior predictive arrays for manifest rows."""
    payload = _predictive_payload(analysis)
    wrote_any = False
    for dataset in analysis.bayesian_predictive_datasets:
        dataset_data = payload.get(dataset.experiment_name.value)
        if dataset_data is None:
            continue

        x_values = np.asarray(dataset_data.get('x'))
        best_sample_prediction = np.asarray(dataset_data.get('best_sample_prediction'))
        n_x = int(dataset.n_x.value)
        if x_values.shape != (n_x,) or best_sample_prediction.shape != (n_x,):
            log.warning(
                'Skipping Bayesian predictive dataset with shape mismatch for '
                f'{dataset.experiment_name.value!r}.'
            )
            continue

        _create_dataset(handle, dataset.x_path.value, x_values)
        _create_dataset(
            handle,
            dataset.best_sample_prediction_path.value,
            best_sample_prediction,
        )

        for field_name, path_value in (
            ('lower_95', dataset.lower_95_path.value),
            ('upper_95', dataset.upper_95_path.value),
            ('lower_68', dataset.lower_68_path.value),
            ('upper_68', dataset.upper_68_path.value),
        ):
            values = dataset_data.get(field_name)
            if values is None or path_value is None:
                continue
            values_array = np.asarray(values)
            if values_array.shape != (n_x,):
                log.warning(
                    'Skipping Bayesian predictive band with shape mismatch for '
                    f'{dataset.experiment_name.value!r}:{field_name}.'
                )
                continue
            _create_dataset(handle, path_value, values_array)

        draws = dataset_data.get('draws')
        if draws is not None and dataset.draws_path.value is not None:
            draws_array = np.asarray(draws)
            if draws_array.ndim != _PREDICTIVE_DRAWS_NDIM or draws_array.shape[1] != n_x:
                log.warning(
                    'Skipping Bayesian predictive draws with shape mismatch for '
                    f'{dataset.experiment_name.value!r}.'
                )
            elif dataset.n_draws_cached.value not in {0, draws_array.shape[0]}:
                log.warning(
                    'Skipping Bayesian predictive draws whose draw count does not match '
                    'the manifest metadata.'
                )
            else:
                _create_dataset(handle, dataset.draws_path.value, draws_array)

        wrote_any = True

    return wrote_any


def write_analysis_results_sidecar(
    *,
    analysis: object,
    analysis_dir: Path,
) -> None:
    """
    Write persisted Bayesian arrays to ``analysis/results.h5``.

    Parameters
    ----------
    analysis : object
        Analysis instance that owns fit-state categories and runtime fit
        results.
    analysis_dir : Path
        The project ``analysis/`` directory.

    Raises
    ------
    Exception
        Propagated when sidecar writing fails after temporary-file
        cleanup.
    """
    sidecar_path = _sidecar_path(analysis=analysis, analysis_dir=analysis_dir)
    if not _should_use_sidecar(analysis):
        _delete_stale_sidecar(sidecar_path)
        return

    import h5py  # noqa: PLC0415

    analysis_dir.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        delete=False,
        dir=analysis_dir,
        prefix=f'{sidecar_path.stem}.',
        suffix=sidecar_path.suffix,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with h5py.File(temporary_path, 'w') as handle:
            wrote_any = _write_posterior_payload(handle, analysis)
            wrote_any = _write_distribution_caches(handle, analysis) or wrote_any
            wrote_any = _write_pair_caches(handle, analysis) or wrote_any
            wrote_any = _write_predictive_datasets(handle, analysis) or wrote_any
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    if not wrote_any:
        temporary_path.unlink()
        _delete_stale_sidecar(sidecar_path)
        return

    temporary_path.replace(sidecar_path)


def _read_posterior_payload(handle: object, analysis: object) -> dict[str, np.ndarray]:
    """Read canonical posterior arrays from a sidecar file."""
    parameter_samples = _read_dataset(handle, _POSTERIOR_PARAMETER_SAMPLES_PATH)
    if parameter_samples is None:
        return {}

    payload: dict[str, np.ndarray] = {
        'parameter_samples': np.asarray(parameter_samples, dtype=float),
    }
    log_posterior = _read_dataset(handle, _POSTERIOR_LOG_POSTERIOR_PATH)
    if log_posterior is not None:
        payload['log_posterior'] = np.asarray(log_posterior, dtype=float)
    draw_index = _read_dataset(handle, _POSTERIOR_DRAW_INDEX_PATH)
    if draw_index is not None:
        payload['draw_index'] = np.asarray(draw_index)

    if not _validate_posterior_payload(analysis, payload):
        return {}
    return payload


def _read_distribution_caches(
    handle: object, analysis: object
) -> dict[str, dict[str, np.ndarray]]:
    """Read cached posterior distribution arrays for manifest rows."""
    payload: dict[str, dict[str, np.ndarray]] = {}
    for cache in analysis.bayesian_distribution_caches:
        x_values = _read_dataset(handle, cache.x_path.value)
        density_values = _read_dataset(handle, cache.density_path.value)
        if x_values is None or density_values is None:
            continue
        if x_values.shape != (int(cache.n_grid.value),) or density_values.shape != (
            int(cache.n_grid.value),
        ):
            log.warning(
                'Skipping restored Bayesian distribution cache with shape mismatch for '
                f'{cache.param_unique_name.value!r}.'
            )
            continue
        payload[cache.param_unique_name.value] = {
            'x': np.asarray(x_values),
            'density': np.asarray(density_values),
        }
    return payload


def _read_pair_caches(handle: object, analysis: object) -> dict[str, dict[str, np.ndarray]]:
    """Read cached posterior pair-density arrays for manifest rows."""
    payload: dict[str, dict[str, np.ndarray]] = {}
    for cache in analysis.bayesian_pair_caches:
        x_values = _read_dataset(handle, cache.x_path.value)
        y_values = _read_dataset(handle, cache.y_path.value)
        density_values = _read_dataset(handle, cache.density_path.value)
        contour_levels = _read_dataset(handle, cache.contour_level_path.value)
        if any(value is None for value in (x_values, y_values, density_values, contour_levels)):
            continue

        n_grid_x = int(cache.n_grid_x.value)
        n_grid_y = int(cache.n_grid_y.value)
        valid_density_shape = density_values.shape in {
            (n_grid_y, n_grid_x),
            (n_grid_x, n_grid_y),
        }
        if (
            x_values.shape != (n_grid_x,)
            or y_values.shape != (n_grid_y,)
            or not valid_density_shape
        ):
            log.warning(
                'Skipping restored Bayesian pair cache with shape mismatch for '
                f'{cache.id.value!r}.'
            )
            continue

        payload[cache.id.value] = {
            'x': np.asarray(x_values),
            'y': np.asarray(y_values),
            'density': np.asarray(density_values),
            'contour_levels': np.asarray(contour_levels),
        }
    return payload


def _read_predictive_datasets(
    handle: object, analysis: object
) -> dict[str, dict[str, np.ndarray]]:
    """Read cached posterior predictive arrays for manifest rows."""
    payload: dict[str, dict[str, np.ndarray]] = {}
    for dataset in analysis.bayesian_predictive_datasets:
        x_values = _read_dataset(handle, dataset.x_path.value)
        best_sample_prediction = _read_dataset(handle, dataset.best_sample_prediction_path.value)
        if x_values is None or best_sample_prediction is None:
            continue

        n_x = int(dataset.n_x.value)
        if x_values.shape != (n_x,) or best_sample_prediction.shape != (n_x,):
            log.warning(
                'Skipping restored Bayesian predictive dataset with shape mismatch for '
                f'{dataset.experiment_name.value!r}.'
            )
            continue

        dataset_payload: dict[str, np.ndarray] = {
            'x': np.asarray(x_values),
            'best_sample_prediction': np.asarray(best_sample_prediction),
        }

        for field_name, path_value in (
            ('lower_95', dataset.lower_95_path.value),
            ('upper_95', dataset.upper_95_path.value),
            ('lower_68', dataset.lower_68_path.value),
            ('upper_68', dataset.upper_68_path.value),
            ('draws', dataset.draws_path.value),
        ):
            if path_value is None:
                continue
            values = _read_dataset(handle, path_value)
            if values is None:
                continue
            values_array = np.asarray(values)
            if field_name == 'draws':
                if values_array.ndim != _PREDICTIVE_DRAWS_NDIM or values_array.shape[1] != n_x:
                    log.warning(
                        'Skipping restored Bayesian predictive draws with shape mismatch for '
                        f'{dataset.experiment_name.value!r}.'
                    )
                    continue
            elif values_array.shape != (n_x,):
                log.warning(
                    'Skipping restored Bayesian predictive band with shape mismatch for '
                    f'{dataset.experiment_name.value!r}:{field_name}.'
                )
                continue
            dataset_payload[field_name] = values_array

        payload[dataset.experiment_name.value] = dataset_payload
    return payload


def read_analysis_results_sidecar(
    *,
    analysis: object,
    analysis_dir: Path,
) -> None:
    """
    Read persisted Bayesian arrays from ``analysis/results.h5``.

    Parameters
    ----------
    analysis : object
        Analysis instance that owns fit-state categories.
    analysis_dir : Path
        The project ``analysis/`` directory.
    """
    analysis._persisted_fit_state_sidecar = {}
    if not _should_use_sidecar(analysis):
        return

    sidecar_path = _sidecar_path(analysis=analysis, analysis_dir=analysis_dir)
    if not sidecar_path.is_file():
        log.warning(
            'Expected Bayesian results sidecar is missing: '
            f"'{sidecar_path}'. Restoring available CIF summaries only."
        )
        return

    import h5py  # noqa: PLC0415

    with h5py.File(sidecar_path, 'r') as handle:
        sidecar_data: dict[str, object] = {}

        posterior_payload = _read_posterior_payload(handle, analysis)
        if posterior_payload:
            sidecar_data['posterior'] = posterior_payload

        distribution_caches = _read_distribution_caches(handle, analysis)
        if distribution_caches:
            sidecar_data['distribution_caches'] = distribution_caches

        pair_caches = _read_pair_caches(handle, analysis)
        if pair_caches:
            sidecar_data['pair_caches'] = pair_caches

        predictive_datasets = _read_predictive_datasets(handle, analysis)
        if predictive_datasets:
            sidecar_data['predictive_datasets'] = predictive_datasets

    analysis._persisted_fit_state_sidecar = sidecar_data
