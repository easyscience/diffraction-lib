# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the Bayesian results sidecar helpers.

These exercise edge cases and error paths that the primary
``test_results_sidecar`` suite does not reach: stale-sidecar deletion,
overwrite warnings, payload validation failures, optional predictive
arrays, persisted-state fallbacks, duplicate group-id collisions, and
low-level HDF5 read/write helpers.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from easydiffraction.utils.logging import Logger


def _bayesian_fit_result() -> object:
    """Return a BayesianFitResult flagged as a Bayesian result kind."""
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

    fit_result = BayesianFitResult()
    fit_result._set_result_kind('bayesian')
    return fit_result


def _empty_analysis(*, has_fit_state: bool = True, bayesian: bool = True) -> object:
    """Return a minimal analysis namespace with no runtime fit results."""
    fit_result = _bayesian_fit_result()
    if not bayesian:
        fit_result._set_result_kind('deterministic')

    return SimpleNamespace(
        fit_result=fit_result,
        fit_results=None,
        _persisted_fit_state_sidecar={},
        _has_persisted_fit_state=(lambda: True) if has_fit_state else (lambda: False),
    )


# --- Stale-sidecar deletion and overwrite warnings ----------------------------


def test_delete_stale_sidecar_removes_existing_file(tmp_path):
    from easydiffraction.io.results_sidecar import _delete_stale_sidecar

    sidecar_path = Path(tmp_path) / 'results.h5'
    sidecar_path.write_bytes(b'stale')
    assert sidecar_path.is_file()

    _delete_stale_sidecar(sidecar_path)

    assert not sidecar_path.exists()


def test_delete_stale_sidecar_is_noop_when_missing(tmp_path):
    from easydiffraction.io.results_sidecar import _delete_stale_sidecar

    sidecar_path = Path(tmp_path) / 'absent.h5'

    _delete_stale_sidecar(sidecar_path)

    assert not sidecar_path.exists()


def test_warn_existing_sidecar_overwrite_skips_missing_and_empty(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    missing_path = Path(tmp_path) / 'missing.h5'
    mod._warn_existing_sidecar_overwrite(missing_path)

    empty_path = Path(tmp_path) / 'empty.h5'
    empty_path.write_bytes(b'')
    mod._warn_existing_sidecar_overwrite(empty_path)

    assert warnings == []


def test_warn_existing_sidecar_overwrite_warns_for_nonempty(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    sidecar_path = Path(tmp_path) / 'results.h5'
    sidecar_path.write_bytes(b'payload')

    mod._warn_existing_sidecar_overwrite(sidecar_path)

    assert len(warnings) == 1
    assert 'will be overwritten' in warnings[0]


def test_prepare_analysis_results_sidecar_for_new_fit_warns_and_removes(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    analysis_dir = Path(tmp_path)
    sidecar_path = analysis_dir / 'results.h5'
    sidecar_path.write_bytes(b'previous-fit')

    mod.prepare_analysis_results_sidecar_for_new_fit(analysis_dir=analysis_dir)

    assert not sidecar_path.exists()
    assert len(warnings) == 1
    assert 'will be overwritten' in warnings[0]


def test_prepare_analysis_results_sidecar_for_new_fit_noop_when_absent(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    mod.prepare_analysis_results_sidecar_for_new_fit(analysis_dir=Path(tmp_path))

    assert warnings == []


# --- _should_use_sidecar gating -----------------------------------------------


def test_should_use_sidecar_false_without_persisted_fit_state():
    from easydiffraction.io.results_sidecar import _should_use_sidecar

    analysis = _empty_analysis(has_fit_state=False)

    assert _should_use_sidecar(analysis) is False


def test_should_use_sidecar_false_when_callable_missing():
    from easydiffraction.io.results_sidecar import _should_use_sidecar

    analysis = SimpleNamespace(fit_result=_bayesian_fit_result())

    assert _should_use_sidecar(analysis) is False


# --- Low-level HDF5 dataset helpers -------------------------------------------


def test_create_dataset_replaces_existing_dataset(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _create_dataset
    from easydiffraction.io.results_sidecar import _read_dataset

    path = Path(tmp_path) / 'data.h5'
    with h5py.File(path, 'w') as handle:
        _create_dataset(handle, '/group/values', np.asarray([1.0, 2.0]))
        # Re-create the same dataset to hit the delete-then-create branch.
        _create_dataset(handle, '/group/values', np.asarray([9.0, 8.0, 7.0]))
        restored = _read_dataset(handle, '/group/values')

    assert np.allclose(restored, np.asarray([9.0, 8.0, 7.0]))


def test_create_dataset_at_root_without_group(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _create_dataset
    from easydiffraction.io.results_sidecar import _read_dataset

    path = Path(tmp_path) / 'root.h5'
    with h5py.File(path, 'w') as handle:
        _create_dataset(handle, 'rootset', np.asarray([3.0]))
        restored = _read_dataset(handle, 'rootset')

    assert np.allclose(restored, np.asarray([3.0]))


def test_read_dataset_returns_none_when_absent(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_dataset

    path = Path(tmp_path) / 'empty.h5'
    with h5py.File(path, 'w') as handle:
        assert _read_dataset(handle, '/does/not/exist') is None


def test_read_hdf5_attr_decodes_bytes_and_passes_through_str():
    from easydiffraction.io.results_sidecar import _read_hdf5_attr

    assert _read_hdf5_attr(b'two_theta') == 'two_theta'
    assert _read_hdf5_attr('plain') == 'plain'
    assert _read_hdf5_attr(42) == 42


def test_read_payload_group_returns_empty_when_group_absent(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_payload_group

    path = Path(tmp_path) / 'noop.h5'
    with h5py.File(path, 'w') as handle:
        assert _read_payload_group(handle, '/distribution_cache') == {}


# --- Posterior payload validation ---------------------------------------------


def test_validate_posterior_payload_false_without_parameter_samples():
    from easydiffraction.io.results_sidecar import _validate_posterior_payload

    assert _validate_posterior_payload({}) is False
    assert _validate_posterior_payload({'parameter_samples': None}) is False


def test_validate_posterior_payload_warns_on_wrong_ndim(monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    payload = {'parameter_samples': np.asarray([[1.0, 2.0], [3.0, 4.0]])}

    assert mod._validate_posterior_payload(payload) is False
    assert any('n_draws, n_chains, n_parameters' in warning for warning in warnings)


def test_validate_posterior_payload_warns_on_log_posterior_shape(monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    payload = {
        'parameter_samples': np.zeros((2, 1, 3)),
        'log_posterior': np.zeros((5, 5)),
    }

    assert mod._validate_posterior_payload(payload) is False
    assert any('log-posterior array does not match' in warning for warning in warnings)


def test_validate_posterior_payload_warns_on_draw_index_shape(monkeypatch):
    from easydiffraction.io import results_sidecar as mod

    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    payload = {
        'parameter_samples': np.zeros((2, 1, 3)),
        'draw_index': np.zeros((7,)),
    }

    assert mod._validate_posterior_payload(payload) is False
    assert any('draw-index array does not match' in warning for warning in warnings)


def test_validate_posterior_payload_accepts_matching_aux_arrays():
    from easydiffraction.io.results_sidecar import _validate_posterior_payload

    payload = {
        'parameter_samples': np.zeros((2, 1, 3)),
        'log_posterior': np.zeros((2, 1)),
        'draw_index': np.zeros((2,)),
    }

    assert _validate_posterior_payload(payload) is True


# --- Payload extraction from persisted state (no runtime fit_results) ---------


def test_posterior_payload_falls_back_to_persisted_sidecar():
    from easydiffraction.io.results_sidecar import _posterior_payload_from_analysis

    stored = {'parameter_samples': np.zeros((2, 1, 1))}
    analysis = SimpleNamespace(
        fit_results=None,
        _persisted_fit_state_sidecar={'posterior': stored},
    )

    payload = _posterior_payload_from_analysis(analysis)

    assert payload is not stored  # defensive copy
    assert np.allclose(payload['parameter_samples'], stored['parameter_samples'])


def test_distribution_and_pair_payloads_fall_back_to_persisted_sidecar():
    from easydiffraction.io.results_sidecar import _distribution_cache_payload
    from easydiffraction.io.results_sidecar import _pair_cache_payload

    analysis = SimpleNamespace(
        fit_results=SimpleNamespace(
            posterior_distribution_caches={},
            posterior_pair_caches={},
        ),
        _persisted_fit_state_sidecar={
            'distribution_caches': {'a': {'x': np.zeros(2)}},
            'pair_caches': {'a__b': {'density': np.zeros((2, 2))}},
        },
    )

    assert 'a' in _distribution_cache_payload(analysis)
    assert 'a__b' in _pair_cache_payload(analysis)


def test_predictive_payload_falls_back_to_persisted_sidecar():
    from easydiffraction.io.results_sidecar import _predictive_payload

    analysis = SimpleNamespace(
        fit_results=SimpleNamespace(posterior_predictive={}),
        _persisted_fit_state_sidecar={
            'predictive_datasets': {'hrpt': {'x': np.zeros(2)}},
        },
    )

    assert 'hrpt' in _predictive_payload(analysis)


def test_predictive_payload_collects_all_optional_arrays_and_fallback_name():
    from easydiffraction.io.results_sidecar import _predictive_payload

    summary = SimpleNamespace(
        experiment_name='   ',  # blank -> fall back to runtime key
        x_axis_name='two_theta',
        x=np.asarray([1.0, 2.0]),
        best_sample_prediction=np.asarray([3.0, 4.0]),
        lower_95=np.asarray([2.5, 3.5]),
        upper_95=np.asarray([3.5, 4.5]),
        lower_68=np.asarray([2.8, 3.8]),
        upper_68=np.asarray([3.2, 4.2]),
        draws=np.asarray([[1.0, 2.0], [3.0, 4.0]]),
    )
    analysis = SimpleNamespace(
        fit_results=SimpleNamespace(posterior_predictive={'runtime_key': summary}),
        _persisted_fit_state_sidecar={},
    )

    payload = _predictive_payload(analysis)

    assert 'runtime_key' in payload  # blank experiment_name fell back to key
    dataset = payload['runtime_key']
    assert dataset['x_axis_name'] == 'two_theta'
    for key in ('lower_95', 'upper_95', 'lower_68', 'upper_68', 'draws'):
        assert key in dataset


# --- Duplicate group ids and None-value skipping in _write_payload_group ------


def test_write_payload_group_disambiguates_colliding_ids(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_payload_group
    from easydiffraction.io.results_sidecar import _write_payload_group

    # Two distinct ids that sanitise to the same group name 'a_b'.
    payload = {
        'a/b': {'x': np.asarray([1.0])},
        'a_b': {'x': np.asarray([2.0])},
    }
    path = Path(tmp_path) / 'collide.h5'
    with h5py.File(path, 'w') as handle:
        wrote_any = _write_payload_group(handle, '/distribution_cache', payload)
        assert wrote_any is True
        restored = _read_payload_group(handle, '/distribution_cache')

    # Both ids round-trip via the stored 'id' attribute despite the name clash.
    assert set(restored) == {'a/b', 'a_b'}


def test_write_payload_group_skips_none_values(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_payload_group
    from easydiffraction.io.results_sidecar import _write_payload_group

    payload = {'item': {'present': np.asarray([1.0]), 'absent': None}}
    path = Path(tmp_path) / 'skip.h5'
    with h5py.File(path, 'w') as handle:
        _write_payload_group(handle, '/pair_cache', payload)
        restored = _read_payload_group(handle, '/pair_cache')

    assert 'present' in restored['item']
    assert 'absent' not in restored['item']


def test_write_payload_group_empty_id_becomes_item(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_payload_group
    from easydiffraction.io.results_sidecar import _write_payload_group

    payload = {'/': {'x': np.asarray([1.0])}}
    path = Path(tmp_path) / 'emptyid.h5'
    with h5py.File(path, 'w') as handle:
        _write_payload_group(handle, '/distribution_cache', payload)
        assert 'item' in handle['distribution_cache']
        restored = _read_payload_group(handle, '/distribution_cache')

    assert '/' in restored


# --- write side: nothing to write deletes the sidecar -------------------------


def test_write_analysis_results_sidecar_removes_file_when_nothing_written(tmp_path):
    from easydiffraction.io import results_sidecar as mod

    analysis_dir = Path(tmp_path) / 'analysis'
    analysis = SimpleNamespace(
        fit_result=_bayesian_fit_result(),
        fit_results=SimpleNamespace(
            posterior_samples=None,
            posterior_distribution_caches={},
            posterior_pair_caches={},
            posterior_predictive={},
        ),
        _persisted_fit_state_sidecar={},
        _has_persisted_fit_state=lambda: True,
    )

    mod.write_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    assert not (analysis_dir / 'results.h5').exists()


def test_write_analysis_results_sidecar_deletes_stale_when_not_bayesian(tmp_path):
    from easydiffraction.io import results_sidecar as mod

    analysis_dir = Path(tmp_path)
    sidecar_path = analysis_dir / 'results.h5'
    sidecar_path.write_bytes(b'stale')

    analysis = _empty_analysis(bayesian=False)
    mod.write_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    assert not sidecar_path.exists()


# --- read side: posterior reader edge cases -----------------------------------


def test_read_posterior_payload_returns_empty_without_parameter_samples(tmp_path):
    import h5py

    from easydiffraction.io.results_sidecar import _read_posterior_payload

    path = Path(tmp_path) / 'noposterior.h5'
    with h5py.File(path, 'w') as handle:
        assert _read_posterior_payload(handle) == {}


def test_read_posterior_payload_returns_empty_on_invalid_payload(tmp_path, monkeypatch):
    import h5py

    from easydiffraction.io import results_sidecar as mod

    monkeypatch.setattr(mod.log, 'warning', lambda *args, **kwargs: None)

    path = Path(tmp_path) / 'invalid.h5'
    with h5py.File(path, 'w') as handle:
        # 2D parameter_samples fails the ndim check inside _validate.
        mod._create_dataset(
            handle,
            mod._POSTERIOR_PARAMETER_SAMPLES_PATH,
            np.zeros((2, 2)),
        )
        assert mod._read_posterior_payload(handle) == {}


def test_read_posterior_payload_reads_aux_arrays(tmp_path):
    import h5py

    from easydiffraction.io import results_sidecar as mod

    path = Path(tmp_path) / 'aux.h5'
    with h5py.File(path, 'w') as handle:
        mod._create_dataset(handle, mod._POSTERIOR_PARAMETER_SAMPLES_PATH, np.zeros((2, 1, 3)))
        mod._create_dataset(handle, mod._POSTERIOR_LOG_POSTERIOR_PATH, np.zeros((2, 1)))
        mod._create_dataset(handle, mod._POSTERIOR_DRAW_INDEX_PATH, np.asarray([0, 1]))
        payload = mod._read_posterior_payload(handle)

    assert set(payload) == {'parameter_samples', 'log_posterior', 'draw_index'}


# --- read_analysis_results_sidecar early returns ------------------------------


def test_read_analysis_results_sidecar_returns_early_when_not_bayesian(tmp_path):
    from easydiffraction.io import results_sidecar as mod

    analysis = _empty_analysis(bayesian=False)
    analysis._persisted_fit_state_sidecar = {'stale': 'data'}

    mod.read_analysis_results_sidecar(analysis=analysis, analysis_dir=Path(tmp_path))

    # The reader resets the persisted sidecar then returns before any read.
    assert analysis._persisted_fit_state_sidecar == {}


def test_read_analysis_results_sidecar_populates_all_groups(tmp_path):
    import h5py

    from easydiffraction.io import results_sidecar as mod

    analysis_dir = Path(tmp_path)
    path = analysis_dir / 'results.h5'
    with h5py.File(path, 'w') as handle:
        mod._create_dataset(handle, mod._POSTERIOR_PARAMETER_SAMPLES_PATH, np.zeros((2, 1, 1)))
        mod._write_payload_group(
            handle,
            mod._DISTRIBUTION_CACHE_GROUP,
            {'alpha': {'x': np.asarray([0.0, 1.0])}},
        )
        mod._write_payload_group(
            handle,
            mod._PAIR_CACHE_GROUP,
            {'a__b': {'density': np.zeros((2, 2))}},
        )
        mod._write_payload_group(
            handle,
            mod._PREDICTIVE_GROUP,
            {'hrpt': {'x': np.asarray([1.0, 2.0])}},
        )

    analysis = _empty_analysis()
    mod.read_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    sidecar = analysis._persisted_fit_state_sidecar
    assert set(sidecar) == {
        'posterior',
        'distribution_caches',
        'pair_caches',
        'predictive_datasets',
    }


def test_read_analysis_results_sidecar_skips_empty_groups(tmp_path):
    import h5py

    from easydiffraction.io import results_sidecar as mod

    analysis_dir = Path(tmp_path)
    path = analysis_dir / 'results.h5'
    # File exists but contains no canonical EasyDiffraction groups.
    with h5py.File(path, 'w') as handle:
        handle.create_group('unrelated')

    analysis = _empty_analysis()
    mod.read_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    assert analysis._persisted_fit_state_sidecar == {}


def test_read_analysis_results_sidecar_warns_and_resets_when_file_missing(
    tmp_path,
    monkeypatch,
):
    """A Bayesian analysis with no sidecar warns and clears the payload."""
    from easydiffraction.io import results_sidecar as mod

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    warnings: list[str] = []
    monkeypatch.setattr(mod.log, 'warning', warnings.append)

    analysis = _empty_analysis()
    analysis._persisted_fit_state_sidecar = {'stale': 'data'}
    mod.read_analysis_results_sidecar(analysis=analysis, analysis_dir=Path(tmp_path))

    assert analysis._persisted_fit_state_sidecar == {}
    assert any('Bayesian results sidecar is missing' in warning for warning in warnings)
