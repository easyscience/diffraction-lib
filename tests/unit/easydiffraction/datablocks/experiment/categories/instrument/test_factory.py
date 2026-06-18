# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_instrument_factory_default_and_errors():
    try:
        from easydiffraction.datablocks.experiment.categories.instrument.factory import (
            InstrumentFactory,
        )
        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    except ImportError as e:  # pragma: no cover - environment-specific circular import
        pytest.skip(f'InstrumentFactory import triggers circular import in this context: {e}')
        return

    # By tag
    inst = InstrumentFactory.create('cwl-pd-neutron')
    assert inst.__class__.__name__ == 'CwlPdNeutronInstrument'

    # By tag
    inst2 = InstrumentFactory.create('cwl-pd-xray')
    assert inst2.__class__.__name__ == 'CwlPdXrayInstrument'
    inst3 = InstrumentFactory.create('tof-pd')
    assert inst3.__class__.__name__ == 'TofPdInstrument'

    # Context-dependent default
    tag = InstrumentFactory.default_tag(
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
        sample_form=SampleFormEnum.POWDER,
    )
    assert tag == 'tof-pd'

    neutron_tag = InstrumentFactory.default_tag(
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        radiation_probe=RadiationProbeEnum.NEUTRON,
    )
    assert neutron_tag == 'cwl-pd-neutron'

    xray_tag = InstrumentFactory.default_tag(
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        radiation_probe=RadiationProbeEnum.XRAY,
    )
    assert xray_tag == 'cwl-pd-xray'

    # Invalid tag
    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'nonexistent'\. Supported: .*",
    ):
        InstrumentFactory.create('nonexistent')

    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'cwl-pd'\. Supported: .*",
    ):
        InstrumentFactory.create('cwl-pd')
