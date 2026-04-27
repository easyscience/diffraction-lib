# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for experiment configuration (forms, modes, types)."""

from enum import StrEnum


class SampleFormEnum(StrEnum):
    """Physical sample form supported by experiments."""

    POWDER = 'powder'
    SINGLE_CRYSTAL = 'single crystal'

    @classmethod
    def default(cls) -> 'SampleFormEnum':
        """
        Return the default sample form (POWDER).

        Returns
        -------
        'SampleFormEnum'
            The default enum member.
        """
        return cls.POWDER

    def description(self) -> str:
        """
        Return a human-readable description of this sample form.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is SampleFormEnum.POWDER:
            return 'Powdered or polycrystalline sample.'
        if self is SampleFormEnum.SINGLE_CRYSTAL:
            return 'Single crystal sample.'
        return ''


class ScatteringTypeEnum(StrEnum):
    """Type of scattering modeled in an experiment."""

    BRAGG = 'bragg'
    TOTAL = 'total'

    @classmethod
    def default(cls) -> 'ScatteringTypeEnum':
        """
        Return the default scattering type (BRAGG).

        Returns
        -------
        'ScatteringTypeEnum'
            The default enum member.
        """
        return cls.BRAGG

    def description(self) -> str:
        """
        Return a human-readable description of this scattering type.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is ScatteringTypeEnum.BRAGG:
            return 'Bragg diffraction for conventional structure refinement.'
        if self is ScatteringTypeEnum.TOTAL:
            return 'Total scattering for pair distribution function analysis (PDF).'
        return ''


class RadiationProbeEnum(StrEnum):
    """Incident radiation probe used in the experiment."""

    NEUTRON = 'neutron'
    XRAY = 'xray'

    @classmethod
    def default(cls) -> 'RadiationProbeEnum':
        """
        Return the default radiation probe (NEUTRON).

        Returns
        -------
        'RadiationProbeEnum'
            The default enum member.
        """
        return cls.NEUTRON

    def description(self) -> str:
        """
        Return a human-readable description of this radiation probe.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is RadiationProbeEnum.NEUTRON:
            return 'Neutron diffraction.'
        if self is RadiationProbeEnum.XRAY:
            return 'X-ray diffraction.'
        return None


class BeamModeEnum(StrEnum):
    """Beam delivery mode for the instrument."""

    # TODO: Rename to CWL and TOF
    CONSTANT_WAVELENGTH = 'constant wavelength'
    TIME_OF_FLIGHT = 'time-of-flight'

    @classmethod
    def default(cls) -> 'BeamModeEnum':
        """
        Return the default beam mode (CONSTANT_WAVELENGTH).

        Returns
        -------
        'BeamModeEnum'
            The default enum member.
        """
        return cls.CONSTANT_WAVELENGTH

    def description(self) -> str:
        """
        Return a human-readable description of this beam mode.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is BeamModeEnum.CONSTANT_WAVELENGTH:
            return 'Constant wavelength (CW) diffraction.'
        if self is BeamModeEnum.TIME_OF_FLIGHT:
            return 'Time-of-flight (TOF) diffraction.'
        return None


class CalculatorEnum(StrEnum):
    """Known calculation engine identifiers."""

    CRYSPY = 'cryspy'
    CRYSFML = 'crysfml'
    PDFFIT = 'pdffit'


# TODO: Can, instead of hardcoding here, this info be auto-extracted
#  from the actual peak profile classes defined in peak/cwl.py, tof.py,
#  total.py? So that their Enum variable, string representation and
#  description are defined in the respective classes?
# TODO: Can supported values be defined based on the structure of peak/?
# TODO: Can the same be reused for other enums in this file?
class PeakProfileTypeEnum(StrEnum):
    """Available peak profile types per scattering and beam mode."""

    CWL_PSEUDO_VOIGT = 'cwl-pseudo-voigt'
    CWL_PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY = 'cwl-pseudo-voigt-empirical-asymmetry'
    CWL_THOMPSON_COX_HASTINGS = 'cwl-thompson-cox-hastings'
    TOF_PSEUDO_VOIGT = 'tof-pseudo-voigt'
    TOF_JORGENSEN = 'tof-jorgensen'
    TOF_JORGENSEN_VON_DREELE = 'tof-jorgensen-von-dreele'
    TOF_DOUBLE_JORGENSEN_VON_DREELE = 'tof-double-jorgensen-von-dreele'
    TOTAL_GAUSSIAN_DAMPED_SINC = 'total-gaussian-damped-sinc'

    @classmethod
    def default(
        cls,
        scattering_type: ScatteringTypeEnum | None = None,
        beam_mode: BeamModeEnum | None = None,
    ) -> 'PeakProfileTypeEnum':
        """
        Return the default peak profile type for a given mode.

        Parameters
        ----------
        scattering_type : ScatteringTypeEnum | None, default=None
            Scattering type; defaults to
            ``ScatteringTypeEnum.default()`` when ``None``.
        beam_mode : BeamModeEnum | None, default=None
            Beam mode; defaults to ``BeamModeEnum.default()`` when
            ``None``.

        Returns
        -------
        'PeakProfileTypeEnum'
            The default profile type for the given combination.
        """
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        return {
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): (cls.CWL_PSEUDO_VOIGT),
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.TOF_JORGENSEN,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): (
                cls.TOTAL_GAUSSIAN_DAMPED_SINC
            ),
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): (
                cls.TOTAL_GAUSSIAN_DAMPED_SINC
            ),
        }[scattering_type, beam_mode]

    def description(self) -> str:  # noqa: PLR0911
        """
        Return a human-readable description of this peak profile type.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is PeakProfileTypeEnum.CWL_PSEUDO_VOIGT:
            return 'CWL pseudo-Voigt profile'
        if self is PeakProfileTypeEnum.CWL_PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY:
            return 'CWL pseudo-Voigt profile with empirical asymmetry correction.'
        if self is PeakProfileTypeEnum.CWL_THOMPSON_COX_HASTINGS:
            return 'CWL Thompson-Cox-Hastings profile with FCJ asymmetry correction.'
        if self is PeakProfileTypeEnum.TOF_PSEUDO_VOIGT:
            return 'TOF non-convoluted pseudo-Voigt profile'
        if self is PeakProfileTypeEnum.TOF_JORGENSEN:
            return 'TOF Jorgensen profile: back-to-back exponentials ⊗ Gaussian'
        if self is PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE:
            return 'TOF Jorgensen-Von Dreele profile: back-to-back exponentials ⊗ pseudo-Voigt'
        if self is PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE:
            return (
                'TOF Double-Jorgensen-Von Dreele profile: double back-to-back '
                'exponentials ⊗ pseudo-Voigt (Z-Rietveld type0m)'
            )
        if self is PeakProfileTypeEnum.TOTAL_GAUSSIAN_DAMPED_SINC:
            return 'Total-scattering Gaussian-damped sinc profile for PDF analysis.'
        return None


class ExtinctionModelEnum(StrEnum):
    """Mosaicity distribution model for Becker-Coppens extinction."""

    GAUSS = 'gauss'
    LORENTZ = 'lorentz'

    @classmethod
    def default(cls) -> 'ExtinctionModelEnum':
        """
        Return the default extinction model (GAUSS).

        Returns
        -------
        'ExtinctionModelEnum'
            The default enum member.
        """
        return cls.GAUSS

    def description(self) -> str:
        """
        Return a human-readable description of this extinction model.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is ExtinctionModelEnum.GAUSS:
            return 'Gaussian mosaicity distribution for extinction correction.'
        if self is ExtinctionModelEnum.LORENTZ:
            return 'Lorentzian mosaicity distribution for extinction correction.'
        return None
