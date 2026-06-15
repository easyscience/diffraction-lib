# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit sidecar read/write helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from pathlib import Path

SidecarPayload = dict[str, dict[str, object]]
SIDECAR_FILE_NAME = 'mcmc.h5'
_POSTERIOR_PARAMETER_SAMPLES_PATH = '/posterior/parameter_samples'
_POSTERIOR_LOG_POSTERIOR_PATH = '/posterior/log_posterior'
_POSTERIOR_DRAW_INDEX_PATH = '/posterior/draw_index'
_DISTRIBUTION_CACHE_GROUP = '/distribution_cache'
_PAIR_CACHE_GROUP = '/pair_cache'
_PREDICTIVE_GROUP = '/predictive'
_CANONICAL_GROUPS = (
    'posterior',
    'distribution_cache',
    'pair_cache',
    'predictive',
)
# Raw, resumable sampler-state groups written per engine (emcee's live
# HDF backend, DREAM's MCMCDraw dump). They are not rebuilt from memory
# on save, so relocating a project must copy them across explicitly.
_RAW_SAMPLER_STATE_GROUPS = (
    'emcee_chain',
    'dream_state',
)
_POSTERIOR_SAMPLE_NDIM = 3


def _normalized_hdf5_path(path: str) -> str:
    """Return an HDF5 path without a leading slash."""
    return path.lstrip('/')


def _sidecar_path(*, analysis_dir: Path) -> Path:
    """Return the results sidecar path inside the analysis directory."""
    return analysis_dir.resolve() / SIDECAR_FILE_NAME


def _should_use_sidecar(analysis: object) -> bool:
    """
    Return whether the analysis currently expects a Bayesian sidecar.
    """
    has_fit_state = getattr(analysis, '_has_persisted_fit_state', None)
    if not callable(has_fit_state) or not has_fit_state():
        return False

    return analysis.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value


def _delete_stale_sidecar(sidecar_path: Path) -> None:
    """
    Delete an existing sidecar when no persisted arrays should remain.
    """
    if sidecar_path.is_file():
        sidecar_path.unlink()


def _warn_existing_sidecar_overwrite(sidecar_path: Path) -> None:
    """Warn when a new fit will overwrite existing sidecar arrays."""
    if not sidecar_path.is_file() or sidecar_path.stat().st_size == 0:
        return

    log.warning(
        f"Existing fit results sidecar '{sidecar_path}' will be overwritten "
        'when the new fit is saved.'
    )


def carry_over_raw_sampler_state(
    *,
    source_analysis_dir: Path,
    destination_analysis_dir: Path,
) -> None:
    """
    Copy raw sampler-state groups into a relocated project's sidecar.

    A project ``save_as`` rebuilds the derived sidecar arrays from
    memory but cannot reconstruct the raw, resumable sampler state
    (``emcee_chain`` / ``dream_state``). This copies those groups from
    the source sidecar into the destination so a resume after load +
    ``save_as`` still finds the chain to extend. No-op when the source
    sidecar or its raw-state groups are absent.

    Parameters
    ----------
    source_analysis_dir : Path
        The ``analysis/`` directory of the previously saved project.
    destination_analysis_dir : Path
        The ``analysis/`` directory of the relocated project.
    """
    source_path = _sidecar_path(analysis_dir=source_analysis_dir)
    if not source_path.is_file():
        return

    import h5py  # noqa: PLC0415

    with h5py.File(source_path, 'r') as source_handle:
        present_groups = [
            group_name for group_name in _RAW_SAMPLER_STATE_GROUPS if group_name in source_handle
        ]
        if not present_groups:
            return

        destination_analysis_dir.mkdir(parents=True, exist_ok=True)
        destination_path = _sidecar_path(analysis_dir=destination_analysis_dir)
        with h5py.File(destination_path, 'a') as destination_handle:
            for group_name in present_groups:
                _delete_group_if_present(destination_handle, group_name)
                source_handle.copy(group_name, destination_handle, name=group_name)


def prepare_analysis_results_sidecar_for_new_fit(*, analysis_dir: Path) -> None:
    """Warn and remove the results sidecar before a fresh fit starts."""
    sidecar_path = _sidecar_path(analysis_dir=analysis_dir)
    _warn_existing_sidecar_overwrite(sidecar_path)
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


def _delete_group_if_present(handle: object, group_name: str) -> None:
    """
    Delete one top-level group from an open HDF5 file when present.
    """
    if group_name in handle:
        del handle[group_name]


def _delete_canonical_groups(handle: object) -> None:
    """
    Delete EasyDiffraction-owned top-level groups before append writes.
    """
    for group_name in _CANONICAL_GROUPS:
        _delete_group_if_present(handle, group_name)


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


def _distribution_cache_payload(analysis: object) -> SidecarPayload:
    """Return distribution caches keyed by parameter name."""
    fit_results = getattr(analysis, 'fit_results', None)
    distribution_caches = getattr(fit_results, 'posterior_distribution_caches', None)
    if distribution_caches:
        return dict(distribution_caches)

    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('distribution_caches', {}))


def _pair_cache_payload(analysis: object) -> SidecarPayload:
    """Return pair-cache arrays keyed by cache id."""
    fit_results = getattr(analysis, 'fit_results', None)
    pair_caches = getattr(fit_results, 'posterior_pair_caches', None)
    if pair_caches:
        return dict(pair_caches)

    sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
    return dict(sidecar_data.get('pair_caches', {}))


def _predictive_payload(analysis: object) -> SidecarPayload:
    """Return persisted predictive arrays keyed by experiment name."""
    fit_results = getattr(analysis, 'fit_results', None)
    posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
    if posterior_predictive:
        payload: SidecarPayload = {}
        for runtime_key, summary in posterior_predictive.items():
            experiment_name = getattr(summary, 'experiment_name', None)
            if not isinstance(experiment_name, str) or not experiment_name.strip():
                experiment_name = runtime_key

            dataset_payload = payload.setdefault(experiment_name, {})
            dataset_payload['x_axis_name'] = str(summary.x_axis_name)
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
    payload: dict[str, np.ndarray | None],
) -> bool:
    """Return whether posterior arrays match stored metadata."""
    parameter_samples = payload.get('parameter_samples')
    if parameter_samples is None:
        return False

    parameter_samples = np.asarray(parameter_samples, dtype=float)
    if parameter_samples.ndim != _POSTERIOR_SAMPLE_NDIM:
        log.warning(
            'Posterior parameter samples must have shape (n_draws, n_chains, n_parameters).'
        )
        return False

    n_draws, n_chains, _ = parameter_samples.shape
    return _posterior_aux_shapes_match(
        payload,
        n_draws=n_draws,
        n_chains=n_chains,
    )


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
    if not _validate_posterior_payload(payload):
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


def _write_payload_group(
    handle: object,
    group_name: str,
    payload: SidecarPayload,
) -> bool:
    """Write a mapping payload under one HDF5 group."""
    wrote_any = False
    root = handle.require_group(_normalized_hdf5_path(group_name))
    for item_id, item_payload in payload.items():
        base_group_name = str(item_id).strip('/').replace('/', '_') or 'item'
        item_group_name = base_group_name
        suffix = 2
        while item_group_name in root:
            item_group_name = f'{base_group_name}_{suffix}'
            suffix += 1
        item_group = root.create_group(item_group_name)
        item_group.attrs['id'] = str(item_id)
        for dataset_name, values in item_payload.items():
            if values is None:
                continue
            if isinstance(values, str):
                item_group.attrs[dataset_name] = values
                wrote_any = True
                continue
            item_group.create_dataset(dataset_name, data=np.asarray(values))
            wrote_any = True
    return wrote_any


def _write_distribution_caches(handle: object, analysis: object) -> bool:
    """Write cached posterior distribution arrays."""
    payload = _distribution_cache_payload(analysis)
    return _write_payload_group(handle, _DISTRIBUTION_CACHE_GROUP, payload)


def _write_pair_caches(handle: object, analysis: object) -> bool:
    """Write cached posterior pair-density arrays."""
    payload = _pair_cache_payload(analysis)
    return _write_payload_group(handle, _PAIR_CACHE_GROUP, payload)


def _write_predictive_datasets(handle: object, analysis: object) -> bool:
    """Write cached posterior predictive arrays."""
    payload = _predictive_payload(analysis)
    return _write_payload_group(handle, _PREDICTIVE_GROUP, payload)


def write_analysis_results_sidecar(
    *,
    analysis: object,
    analysis_dir: Path,
) -> None:
    """
    Write persisted Bayesian arrays to ``analysis/mcmc.h5``.

    Parameters
    ----------
    analysis : object
        Analysis instance that owns fit-state categories and runtime fit
        results.
    analysis_dir : Path
        The project ``analysis/`` directory.
    """
    sidecar_path = _sidecar_path(analysis_dir=analysis_dir)
    if not _should_use_sidecar(analysis):
        _delete_stale_sidecar(sidecar_path)
        return

    import h5py  # noqa: PLC0415

    analysis_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(sidecar_path, 'a') as handle:
        _delete_canonical_groups(handle)
        wrote_any = _write_posterior_payload(handle, analysis)
        wrote_any = _write_distribution_caches(handle, analysis) or wrote_any
        wrote_any = _write_pair_caches(handle, analysis) or wrote_any
        wrote_any = _write_predictive_datasets(handle, analysis) or wrote_any

    if not wrote_any:
        _delete_stale_sidecar(sidecar_path)


def _read_posterior_payload(handle: object) -> dict[str, np.ndarray]:
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

    if not _validate_posterior_payload(payload):
        return {}
    return payload


def _read_hdf5_attr(value: object) -> object:
    """Return one HDF5 attribute as a plain Python value."""
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def _read_payload_group(handle: object, group_name: str) -> SidecarPayload:
    """Read a mapping payload from one HDF5 group."""
    payload: SidecarPayload = {}
    normalized_group = _normalized_hdf5_path(group_name)
    if normalized_group not in handle:
        return payload

    root = handle[normalized_group]
    for item_name, item_group in root.items():
        item_id = str(item_group.attrs.get('id', item_name))
        item_payload: dict[str, object] = {
            dataset_name: np.asarray(dataset) for dataset_name, dataset in item_group.items()
        }
        for attr_name, attr_value in item_group.attrs.items():
            if attr_name == 'id':
                continue
            item_payload[attr_name] = _read_hdf5_attr(attr_value)
        payload[item_id] = item_payload
    return payload


def _read_distribution_caches(handle: object) -> SidecarPayload:
    """Read cached posterior distribution arrays."""
    return _read_payload_group(handle, _DISTRIBUTION_CACHE_GROUP)


def _read_pair_caches(handle: object) -> SidecarPayload:
    """Read cached posterior pair-density arrays."""
    return _read_payload_group(handle, _PAIR_CACHE_GROUP)


def _read_predictive_datasets(handle: object) -> SidecarPayload:
    """Read cached posterior predictive arrays."""
    return _read_payload_group(handle, _PREDICTIVE_GROUP)


def read_analysis_results_sidecar(
    *,
    analysis: object,
    analysis_dir: Path,
) -> None:
    """
    Read persisted Bayesian arrays from ``analysis/mcmc.h5``.

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

    sidecar_path = _sidecar_path(analysis_dir=analysis_dir)
    if not sidecar_path.is_file():
        log.warning(
            'Expected Bayesian results sidecar is missing: '
            f"'{sidecar_path}'. Restoring available CIF summaries only."
        )
        return

    import h5py  # noqa: PLC0415

    with h5py.File(sidecar_path, 'r') as handle:
        sidecar_data: dict[str, object] = {}

        posterior_payload = _read_posterior_payload(handle)
        if posterior_payload:
            sidecar_data['posterior'] = posterior_payload

        distribution_caches = _read_distribution_caches(handle)
        if distribution_caches:
            sidecar_data['distribution_caches'] = distribution_caches

        pair_caches = _read_pair_caches(handle)
        if pair_caches:
            sidecar_data['pair_caches'] = pair_caches

        predictive_datasets = _read_predictive_datasets(handle)
        if predictive_datasets:
            sidecar_data['predictive_datasets'] = predictive_datasets

    analysis._persisted_fit_state_sidecar = sidecar_data
