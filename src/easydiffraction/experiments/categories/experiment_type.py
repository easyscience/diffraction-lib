# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
from easydiffraction.experiments.experiment.enums import SampleFormEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


class ExperimentType(CategoryItem):
    def __init__(
        self,
        *,
        sample_form: str,
        beam_mode: str,
        radiation_probe: str,
        scattering_type: str,
    ):
        super().__init__()

        self._sample_form: StringDescriptor = StringDescriptor(
            name='sample_form',
            description='Specifies whether the diffraction data corresponds to '
            'powder diffraction or single crystal diffraction',
            value_spec=AttributeSpec(
                value=sample_form,
                type_=DataTypes.STRING,
                default=SampleFormEnum.default(),
                content_validator=MembershipValidator(
                    allowed=[member.value for member in SampleFormEnum]
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_expt_type.sample_form',
                ]
            ),
        )

        self._beam_mode: StringDescriptor = StringDescriptor(
            name='beam_mode',
            description='Defines whether the measurement is performed with a '
            'constant wavelength (CW) or time-of-flight (TOF) method',
            value_spec=AttributeSpec(
                value=beam_mode,
                type_=DataTypes.STRING,
                default=BeamModeEnum.default(),
                content_validator=MembershipValidator(
                    allowed=[member.value for member in BeamModeEnum]
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_expt_type.beam_mode',
                ]
            ),
        )
        self._radiation_probe: StringDescriptor = StringDescriptor(
            name='radiation_probe',
            description='Specifies whether the measurement uses neutrons or X-rays',
            value_spec=AttributeSpec(
                value=radiation_probe,
                type_=DataTypes.STRING,
                default=RadiationProbeEnum.default(),
                content_validator=MembershipValidator(
                    allowed=[member.value for member in RadiationProbeEnum]
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_expt_type.radiation_probe',
                ]
            ),
        )
        self._scattering_type: StringDescriptor = StringDescriptor(
            name='scattering_type',
            description='Specifies whether the experiment uses Bragg scattering '
            '(for conventional structure refinement) or total scattering '
            '(for pair distribution function analysis - PDF)',
            value_spec=AttributeSpec(
                value=scattering_type,
                type_=DataTypes.STRING,
                default=ScatteringTypeEnum.default(),
                content_validator=MembershipValidator(
                    allowed=[member.value for member in ScatteringTypeEnum]
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_expt_type.scattering_type',
                ]
            ),
        )

        self._identity.category_code = 'expt_type'

    @property
    def sample_form(self):
        return self._sample_form

    @sample_form.setter
    def sample_form(self, value):
        self._sample_form.value = value

    @property
    def beam_mode(self):
        return self._beam_mode

    @beam_mode.setter
    def beam_mode(self, value):
        self._beam_mode.value = value

    @property
    def radiation_probe(self):
        return self._radiation_probe

    @radiation_probe.setter
    def radiation_probe(self, value):
        self._radiation_probe.value = value

    @property
    def scattering_type(self):
        return self._scattering_type

    @scattering_type.setter
    def scattering_type(self, value):
        self._scattering_type.value = value
