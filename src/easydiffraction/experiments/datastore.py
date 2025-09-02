# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations
from abc import abstractmethod

from typing import Optional

import numpy as np

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
    def as_cif(self):
        """
        Must be implemented in subclasses to return the CIF representation.
        """
        pass


class PowderDatastore(BaseDatastore):
    """Class for powder diffraction data"""

    def __init__(self) -> None:
        super().__init__()
        self.x: Optional[np.ndarray] = None
        self.d: Optional[np.ndarray] = None
        self.bkg: Optional[np.ndarray] = None

    def as_cif(self, max_points: Optional[int] = None):
        cif_lines = []
        cif_lines.append('loop_')
        category = '_pd_meas'  # TODO: Add category to pattern component
        attributes = ('2theta_scan', 'intensity_total', 'intensity_total_su')
        for attribute in attributes:
            cif_lines.append(f'{category}.{attribute}')
        if max_points is not None and len(self.x) > 2 * max_points:
            for i in range(max_points):
                x = self.x[i]
                meas = self.meas[i]
                meas_su = self.meas_su[i]
                cif_lines.append(f'{x} {meas} {meas_su}')
            cif_lines.append('...')
            for i in range(-max_points, 0):
                x = self.x[i]
                meas = self.meas[i]
                meas_su = self.meas_su[i]
                cif_lines.append(f'{x} {meas} {meas_su}')
        else:
            for x, meas, meas_su in zip(self.x, self.meas, self.meas_su):
                cif_lines.append(f'{x} {meas} {meas_su}')

        cif_str = '\n'.join(cif_lines)

        return cif_str


class SingleCrystalDatastore(BaseDatastore):
    """Class for single crystal diffraction data."""

    def __init__(self) -> None:
        super().__init__()
        self.sin_theta_over_lambda: Optional[np.ndarray] = None
        self.h: Optional[np.ndarray] = None
        self.k: Optional[np.ndarray] = None
        self.l: Optional[np.ndarray] = None

    def as_cif(self):
        pass


class DatastoreFactory:
    _supported = {
        'powder': PowderDatastore,
        'single crystal': SingleCrystalDatastore,
    }

    @classmethod
    def create(cls, sample_form=DEFAULT_SAMPLE_FORM):
        """
        Create and return a datastore object for the given sample form.
        Raises ValueError if the sample form is not supported.
        """
        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(f"Unsupported sample form: '{sample_form}'.\n Supported sample forms: {supported_sample_forms}")

        datastore_class = cls._supported[sample_form]
        datastore_obj = datastore_class()

        return datastore_obj
