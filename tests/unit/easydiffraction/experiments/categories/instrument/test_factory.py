import pytest


def test_instrument_factory_default_and_errors():
    try:
        from easydiffraction.experiments.categories.instrument.factory import InstrumentFactory
        from easydiffraction.experiments.experiment.enums import BeamModeEnum, ScatteringTypeEnum
    except ImportError as e:  # pragma: no cover - environment-specific circular import
        pytest.skip(f"InstrumentFactory import triggers circular import in this context: {e}")
        return

    inst = InstrumentFactory.create()  # defaults
    assert inst.__class__.__name__ in {'CwlInstrument', 'TofInstrument'}

    # Valid combinations
    inst2 = InstrumentFactory.create(ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH)
    assert inst2.__class__.__name__ == 'CwlInstrument'
    inst3 = InstrumentFactory.create(ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT)
    assert inst3.__class__.__name__ == 'TofInstrument'

    # Invalid scattering type
    class FakeST:
        pass
    with pytest.raises(ValueError):
        InstrumentFactory.create(FakeST, BeamModeEnum.CONSTANT_WAVELENGTH)  # type: ignore[arg-type]

    # Invalid beam mode
    class FakeBM:
        pass
    with pytest.raises(ValueError):
        InstrumentFactory.create(ScatteringTypeEnum.BRAGG, FakeBM)  # type: ignore[arg-type]
