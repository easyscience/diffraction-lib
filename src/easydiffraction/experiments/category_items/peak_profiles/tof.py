# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.category_items.peak_profiles import PeakBase
from easydiffraction.experiments.category_items.peak_profiles.tof_mixins import (
    IkedaCarpenterAsymmetryMixin,
)
from easydiffraction.experiments.category_items.peak_profiles.tof_mixins import (
    TimeOfFlightBroadeningMixin,
)


class TimeOfFlightPseudoVoigt(
    PeakBase,
    TimeOfFlightBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()


class TimeOfFlightPseudoVoigtIkedaCarpenter(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()


class TimeOfFlightPseudoVoigtBackToBack(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()
