from easydiffraction.experiments.components.base import ComponentBase


class ExperimentTypeBase(ComponentBase):
    cif_category_name = "_expt_type"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ExperimentType(ExperimentTypeBase):
    def __init__(self, diffr_mode, expt_mode, radiation_probe, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diffr_mode = diffr_mode
        self.expt_mode = expt_mode
        self.radiation_probe = radiation_probe
