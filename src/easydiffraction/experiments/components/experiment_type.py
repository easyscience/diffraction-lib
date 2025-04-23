from easydiffraction.core.objects import (
    Descriptor,
    Component
)
from typing import Optional


class ExperimentType(Component):
    def __init__(self,
                 sample_form: str,
                 beam_mode: str,
                 radiation_probe: str) -> None:
        super().__init__()

        self.sample_form: Descriptor = Descriptor(
            value=sample_form,
            name="samle_form",
            cif_name="sample_form",
            description="Specifies whether the diffraction data corresponds to powder diffraction or single crystal diffraction"
        )
        self.beam_mode: Descriptor = Descriptor(
            value=beam_mode,
            name="beam_mode",
            cif_name="beam_mode",
            description="Defines whether the measurement is performed with a constant wavelength (CW) or time-of-flight (TOF) method"
        )
        self.radiation_probe: Descriptor = Descriptor(
            value=radiation_probe,
            name="radiation_probe",
            cif_name="radiation_probe",
            description="Specifies whether the measurement uses neutrons or X-rays"
        )

        self._locked: bool = True  # Lock further attribute additions

    @property
    def cif_category_key(self) -> str:
        return "expt_type"

    @property
    def category_key(self) -> str:
        return "expt_type"

    @property
    def _entry_id(self) -> Optional[str]:
        return None