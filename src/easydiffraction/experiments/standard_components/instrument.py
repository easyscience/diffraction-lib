from easydiffraction.core.component import StandardComponent
from easydiffraction.core.parameter import Parameter
from easydiffraction.core.constants import DEFAULT_BEAM_MODE


class InstrumentBase(StandardComponent):
    @property
    def cif_category_key(self):
        return "_instr"


class ConstantWavelengthInstrument(InstrumentBase):
    def __init__(self,
                 setup_wavelength=1.5406,
                 calib_twotheta_offset=0):
        super().__init__()

        self.setup_wavelength = Parameter(
            value=setup_wavelength,
            cif_param_name="wavelength",
            units="Å",
            description="Incident neutron or X-ray wavelength"
        )
        self.calib_twotheta_offset = Parameter(
            value=calib_twotheta_offset,
            cif_param_name="2theta_offset",
            units="deg",
            description="Instrument misalignment offset"
        )

        self._locked = True  # Lock further attribute additions


class TimeOfFlightInstrument(InstrumentBase):
    def __init__(self,
                 setup_twotheta_bank=150.0,
                 calib_d_to_tof_offset=0.0,
                 calib_d_to_tof_linear=10000.0,
                 calib_d_to_tof_quad=-1.0,
                 calib_d_to_tof_recip=0.0):
        super().__init__()

        self.setup_twotheta_bank = Parameter(
            value=setup_twotheta_bank,
            cif_param_name="2theta_bank",
            units="deg",
            description="Detector bank position"
        )
        self.calib_d_to_tof_offset = Parameter(
            value=calib_d_to_tof_offset,
            cif_param_name="d_to_tof_offset",
            units="µs",
            description="TOF offset"
        )
        self.calib_d_to_tof_linear = Parameter(
            value=calib_d_to_tof_linear,
            cif_param_name="d_to_tof_linear",
            units="µs/Å",
            description="TOF linear conversion"
        )
        self.calib_d_to_tof_quad = Parameter(
            value=calib_d_to_tof_quad,
            cif_param_name="d_to_tof_quad",
            units="µs/Å²",
            description="TOF quadratic correction"
        )
        self.calib_d_to_tof_recip = Parameter(
            value=calib_d_to_tof_recip,
            cif_param_name="d_to_tof_recip",
            units="µs·Å",
            description="TOF reciprocal velocity correction"
        )

        self._locked = True  # Lock further attribute additions


class InstrumentFactory:
    _supported = {
        "constant wavelength": ConstantWavelengthInstrument,
        "time-of-flight": TimeOfFlightInstrument
    }

    @classmethod
    def create(cls, beam_mode=DEFAULT_BEAM_MODE):
        if beam_mode not in cls._supported:
            supported = list(cls._supported.keys())

            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}'.\n "
                f"Supported beam modes are: {supported}"
            )

        instrument_class = cls._supported[beam_mode]
        instance = instrument_class()
        return instance