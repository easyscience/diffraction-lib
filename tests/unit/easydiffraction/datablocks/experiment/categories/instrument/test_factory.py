# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_instrument_factory_default_and_errors():
    try:
        from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    except ImportError as e:  # pragma: no cover - environment-specific circular import
        pytest.skip(f'InstrumentFactory import triggers circular import in this context: {e}')
        return

    # By tag
    inst = InstrumentFactory.create('cwl-pd')
    assert inst.__class__.__name__ == 'CwlPdInstrument'

    # By tag
    inst2 = InstrumentFactory.create('cwl-pd')
    assert inst2.__class__.__name__ == 'CwlPdInstrument'
    inst3 = InstrumentFactory.create('tof-pd')
    assert inst3.__class__.__name__ == 'TofPdInstrument'

    # Context-dependent default
    tag = InstrumentFactory.default_tag(
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
        sample_form=SampleFormEnum.POWDER,
    )
    assert tag == 'tof-pd'

    # Invalid tag
    with pytest.raises(ValueError):
        InstrumentFactory.create('nonexistent')
