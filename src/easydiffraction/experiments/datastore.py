# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

import numpy as np

from easydiffraction.core.constants import DEFAULT_BEAM_MODE
from easydiffraction.core.constants import DEFAULT_SAMPLE_FORM


class BaseDatastore:
    """Base class for all data stores."""

    def __init__(self) -> None:
        self.meas: Optional[np.ndarray] = None
        self.meas_su: Optional[np.ndarray] = None
        self.excluded: Optional[np.ndarray] = None  # Flags for excluded points
        self._calc: Optional[np.ndarray] = None  # Cached calculated intensities

    @property
    def calc(self) -> Optional[np.ndarray]:
        """Access calculated intensities. Should be updated via external calculation."""
        return self._calc

    @calc.setter
    def calc(self, values: np.ndarray) -> None:
        """Set calculated intensities (from Analysis.calculate_pattern())."""
        self._calc = values

    @abstractmethod
    def _cif_mapping(self) -> dict[str, str]:
        """
        Must be implemented in subclasses to return a mapping from attribute names to CIF tags.
        """
        pass

    def as_cif(self, max_points: Optional[int] = None):
        mapping = self._cif_mapping()
        cif_lines = ['loop_']
        for cif_tag in mapping.values():
            cif_lines.append(cif_tag)

        # Collect data arrays according to mapping keys
        arrays = []
        for attr_name in mapping.keys():
            attr_value = getattr(self, attr_name, None)
            if attr_value is None:
                arrays.append([])
            else:
                arrays.append(attr_value)

        # Determine number of points
        length = len(arrays[0]) if arrays and arrays[0] is not None else 0

        if max_points is not None and length > 2 * max_points:
            for i in range(max_points):
                line_values = [arrays[j][i] for j in range(len(arrays))]
                cif_lines.append(' '.join(str(v) for v in line_values))
            cif_lines.append('...')
            for i in range(-max_points, 0):
                line_values = [arrays[j][i] for j in range(len(arrays))]
                cif_lines.append(' '.join(str(v) for v in line_values))
        else:
            for i in range(length):
                line_values = [arrays[j][i] for j in range(len(arrays))]
                cif_lines.append(' '.join(str(v) for v in line_values))

        cif_str = '\n'.join(cif_lines)

        return cif_str


class PowderDatastore(BaseDatastore):
    """Class for powder diffraction data"""

    def __init__(self, beam_mode=DEFAULT_BEAM_MODE) -> None:
        super().__init__()
        self.x: Optional[np.ndarray] = None
        self.d: Optional[np.ndarray] = None
        self.bkg: Optional[np.ndarray] = None
        self.beam_mode = beam_mode

    def _cif_mapping(self) -> dict[str, str]:
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
    """Class for single crystal diffraction data."""

    def __init__(self) -> None:
        super().__init__()
        self.sin_theta_over_lambda: Optional[np.ndarray] = None
        self.h: Optional[np.ndarray] = None
        self.k: Optional[np.ndarray] = None
        self.l: Optional[np.ndarray] = None

    def _cif_mapping(self) -> dict[str, str]:
        return {
            'h': '_refln.index_h',
            'k': '_refln.index_k',
            'l': '_refln.index_l',
            'meas': '_refln.intensity_meas',
            'meas_su': '_refln.intensity_meas_su',
        }


class DatastoreFactory:
    _supported = {
        'powder': PowderDatastore,
        'single crystal': SingleCrystalDatastore,
    }

    @classmethod
    def create(cls, sample_form=DEFAULT_SAMPLE_FORM, beam_mode=DEFAULT_BEAM_MODE):
        """
        Create and return a datastore object for the given sample form.
        Raises ValueError if the sample form is not supported.
        """
        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(f"Unsupported sample form: '{sample_form}'.\nSupported sample forms: {supported_sample_forms}")

        datastore_class = cls._supported[sample_form]
        if sample_form == 'powder':
            datastore_obj = datastore_class(beam_mode=beam_mode)
        else:
            datastore_obj = datastore_class()

        return datastore_obj
