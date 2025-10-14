# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

from easydiffraction.experiments.datastore.base import DatastoreBase

if TYPE_CHECKING:
    import numpy as np


class ScDatastore(DatastoreBase):
    """Class for single crystal diffraction data.

    Attributes:
        sin_theta_over_lambda (Optional[np.ndarray]): sin(θ)/λ values.
        index_h (Optional[np.ndarray]): Miller index h.
        index_k (Optional[np.ndarray]): Miller index k.
        index_l (Optional[np.ndarray]): Miller index l.
    """

    def __init__(self) -> None:
        """Initialize SingleCrystalDatastore."""
        super().__init__()
        self.sin_theta_over_lambda: Optional[np.ndarray] = None
        self.index_h: Optional[np.ndarray] = None
        self.index_k: Optional[np.ndarray] = None
        self.index_l: Optional[np.ndarray] = None

    def _cif_mapping(self) -> dict[str, str]:
        """Return mapping from attribute names to CIF tags for single
        crystal data.

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
