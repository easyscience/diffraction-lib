# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Optional

from typeguard import typechecked

from easydiffraction.io.cif.serialize import datastore_to_cif

if TYPE_CHECKING:
    import numpy as np


class DatastoreBase:
    """Base class for all data stores.

    Attributes:
        meas (Optional[np.ndarray]): Measured intensities.
        meas_su (Optional[np.ndarray]): Standard uncertainties of
            measured intensities.
        excluded (Optional[np.ndarray]): Flags for excluded points.
        _calc (Optional[np.ndarray]): Stored calculated intensities.
    """

    def __init__(self) -> None:
        self.meas: Optional[np.ndarray] = None
        self.meas_su: Optional[np.ndarray] = None
        self.excluded: Optional[np.ndarray] = None
        self._calc: Optional[np.ndarray] = None

    @property
    def calc(self) -> Optional[np.ndarray]:
        """Access calculated intensities. Should be updated via external
        calculation.

        Returns:
            Optional[np.ndarray]: Calculated intensities array or None
                if not set.
        """
        return self._calc

    @calc.setter
    @typechecked
    def calc(self, values: np.ndarray) -> None:
        """Set calculated intensities (from
        Analysis.calculate_pattern()).

        Args:
            values (np.ndarray): Array of calculated intensities.
        """
        self._calc = values

    @abstractmethod
    def _cif_mapping(self) -> dict[str, str]:
        """Must be implemented in subclasses to return a mapping from
        attribute names to CIF tags.

        Returns:
            dict[str, str]: Mapping from attribute names to CIF tags.
        """
        pass

    @property
    def as_cif(self) -> str:
        """Generate a CIF-formatted string representing the datastore
        data.
        """
        return datastore_to_cif(self)

    @property
    def as_truncated_cif(self) -> str:
        """Generate a CIF-formatted string representing the datastore
        data.
        """
        return datastore_to_cif(self, max_points=5)
