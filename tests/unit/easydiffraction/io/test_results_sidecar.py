# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for persisted Bayesian results sidecars."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np


def _analysis_with_sidecar_payload(
    *,
    include_posterior: bool = True,
    include_distribution: bool = True,
    include_pair: bool = True,
    include_predictive: bool = True,
) -> object:
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

    fit_result = BayesianFitResult()
    fit_result._set_result_kind('bayesian')

    posterior_samples = None
    if include_posterior:
        posterior_samples = SimpleNamespace(
            parameter_samples=np.asarray([[[1.0]], [[1.2]]], dtype=float),
            log_posterior=np.asarray([[-4.0], [-3.5]], dtype=float),
            draw_index=np.asarray([0, 1]),
        )

    distribution_caches = {}
    if include_distribution:
        distribution_caches = {
            'alpha': {
                'x': np.asarray([0.5, 1.5], dtype=float),
                'density': np.asarray([0.25, 0.75], dtype=float),
            }
        }

    pair_caches = {}
    if include_pair:
        pair_caches = {
            'alpha__beta': {
                'x': np.asarray([0.5, 1.5], dtype=float),
                'y': np.asarray([2.5, 3.5], dtype=float),
                'density': np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=float),
            }
        }

    posterior_predictive = {}
    if include_predictive:
        posterior_predictive = {
            'hrpt': SimpleNamespace(
                experiment_name='hrpt',
                x_axis_name='two_theta',
                x=np.asarray([1.0, 2.0]),
                best_sample_prediction=np.asarray([3.0, 4.0]),
                lower_95=np.asarray([2.5, 3.5]),
                upper_95=np.asarray([3.5, 4.5]),
                lower_68=None,
                upper_68=None,
                draws=None,
            )
        }

    return SimpleNamespace(
        fit_result=fit_result,
        fit_results=SimpleNamespace(
            posterior_samples=posterior_samples,
            posterior_distribution_caches=distribution_caches,
            posterior_pair_caches=pair_caches,
            posterior_predictive=posterior_predictive,
        ),
        _persisted_fit_state_sidecar={},
        _has_persisted_fit_state=lambda: True,
    )


def test_write_and_read_analysis_results_sidecar_round_trip_predictive(tmp_path):
    from easydiffraction.io.results_sidecar import read_analysis_results_sidecar
    from easydiffraction.io.results_sidecar import write_analysis_results_sidecar

    analysis_dir = Path(tmp_path)
    analysis = _analysis_with_sidecar_payload()

    write_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    sidecar_path = analysis_dir / 'mcmc.h5'
    assert sidecar_path.is_file()

    import h5py

    with h5py.File(sidecar_path, 'r') as handle:
        assert 'posterior' in handle
        assert 'distribution_cache' in handle
        assert 'pair_cache' in handle
        assert 'predictive' in handle

    restored = _analysis_with_sidecar_payload()
    restored.fit_results = None
    read_analysis_results_sidecar(analysis=restored, analysis_dir=analysis_dir)

    assert 'posterior' in restored._persisted_fit_state_sidecar
    posterior = restored._persisted_fit_state_sidecar['posterior']
    assert np.allclose(posterior['parameter_samples'], np.asarray([[[1.0]], [[1.2]]]))
    assert 'distribution_caches' in restored._persisted_fit_state_sidecar
    distribution = restored._persisted_fit_state_sidecar['distribution_caches']['alpha']
    assert np.allclose(distribution['x'], np.asarray([0.5, 1.5]))
    assert 'pair_caches' in restored._persisted_fit_state_sidecar
    pair = restored._persisted_fit_state_sidecar['pair_caches']['alpha__beta']
    assert np.allclose(pair['density'], np.asarray([[0.1, 0.2], [0.3, 0.4]]))
    assert 'predictive_datasets' in restored._persisted_fit_state_sidecar
    dataset = restored._persisted_fit_state_sidecar['predictive_datasets']['hrpt']
    assert np.allclose(dataset['x'], np.asarray([1.0, 2.0]))
    assert np.allclose(dataset['best_sample_prediction'], np.asarray([3.0, 4.0]))


def test_read_analysis_results_sidecar_warns_when_expected_file_is_missing(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis = _analysis_with_sidecar_payload()
    warnings: list[str] = []
    monkeypatch.setattr(results_sidecar_mod.log, 'warning', warnings.append)

    results_sidecar_mod.read_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=Path(tmp_path),
    )

    assert analysis._persisted_fit_state_sidecar == {}
    assert any('Expected Bayesian results sidecar is missing' in warning for warning in warnings)


def test_write_analysis_results_sidecar_truncates_stale_payloads(tmp_path):
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis_dir = Path(tmp_path) / 'analysis'
    analysis = _analysis_with_sidecar_payload()
    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    analysis = _analysis_with_sidecar_payload(
        include_posterior=False,
        include_distribution=False,
        include_pair=False,
    )
    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    import h5py

    with h5py.File(analysis_dir / 'mcmc.h5', 'r') as handle:
        assert 'posterior' not in handle
        assert 'alpha' not in handle['distribution_cache']
        assert 'alpha__beta' not in handle['pair_cache']
        assert 'hrpt' in handle['predictive']


def test_write_analysis_results_sidecar_preserves_emcee_chain_group(tmp_path):
    from easydiffraction.analysis.minimizers.emcee import EMCEE_CHAIN_GROUP
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis_dir = Path(tmp_path) / 'analysis'
    analysis = _analysis_with_sidecar_payload()
    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    import h5py

    with h5py.File(analysis_dir / 'mcmc.h5', 'a') as handle:
        chain = handle.require_group(EMCEE_CHAIN_GROUP)
        chain.attrs['iteration'] = 7

    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    with h5py.File(analysis_dir / 'mcmc.h5', 'r') as handle:
        assert handle[EMCEE_CHAIN_GROUP].attrs['iteration'] == 7


def test_write_analysis_results_sidecar_preserves_dream_state_group(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis_dir = Path(tmp_path) / 'analysis'
    analysis = _analysis_with_sidecar_payload()
    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    import h5py

    with h5py.File(analysis_dir / 'mcmc.h5', 'a') as handle:
        state = handle.require_group(DREAM_STATE_GROUP)
        state.attrs['generations'] = 11

    results_sidecar_mod.write_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=analysis_dir,
    )

    with h5py.File(analysis_dir / 'mcmc.h5', 'r') as handle:
        assert handle[DREAM_STATE_GROUP].attrs['generations'] == 11


def test_prepare_for_new_fit_clears_all_raw_state_groups(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP
    from easydiffraction.analysis.minimizers.emcee import EMCEE_CHAIN_GROUP
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis_dir = Path(tmp_path) / 'analysis'
    analysis_dir.mkdir(parents=True)
    sidecar_path = analysis_dir / 'mcmc.h5'

    import h5py

    # A fresh fit must wipe every engine's raw sampler-state group, not
    # just the active one, so a stale chain can never be resumed.
    with h5py.File(sidecar_path, 'w') as handle:
        handle.create_group(EMCEE_CHAIN_GROUP)
        handle.create_group(DREAM_STATE_GROUP)
        handle.create_group('posterior')

    results_sidecar_mod.prepare_analysis_results_sidecar_for_new_fit(
        analysis_dir=analysis_dir,
    )

    assert not sidecar_path.is_file()


def test_carry_over_raw_sampler_state_copies_engine_groups(tmp_path):
    import h5py

    from easydiffraction.io import results_sidecar as results_sidecar_mod

    source_dir = Path(tmp_path) / 'src' / 'analysis'
    source_dir.mkdir(parents=True)
    with h5py.File(source_dir / 'mcmc.h5', 'w') as handle:
        chain = handle.create_group('emcee_chain')
        chain.attrs['iteration'] = 5
        state = handle.create_group('dream_state')
        state.create_dataset('param_names', data=[b'a', b'b'])
        handle.create_group('posterior')  # canonical: must NOT be copied

    dest_dir = Path(tmp_path) / 'dst' / 'analysis'

    results_sidecar_mod.carry_over_raw_sampler_state(
        source_analysis_dir=source_dir,
        destination_analysis_dir=dest_dir,
    )

    with h5py.File(dest_dir / 'mcmc.h5', 'r') as handle:
        assert handle['emcee_chain'].attrs['iteration'] == 5
        assert 'dream_state' in handle
        assert list(handle['dream_state']['param_names'][()]) == [b'a', b'b']
        # Canonical groups are rebuilt from memory, never carried over.
        assert 'posterior' not in handle


def test_carry_over_raw_sampler_state_is_noop_without_source(tmp_path):
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    dest_dir = Path(tmp_path) / 'dst' / 'analysis'

    results_sidecar_mod.carry_over_raw_sampler_state(
        source_analysis_dir=Path(tmp_path) / 'missing' / 'analysis',
        destination_analysis_dir=dest_dir,
    )

    assert not (dest_dir / 'mcmc.h5').exists()


def test_carry_over_raw_sampler_state_is_noop_without_raw_groups(tmp_path):
    import h5py

    from easydiffraction.io import results_sidecar as results_sidecar_mod

    source_dir = Path(tmp_path) / 'src' / 'analysis'
    source_dir.mkdir(parents=True)
    with h5py.File(source_dir / 'mcmc.h5', 'w') as handle:
        handle.create_group('posterior')

    dest_dir = Path(tmp_path) / 'dst' / 'analysis'

    results_sidecar_mod.carry_over_raw_sampler_state(
        source_analysis_dir=source_dir,
        destination_analysis_dir=dest_dir,
    )

    assert not (dest_dir / 'mcmc.h5').exists()


def test_should_use_sidecar_compares_to_fit_result_kind_enum():
    """`_should_use_sidecar` must read from `FitResultKindEnum`, not a literal."""
    from easydiffraction.analysis.enums import FitResultKindEnum
    from easydiffraction.io.results_sidecar import _should_use_sidecar

    deterministic_analysis = _analysis_with_sidecar_payload()
    deterministic_analysis.fit_result._set_result_kind(FitResultKindEnum.DETERMINISTIC.value)

    bayesian_analysis = _analysis_with_sidecar_payload()
    bayesian_analysis.fit_result._set_result_kind(FitResultKindEnum.BAYESIAN.value)

    assert _should_use_sidecar(deterministic_analysis) is False
    assert _should_use_sidecar(bayesian_analysis) is True
