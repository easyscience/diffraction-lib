# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

# Deterministic import order to avoid a circular import in isolation:
# Pre-import the experiment enums so that when DatastoreFactory pulls in
# PdDatastore -> enums, the module is already initialized and doesn't re-enter
# the experiment package initialization.
import easydiffraction.experiments.experiment.enums as _exp_enums  # noqa: F401
from easydiffraction.experiments.datastore.factory import DatastoreFactory


def test_create_powder_and_sc_datastores():
    ds_pd = DatastoreFactory.create(sample_form='powder', beam_mode='constant wavelength')
    assert hasattr(ds_pd, 'beam_mode')

    ds_sc = DatastoreFactory.create(sample_form='single crystal', beam_mode='constant wavelength')
    assert not hasattr(ds_sc, 'beam_mode')


def test_create_invalid_sample_form_raises():
    with pytest.raises(ValueError):
        DatastoreFactory.create(sample_form='unknown', beam_mode='constant wavelength')
