from easydiffraction.core.parameter import Descriptor
from easydiffraction.experiments.standard_components.standard_component_base import StandardComponentBase


class ExperimentType(StandardComponentBase):
    cif_category_name = "_expt_type"

    def __init__(self, diffr_mode, expt_mode, radiation_probe, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diffr_mode = Descriptor(diffr_mode,
                                     cif_name='diffr_mode')
        self.expt_mode = Descriptor(expt_mode,
                                    cif_name='expt_mode')
        self.radiation_probe = Descriptor(radiation_probe,
                                          cif_name='radiation_probe')

