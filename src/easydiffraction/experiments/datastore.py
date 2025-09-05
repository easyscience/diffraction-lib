# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

import numpy as np

from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import SampleFormEnum
from easydiffraction.utils.decorators import enforce_type


class BaseDatastore:
    """
    Base class for all data stores.

    Attributes
    ----------
    meas : Optional[np.ndarray]
        Measured intensities.
    meas_su : Optional[np.ndarray]
        Standard uncertainties of measured intensities.
    excluded : Optional[np.ndarray]
        Flags for excluded points.
    _calc : Optional[np.ndarray]
        Stored calculated intensities.
    """

    def __init__(self) -> None:
        self.meas: Optional[np.ndarray] = None
        self.meas_su: Optional[np.ndarray] = None
        self.excluded: Optional[np.ndarray] = None
        self._calc: Optional[np.ndarray] = None

    @property
    def calc(self) -> Optional[np.ndarray]:
        """Access calculated intensities. Should be updated via external calculation.

        Returns:
            Optional[np.ndarray]: Calculated intensities array or None if not set.
        """
        return self._calc

    @calc.setter
    @enforce_type
    def calc(self, values: np.ndarray) -> None:
        """Set calculated intensities (from Analysis.calculate_pattern()).

        Args:
            values (np.ndarray): Array of calculated intensities.
        """
        self._calc = values

    @abstractmethod
    def _cif_mapping(self) -> dict[str, str]:
        """
        Must be implemented in subclasses to return a mapping from attribute
        names to CIF tags.

        Returns:
            dict[str, str]: Mapping from attribute names to CIF tags.
        """
        pass

    def as_cif(self, max_points: Optional[int] = None) -> str:
        """
        Generate a CIF-formatted string representing the datastore data.

        Args:
            max_points (Optional[int]): Maximum number of points to include
            from start and end.
            If the total points exceed twice this number, data in the middle
            is truncated with '...'.

        Returns:
            str: CIF-formatted string of the data. Empty string if no data available.
        """
        cif_lines = ['loop_']

        # Add CIF tags from mapping
        mapping = self._cif_mapping()
        for cif_key in mapping.values():
            cif_lines.append(cif_key)

        # Collect data arrays according to mapping keys
        data_arrays = []
        for attr_name in mapping.keys():
            attr_array = getattr(self, attr_name, None)
            if attr_array is None:
                data_arrays.append(np.array([]))
            else:
                data_arrays.append(attr_array)

        # Return empty string if no data
        if not data_arrays or not data_arrays[0].size:
            return ''

        # Determine number of points in the first data array
        n_points = len(data_arrays[0])

        # Function to format a single row of data
        def _format_row(i: int) -> str:
            return ' '.join(str(data_arrays[j][i]) for j in range(len(data_arrays)))

        # Add data lines, applying max_points truncation if needed
        if max_points is not None and n_points > 2 * max_points:
            for i in range(max_points):
                cif_lines.append(_format_row(i))
            cif_lines.append('...')
            for i in range(-max_points, 0):
                cif_lines.append(_format_row(i))
        else:
            for i in range(n_points):
                cif_lines.append(_format_row(i))

        cif_str = '\n'.join(cif_lines)

        return cif_str


class PowderDatastore(BaseDatastore):
    """Class for powder diffraction data.

    Attributes
    ----------
    x : Optional[np.ndarray]
        Scan variable (e.g. 2θ or time-of-flight values).
    d : Optional[np.ndarray]
        d-spacing values.
    bkg : Optional[np.ndarray]
        Background values.
    """

    def __init__(self, beam_mode: BeamModeEnum = BeamModeEnum.default()) -> None:
        """
        Initialize PowderDatastore.

        Args:
            beam_mode (str): Beam mode, e.g. 'time-of-flight' or 'constant wavelength'.
        """
        super().__init__()
        self.beam_mode = beam_mode
        self.x: Optional[np.ndarray] = None
        self.d: Optional[np.ndarray] = None
        self.bkg: Optional[np.ndarray] = None

    def _cif_mapping(self) -> dict[str, str]:
        """
        Return mapping from attribute names to CIF tags based on beam mode.

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


class SingleCrystalDatastore(BaseDatastore):
    """Class for single crystal diffraction data.

    Attributes
    ----------
    sin_theta_over_lambda : Optional[np.ndarray]
        sin(θ)/λ values.
    index_h : Optional[np.ndarray]
        Miller index h.
    index_k : Optional[np.ndarray]
        Miller index k.
    index_l : Optional[np.ndarray]
        Miller index l.
    """

    def __init__(self) -> None:
        """
        Initialize SingleCrystalDatastore.
        """
        super().__init__()
        self.sin_theta_over_lambda: Optional[np.ndarray] = None
        self.index_h: Optional[np.ndarray] = None
        self.index_k: Optional[np.ndarray] = None
        self.index_l: Optional[np.ndarray] = None

    def _cif_mapping(self) -> dict[str, str]:
        """
        Return mapping from attribute names to CIF tags for single crystal data.

        Returns:
            dict[str, str]: Mapping dictionary.
        """
        return {
            'index_h': '_refln.index_h',
            'index_k': '_refln.index_k',
            'index_l': '_refln.index_l',
            'meas': '_refln.intensity_meas',
            'meas_su': '_refln.intensity_meas_su',
        }


class DatastoreFactory:
    _supported = {
        'powder': PowderDatastore,
        'single crystal': SingleCrystalDatastore,
    }

    @classmethod
    def create(
        cls,
        sample_form: str = SampleFormEnum.default(),
        beam_mode: str = BeamModeEnum.default(),
    ) -> BaseDatastore:
        """
        Create and return a datastore object for the given sample form.

        Args:
            sample_form (str): Sample form type, e.g. 'powder' or 'single crystal'.
            beam_mode (str): Beam mode for powder sample form.

        Returns:
            BaseDatastore: Instance of a datastore class corresponding to sample form.
        """
        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(f"Unsupported sample form: '{sample_form}'.\nSupported sample forms: {supported_sample_forms}")

        supported_beam_modes = ['time-of-flight', 'constant wavelength']
        if beam_mode not in supported_beam_modes:
            raise ValueError(f"Unsupported beam mode: '{beam_mode}'.\nSupported beam modes: {supported_beam_modes}")

        datastore_class = cls._supported[sample_form]
        if sample_form == 'powder':
            datastore_obj = datastore_class(beam_mode=beam_mode)
        else:
            datastore_obj = datastore_class()

        return datastore_obj
