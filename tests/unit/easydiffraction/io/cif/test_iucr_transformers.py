# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for IUCr category transformers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from easydiffraction.io.cif.handler import TagSpec


class _Descriptor:
    def __init__(self, value, tag='_x.value', cif_name=None):
        self.value = value
        cif_names = [cif_name] if cif_name is not None else None
        self._tags = TagSpec(edi_names=[tag], cif_names=cif_names)


def _items_by_tag(items):
    return {item.tag: item.value for item in items}


def test_wavelength_transformer_emits_monochromatic_items():
    from easydiffraction.io.cif.iucr_transformers import WavelengthTransformer

    experiment = SimpleNamespace(instrument=SimpleNamespace(setup_wavelength=_Descriptor(1.5406)))
    transformer = WavelengthTransformer()

    assert tuple((item.tag, item.value) for item in transformer.items(experiment)) == (
        ('_diffrn_radiation_wavelength.id', '1'),
        ('_diffrn_radiation_wavelength.value', 1.5406),
        ('_diffrn_radiation_wavelength.wt', 1.0),
    )
    assert transformer.loop(experiment) is None


def test_wavelength_transformer_disabled_second_wavelength_is_monochromatic():
    from easydiffraction.io.cif.iucr_transformers import WavelengthTransformer

    # Second wavelength recorded but disabled (ratio == 0): single-row
    # scalar output, matching the CFL `LAMBDA … 0.0` convention.
    instrument = SimpleNamespace(
        setup_wavelength=_Descriptor(1.5406),
        setup_wavelength_2=_Descriptor(1.5444),
        setup_wavelength_2_to_1_ratio=_Descriptor(0.0),
    )
    experiment = SimpleNamespace(instrument=instrument)
    transformer = WavelengthTransformer()

    assert tuple((item.tag, item.value) for item in transformer.items(experiment)) == (
        ('_diffrn_radiation_wavelength.id', '1'),
        ('_diffrn_radiation_wavelength.value', 1.5406),
        ('_diffrn_radiation_wavelength.wt', 1.0),
    )
    assert transformer.loop(experiment) is None


def test_wavelength_transformer_emits_active_doublet_loop():
    from easydiffraction.io.cif.iucr_transformers import WavelengthTransformer

    instrument = SimpleNamespace(
        setup_wavelength=_Descriptor(1.5406),
        setup_wavelength_2=_Descriptor(1.5444),
        setup_wavelength_2_to_1_ratio=_Descriptor(0.5),
    )
    experiment = SimpleNamespace(instrument=instrument)
    transformer = WavelengthTransformer()

    # Active doublet: items() defers and loop() emits the two rows.
    assert transformer.items(experiment) is None
    loop = transformer.loop(experiment)
    assert loop.tags == (
        '_diffrn_radiation_wavelength.id',
        '_diffrn_radiation_wavelength.value',
        '_diffrn_radiation_wavelength.wt',
    )
    assert loop.rows == (
        ('1', 1.5406, 1.0),
        ('2', 1.5444, 0.5),
    )


def test_wavelength_transformer_rejects_incomplete_pair(monkeypatch):
    from easydiffraction.io.cif.iucr_transformers import WavelengthTransformer
    from easydiffraction.utils.logging import Logger

    # A positive ratio with no second wavelength is an incomplete pair:
    # rejected, not silently dropped.
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    instrument = SimpleNamespace(
        setup_wavelength=_Descriptor(1.5406),
        setup_wavelength_2=_Descriptor(0.0),
        setup_wavelength_2_to_1_ratio=_Descriptor(0.5),
    )
    experiment = SimpleNamespace(instrument=instrument)

    with pytest.raises(ValueError):
        WavelengthTransformer().items(experiment)


def test_tof_calibration_transformer_emits_powers_and_ids():
    from easydiffraction.io.cif.iucr_transformers import TofCalibrationTransformer

    instrument = SimpleNamespace(
        calib_d_to_tof_offset=_Descriptor(1.0),
        calib_d_to_tof_linear=_Descriptor(2.0),
        calib_d_to_tof_quadratic=_Descriptor(3.0),
        calib_d_to_tof_reciprocal=_Descriptor(4.0),
    )
    experiment = SimpleNamespace(name='bank1', instrument=instrument)

    loop = TofCalibrationTransformer().loop(experiment)

    assert loop.tags == (
        '_pd_calib_d_to_tof.id',
        '_pd_calib_d_to_tof.power',
        '_pd_calib_d_to_tof.coeff',
        '_pd_calib_d_to_tof.coeff_su',
        '_pd_calib_d_to_tof.diffractogram_id',
    )
    assert loop.rows == (
        ('offset', 0, 1.0, '?', 'bank1'),
        ('linear', 1, 2.0, '?', 'bank1'),
        ('quad', 2, 3.0, '?', 'bank1'),
        ('recip', -1, 4.0, '?', 'bank1'),
    )


def test_excluded_regions_transformer_emits_range_text():
    from easydiffraction.io.cif.iucr_transformers import ExcludedRegionsTransformer

    experiment = SimpleNamespace(
        excluded_regions=[
            SimpleNamespace(start=_Descriptor(10.0), end=_Descriptor(12.0)),
            SimpleNamespace(start=_Descriptor(20.0), end=_Descriptor(25.0)),
        ]
    )

    items = ExcludedRegionsTransformer().items(experiment)

    assert tuple((item.tag, item.value) for item in items) == (
        ('_pd_proc.info_excluded_regions', '10.0 to 12.0; 20.0 to 25.0'),
    )


def test_symmetry_operations_transformer_emits_identity_operation():
    from easydiffraction.io.cif.iucr_transformers import SymmetryOperationsTransformer

    loop = SymmetryOperationsTransformer().loop(SimpleNamespace())

    assert loop.tags == ('_space_group_symop.id', '_space_group_symop.operation_xyz')
    assert loop.rows == (('1', 'x,y,z'),)


def test_extinction_transformer_emits_becker_coppens_type_1():
    from easydiffraction.io.cif.iucr_transformers import ExtinctionTransformer

    extinction = SimpleNamespace(
        type=_Descriptor(
            'becker-coppens',
            cif_name='_easydiffraction_extinction.type',
        ),
        model=_Descriptor(
            'gaussian_isotropic_type1',
            cif_name='_easydiffraction_extinction.model',
        ),
        mosaicity=_Descriptor(
            0.12,
            cif_name='_easydiffraction_extinction.mosaicity',
        ),
    )
    items = _items_by_tag(ExtinctionTransformer().items(SimpleNamespace(extinction=extinction)))

    assert items['_refine_ls.extinction_method'] == ('Becker-Coppens type 1 Gaussian isotropic')
    assert items['_refine_ls.extinction_coef'] == 0.12
    assert items['_easydiffraction_extinction.type'] == 'becker-coppens'
    assert items['_easydiffraction_extinction.model'] == 'gaussian_isotropic_type1'
    assert items['_easydiffraction_extinction.mosaicity'] == 0.12


def test_extinction_transformer_handles_real_switchable_type_property():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )
    from easydiffraction.io.cif.iucr_transformers import ExtinctionTransformer

    extinction = BeckerCoppensExtinction()

    items = _items_by_tag(ExtinctionTransformer().items(SimpleNamespace(extinction=extinction)))

    assert items['_easydiffraction_extinction.type'] == 'becker-coppens'
    assert items['_easydiffraction_extinction.model'] == 'gauss'


def test_extinction_transformer_emits_becker_coppens_type_2():
    from easydiffraction.io.cif.iucr_transformers import ExtinctionTransformer

    extinction = SimpleNamespace(
        type=_Descriptor(
            'becker-coppens',
            cif_name='_easydiffraction_extinction.type',
        ),
        model=_Descriptor(
            'lorentzian_anisotropic_type2',
            cif_name='_easydiffraction_extinction.model',
        ),
        radius=_Descriptor(
            2.5,
            cif_name='_easydiffraction_extinction.radius',
        ),
    )
    items = _items_by_tag(ExtinctionTransformer().items(SimpleNamespace(extinction=extinction)))

    assert items['_refine_ls.extinction_method'] == (
        'Becker-Coppens type 2 Lorentzian anisotropic'
    )
    assert items['_refine_ls.extinction_coef'] == 2.5
    assert items['_easydiffraction_extinction.radius'] == 2.5


def test_extinction_transformer_emits_mixed_becker_coppens_details():
    from easydiffraction.io.cif.iucr_transformers import ExtinctionTransformer

    extinction = SimpleNamespace(
        type=_Descriptor(
            'becker-coppens',
            cif_name='_easydiffraction_extinction.type',
        ),
        model=_Descriptor(
            'mixed_gaussian',
            cif_name='_easydiffraction_extinction.model',
        ),
        mosaicity=_Descriptor(
            0.12,
            cif_name='_easydiffraction_extinction.mosaicity',
        ),
        radius=_Descriptor(
            2.5,
            cif_name='_easydiffraction_extinction.radius',
        ),
    )
    items = _items_by_tag(ExtinctionTransformer().items(SimpleNamespace(extinction=extinction)))

    assert items['_refine_ls.extinction_method'] == ('Becker-Coppens mixed Gaussian isotropic')
    assert items['_refine_ls.extinction_coef'] == '?'
    assert items['_refine.special_details'] == (
        'Becker-Coppens mixed extinction with mosaicity=0.12 and radius=2.5.'
    )


def test_extinction_transformer_emits_zachariasen_method():
    from easydiffraction.io.cif.iucr_transformers import ExtinctionTransformer

    extinction = SimpleNamespace(
        type=_Descriptor(
            'zachariasen',
            cif_name='_easydiffraction_extinction.type',
        ),
        mosaicity=_Descriptor(
            0.05,
            cif_name='_easydiffraction_extinction.mosaicity',
        ),
    )
    items = _items_by_tag(ExtinctionTransformer().items(SimpleNamespace(extinction=extinction)))

    assert items['_refine_ls.extinction_method'] == 'Zachariasen'
    assert items['_refine_ls.extinction_coef'] == 0.05
