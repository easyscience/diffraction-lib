from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

from easydiffraction.experiments.datastore_types.base import BaseDatastore
from easydiffraction.experiments.experiment_types.enums import BeamModeEnum

if TYPE_CHECKING:
    import numpy as np


class PowderDatastore(BaseDatastore):
    """Class for powder diffraction data.

    Attributes:
        x (Optional[np.ndarray]): Scan variable (e.g. 2θ or
            time-of-flight values).
        d (Optional[np.ndarray]): d-spacing values.
        bkg (Optional[np.ndarray]): Background values.
    """

    def __init__(self, beam_mode: Optional[BeamModeEnum] = None) -> None:
        """Initialize PowderDatastore.

        Args:
            beam_mode (str): Beam mode, e.g. 'time-of-flight' or
                'constant wavelength'.
        """
        super().__init__()

        if beam_mode is None:
            beam_mode = BeamModeEnum.default()

        self.beam_mode = beam_mode
        self.x: Optional[np.ndarray] = None
        self.d: Optional[np.ndarray] = None
        self.bkg: Optional[np.ndarray] = None

    def _cif_mapping(self) -> dict[str, str]:
        """Return mapping from attribute names to CIF tags based on beam
        mode.

        Returns:
            dict[str, str]: Mapping dictionary.
        """
        # TODO: Decide where to have validation for beam_mode,
        #  here or in Experiment class or somewhere else.
        return {
            'time-of-flight': {
                'x': '_pd_meas.time_of_flight',
                'meas': '_pd_meas.intensity_total',
                'meas_su': '_pd_meas.intensity_total_su',
            },
            'constant wavelength': {
                'x': '_pd_meas.2theta_scan',
                'meas': '_pd_meas.intensity_total',
                'meas_su': '_pd_meas.intensity_total_su',
            },
        }[self.beam_mode]
