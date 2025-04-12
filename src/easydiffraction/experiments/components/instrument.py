from easydiffraction.core.objects import (
    Parameter,
    Component
)
from easydiffraction.core.constants import (DEFAULT_BEAM_MODE,
                                            DEFAULT_DIFFRACTION_TYPE)

class InstrumentBase(Component):
    @property
    def category_key(self):
        return "instrument"

    @property
    def cif_category_key(self):
        return "instr"

    @property
    def _entry_id(self):
        return None


class ConstantWavelengthInstrument(InstrumentBase):
    def __init__(self,
                 setup_wavelength=1.5406,
                 calib_twotheta_offset=0):
        super().__init__()

        self.setup_wavelength = Parameter(
            value=setup_wavelength,
            name="wavelength",
            cif_name="wavelength",
            units="Å",
            description="Incident neutron or X-ray wavelength"
        )
        self.calib_twotheta_offset = Parameter(
            value=calib_twotheta_offset,
            name="twotheta_offset",
            cif_name="2theta_offset",
            units="deg",
            description="Instrument misalignment offset"
        )

        #self._locked = True  # Lock further attribute additions


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
            name="twotheta_bank",
            cif_name="2theta_bank",
            units="deg",
            description="Detector bank position"
        )
        self.calib_d_to_tof_offset = Parameter(
            value=calib_d_to_tof_offset,
            name="d_to_tof_offset",
            cif_name="d_to_tof_offset",
            units="µs",
            description="TOF offset"
        )
        self.calib_d_to_tof_linear = Parameter(
            value=calib_d_to_tof_linear,
            name="d_to_tof_linear",
            cif_name="d_to_tof_linear",
            units="µs/Å",
            description="TOF linear conversion"
        )
        self.calib_d_to_tof_quad = Parameter(
            value=calib_d_to_tof_quad,
            name="d_to_tof_quad",
            cif_name="d_to_tof_quad",
            units="µs/Å²",
            description="TOF quadratic correction"
        )
        self.calib_d_to_tof_recip = Parameter(
            value=calib_d_to_tof_recip,
            name="d_to_tof_recip",
            cif_name="d_to_tof_recip",
            units="µs·Å",
            description="TOF reciprocal velocity correction"
        )

        #self._locked = True  # Lock further attribute additions

class PDFInstrumentMixin():
    def _add_instrument_parameters(self):
        self.qmax: Parameter = Parameter(
            value=0.0,
            name="qmax",
            cif_name="pdf_qmax",
            units="",
            description="Q-value cutoff for PDF calculation"
        )
        self.qdamp = Parameter(
            value=0.0,
            name="qdamp",
            cif_name="pdf_qdamp",
            units="",
            description="Instrumental Q-resolution factor"
        )
        self.delta1: Parameter = Parameter(
            value=0.0,
            name="delta1",
            cif_name="pdf_delta1",
            units="",
            description="1/R peak sharpening factor"
        )
        self.delta2: Parameter = Parameter(
            value=0.0,
            name="delta2",
            cif_name="pdf_delta2",
            units="",
            description="(1/R^2) sharpening factor"
        )
        self.qbroad: Parameter = Parameter(
            value=0.0,
            name="qbroad",
            cif_name="pdf_qbroad",
            units="",
            description="Quadratic peak broadening factor"
        )
        self.spdiameter: Parameter = Parameter(
            value=0.0,
            name="spdiameter",
            cif_name="pdf_spdiameter",
            units="",
            description="Diameter value for the spherical particle PDF correction"
        )

class PDFCWInstrument(ConstantWavelengthInstrument, PDFInstrumentMixin):
    _description = "Pair-Distribution Function (PDF) instrument with constant wavelength"
    def __init__(self):
        super().__init__()
        self._add_instrument_parameters()
        self._locked = True  # Lock further attribute additions

class PDFTOFInstrument(TimeOfFlightInstrument, PDFInstrumentMixin):
    _description = "Pair-Distribution Function (PDF) instrument with time-of-flight"
    def __init__(self):
        super().__init__()
        self._add_instrument_parameters()
        self._locked = True  # Lock further attribute additions

class InstrumentFactory:
    _supported = {
        "constant wavelength": {
            "conventional": ConstantWavelengthInstrument,
            "total" : PDFCWInstrument,
        },
        "time-of-flight": {
            "conventional": TimeOfFlightInstrument,
            "total" : PDFTOFInstrument,
        }
    }

    @classmethod
    def create(cls,
               beam_mode=DEFAULT_BEAM_MODE,
               diffraction_type=DEFAULT_DIFFRACTION_TYPE):
        if beam_mode not in cls._supported:
            supported = list(cls._supported.keys())
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}'.\n "
                f"Supported beam modes are: {supported}"
            )
        if diffraction_type not in cls._supported[beam_mode]:
            supported = list(cls._supported[beam_mode].keys())
            raise ValueError(
                f"Unsupported diffraction type: '{diffraction_type}'.\n "
                f"Supported diffraction types for {beam_mode} are: {supported}"
            )

        instrument_class = cls._supported[beam_mode][diffraction_type]
        instance = instrument_class()
        return instance