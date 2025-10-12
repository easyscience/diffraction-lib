# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Peak category entry point (public facade).

End users should import Peak classes from this module. Internals live
under the package
`easydiffraction.experiments.category_items.peak_profiles` and are
re-exported here for a stable and readable API.
"""

from easydiffraction.experiments.category_items.peak_profiles.base import PeakBase
from easydiffraction.experiments.category_items.peak_profiles.base import PeakFactory

# Re-export concrete classes for public API stability
from easydiffraction.experiments.category_items.peak_profiles.cw import (
    ConstantWavelengthPseudoVoigt,
)
from easydiffraction.experiments.category_items.peak_profiles.cw import (
    ConstantWavelengthSplitPseudoVoigt,
)
from easydiffraction.experiments.category_items.peak_profiles.cw import (
    ConstantWavelengthThompsonCoxHastings,
)
from easydiffraction.experiments.category_items.peak_profiles.pdf import (
    PairDistributionFunctionGaussianDampedSinc,
)
from easydiffraction.experiments.category_items.peak_profiles.tof import TimeOfFlightPseudoVoigt
from easydiffraction.experiments.category_items.peak_profiles.tof import (
    TimeOfFlightPseudoVoigtBackToBack,
)
from easydiffraction.experiments.category_items.peak_profiles.tof import (
    TimeOfFlightPseudoVoigtIkedaCarpenter,
)
from easydiffraction.experiments.experiment_types.enums import PeakProfileTypeEnum

__all__ = [
    'PeakBase',
    'PeakFactory',
    'PeakProfileTypeEnum',
    'ConstantWavelengthPseudoVoigt',
    'ConstantWavelengthSplitPseudoVoigt',
    'ConstantWavelengthThompsonCoxHastings',
    'TimeOfFlightPseudoVoigt',
    'TimeOfFlightPseudoVoigtIkedaCarpenter',
    'TimeOfFlightPseudoVoigtBackToBack',
    'PairDistributionFunctionGaussianDampedSinc',
]
