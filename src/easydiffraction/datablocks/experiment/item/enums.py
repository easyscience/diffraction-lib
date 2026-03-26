# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for experiment configuration (forms, modes, types)."""

from enum import Enum


class SampleFormEnum(str, Enum):
    """Physical sample form supported by experiments."""

    POWDER = 'powder'
    SINGLE_CRYSTAL = 'single crystal'

    @classmethod
    def default(cls) -> 'SampleFormEnum':
        """Return the default sample form (POWDER).

        Returns
        -------
        SampleFormEnum
            The default enum member.
        """
        return cls.POWDER

    def description(self) -> str:
        """Return a human-readable description of this sample form.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is SampleFormEnum.POWDER:
            return 'Powdered or polycrystalline sample.'
        elif self is SampleFormEnum.SINGLE_CRYSTAL:
            return 'Single crystal sample.'


class ScatteringTypeEnum(str, Enum):
    """Type of scattering modeled in an experiment."""

    BRAGG = 'bragg'
    TOTAL = 'total'

    @classmethod
    def default(cls) -> 'ScatteringTypeEnum':
        """Return the default scattering type (BRAGG).

        Returns
        -------
        ScatteringTypeEnum
            The default enum member.
        """
        return cls.BRAGG

    def description(self) -> str:
        """Return a human-readable description of this scattering type.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is ScatteringTypeEnum.BRAGG:
            return 'Bragg diffraction for conventional structure refinement.'
        elif self is ScatteringTypeEnum.TOTAL:
            return 'Total scattering for pair distribution function analysis (PDF).'


class RadiationProbeEnum(str, Enum):
    """Incident radiation probe used in the experiment."""

    NEUTRON = 'neutron'
    XRAY = 'xray'

    @classmethod
    def default(cls) -> 'RadiationProbeEnum':
        """Return the default radiation probe (NEUTRON).

        Returns
        -------
        RadiationProbeEnum
            The default enum member.
        """
        return cls.NEUTRON

    def description(self) -> str:
        """Return a human-readable description of this radiation probe.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is RadiationProbeEnum.NEUTRON:
            return 'Neutron diffraction.'
        elif self is RadiationProbeEnum.XRAY:
            return 'X-ray diffraction.'


class BeamModeEnum(str, Enum):
    """Beam delivery mode for the instrument."""

    # TODO: Rename to CWL and TOF
    CONSTANT_WAVELENGTH = 'constant wavelength'
    TIME_OF_FLIGHT = 'time-of-flight'

    @classmethod
    def default(cls) -> 'BeamModeEnum':
        """Return the default beam mode (CONSTANT_WAVELENGTH).

        Returns
        -------
        BeamModeEnum
            The default enum member.
        """
        return cls.CONSTANT_WAVELENGTH

    def description(self) -> str:
        """Return a human-readable description of this beam mode.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is BeamModeEnum.CONSTANT_WAVELENGTH:
            return 'Constant wavelength (CW) diffraction.'
        elif self is BeamModeEnum.TIME_OF_FLIGHT:
            return 'Time-of-flight (TOF) diffraction.'


class CalculatorEnum(str, Enum):
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
class PeakProfileTypeEnum(str, Enum):
    """Available peak profile types per scattering and beam mode."""

    PSEUDO_VOIGT = 'pseudo-voigt'
    SPLIT_PSEUDO_VOIGT = 'split pseudo-voigt'
    THOMPSON_COX_HASTINGS = 'thompson-cox-hastings'
    PSEUDO_VOIGT_IKEDA_CARPENTER = 'pseudo-voigt * ikeda-carpenter'
    PSEUDO_VOIGT_BACK_TO_BACK = 'pseudo-voigt * back-to-back'
    GAUSSIAN_DAMPED_SINC = 'gaussian-damped-sinc'

    @classmethod
    def default(
        cls,
        scattering_type: ScatteringTypeEnum | None = None,
        beam_mode: BeamModeEnum | None = None,
    ) -> 'PeakProfileTypeEnum':
        """Return the default peak profile type for a given mode.

        Parameters
        ----------
        scattering_type : ScatteringTypeEnum | None, default=None
            Scattering type; defaults to ``ScatteringTypeEnum.default()``
            when ``None``.
        beam_mode : BeamModeEnum | None, default=None
            Beam mode; defaults to ``BeamModeEnum.default()`` when
            ``None``.

        Returns
        -------
        PeakProfileTypeEnum
            The default profile type for the given combination.
        """
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        return {
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): cls.PSEUDO_VOIGT,
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.PSEUDO_VOIGT_IKEDA_CARPENTER,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): cls.GAUSSIAN_DAMPED_SINC,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): cls.GAUSSIAN_DAMPED_SINC,
        }[(scattering_type, beam_mode)]

    def description(self) -> str:
        """Return a human-readable description of this peak profile type.

        Returns
        -------
        str
            Description string for the current enum member.
        """
        if self is PeakProfileTypeEnum.PSEUDO_VOIGT:
            return 'Pseudo-Voigt profile'
        elif self is PeakProfileTypeEnum.SPLIT_PSEUDO_VOIGT:
            return 'Split pseudo-Voigt profile with empirical asymmetry correction.'
        elif self is PeakProfileTypeEnum.THOMPSON_COX_HASTINGS:
            return 'Thompson-Cox-Hastings profile with FCJ asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER:
            return 'Pseudo-Voigt profile with Ikeda-Carpenter asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_BACK_TO_BACK:
            return 'Pseudo-Voigt profile with Back-to-Back Exponential asymmetry correction.'
        elif self is PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC:
            return 'Gaussian-damped sinc profile for pair distribution function (PDF) analysis.'
