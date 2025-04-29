# TODO: Change to use enum for these constants
DEFAULT_SAMPLE_FORM = "powder"
DEFAULT_BEAM_MODE = "constant wavelength"
DEFAULT_RADIATION_PROBE = "neutron"
DEFAULT_BACKGROUND_TYPE = "line-segment"
DEFAULT_SCATTERING_TYPE = "bragg"
DEFAULT_PEAK_PROFILE_TYPE = {
    "bragg": {
        "constant wavelength": "pseudo-voigt",
        "time-of-flight": "pseudo-voigt"
    },
    "total": {
        "constant wavelength": "gaussian-damped-sinc"
    }
}
