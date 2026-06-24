# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum


def test_create_by_tag_returns_expected_classes():
    assert DataRangeFactory.create('cwl-pd').__class__.__name__ == 'CwlPdDataRange'
    assert DataRangeFactory.create('tof-pd').__class__.__name__ == 'TofPdDataRange'
    assert DataRangeFactory.create('sc').__class__.__name__ == 'ScDataRange'


def test_default_tag_for_supported_axes():
    assert (
        DataRangeFactory.default_tag(
            beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
            sample_form=SampleFormEnum.POWDER,
        )
        == 'cwl-pd'
    )
    assert (
        DataRangeFactory.default_tag(
            beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
            sample_form=SampleFormEnum.POWDER,
        )
        == 'tof-pd'
    )
    # Both single-crystal beam modes share one sinθ/λ data range.
    assert (
        DataRangeFactory.default_tag(
            beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
            sample_form=SampleFormEnum.SINGLE_CRYSTAL,
        )
        == 'sc'
    )
    assert (
        DataRangeFactory.default_tag(
            beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
            sample_form=SampleFormEnum.SINGLE_CRYSTAL,
        )
        == 'sc'
    )


def test_create_unsupported_tag_raises():
    with pytest.raises(ValueError, match=r"Unsupported type: 'nonexistent'"):
        DataRangeFactory.create('nonexistent')
