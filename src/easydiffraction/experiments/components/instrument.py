from easydiffraction.core.objects import (
    Parameter,
    Component
)
from easydiffraction.core.constants import DEFAULT_BEAM_MODE
from typing import Optional, Type, Dict


class InstrumentBase(Component):
    @property
    def category_key(self) -> str:
        return "instrument"

    @property
    def cif_category_key(self) -> str:
        return "instr"


class ConstantWavelengthInstrument(InstrumentBase):
    def __init__(self,
                 setup_wavelength: float = 1.5406,
                 calib_twotheta_offset: float = 0.0) -> None:
        super().__init__()

        self.setup_wavelength: Parameter = Parameter(
            value=setup_wavelength,
            name="wavelength",
            cif_name="wavelength",
            units="Å",
            description="Incident neutron or X-ray wavelength"
        )
        self.calib_twotheta_offset: Parameter = Parameter(
            value=calib_twotheta_offset,
            name="twotheta_offset",
            cif_name="2theta_offset",
            units="deg",
            description="Instrument misalignment offset"
        )

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class TimeOfFlightInstrument(InstrumentBase):
    def __init__(self,
                 setup_twotheta_bank: float = 150.0,
                 calib_d_to_tof_offset: float = 0.0,
                 calib_d_to_tof_linear: float = 10000.0,
                 calib_d_to_tof_quad: float = -1.0,
                 calib_d_to_tof_recip: float = 0.0) -> None:
        super().__init__()

        self.setup_twotheta_bank: Parameter = Parameter(
            value=setup_twotheta_bank,
            name="twotheta_bank",
            cif_name="2theta_bank",
            units="deg",
            description="Detector bank position"
        )
        self.calib_d_to_tof_offset: Parameter = Parameter(
            value=calib_d_to_tof_offset,
            name="d_to_tof_offset",
            cif_name="d_to_tof_offset",
            units="µs",
            description="TOF offset"
        )
        self.calib_d_to_tof_linear: Parameter = Parameter(
            value=calib_d_to_tof_linear,
            name="d_to_tof_linear",
            cif_name="d_to_tof_linear",
            units="µs/Å",
            description="TOF linear conversion"
        )
        self.calib_d_to_tof_quad: Parameter = Parameter(
            value=calib_d_to_tof_quad,
            name="d_to_tof_quad",
            cif_name="d_to_tof_quad",
            units="µs/Å²",
            description="TOF quadratic correction"
        )
        self.calib_d_to_tof_recip: Parameter = Parameter(
            value=calib_d_to_tof_recip,
            name="d_to_tof_recip",
            cif_name="d_to_tof_recip",
            units="µs·Å",
            description="TOF reciprocal velocity correction"
        )

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class InstrumentFactory:
    _supported: Dict[str, Type[InstrumentBase]] = {
        "constant wavelength": ConstantWavelengthInstrument,
        "time-of-flight": TimeOfFlightInstrument
    }

    @classmethod
    def create(cls, beam_mode: str = DEFAULT_BEAM_MODE) -> InstrumentBase:
        if beam_mode not in cls._supported:
            supported = list(cls._supported.keys())

            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}'.\n "
                f"Supported beam modes are: {supported}"
            )

        instrument_class: Type[InstrumentBase] = cls._supported[beam_mode]
        instance: InstrumentBase = instrument_class()
        return instance
