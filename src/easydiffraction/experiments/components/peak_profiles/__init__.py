# SPDX-Copyright:
#   2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Internal implementation package for the Peak category.

This package hosts the implementation details for the Peak category,
split by beam mode/domain. Public consumers should import Peak concepts
from the category entry point
`easydiffraction.experiments.components.peak`.

Re-exports are provided here to make internals discoverable for
contributors and focused tests (e.g., mixins), while keeping end-user
imports stable.
"""

# Core base and factory
from easydiffraction.experiments.components.peak_profiles.base import PeakBase
from easydiffraction.experiments.components.peak_profiles.base import PeakFactory

# Concrete peak profiles
from easydiffraction.experiments.components.peak_profiles.cw import ConstantWavelengthPseudoVoigt
from easydiffraction.experiments.components.peak_profiles.cw import (
    ConstantWavelengthSplitPseudoVoigt,
)
from easydiffraction.experiments.components.peak_profiles.cw import (
    ConstantWavelengthThompsonCoxHastings,
)

# Domain-specific mixins
from easydiffraction.experiments.components.peak_profiles.cw_mixins import (
    ConstantWavelengthBroadeningMixin,
)
from easydiffraction.experiments.components.peak_profiles.cw_mixins import EmpiricalAsymmetryMixin
from easydiffraction.experiments.components.peak_profiles.cw_mixins import FcjAsymmetryMixin
from easydiffraction.experiments.components.peak_profiles.pdf import (
    PairDistributionFunctionGaussianDampedSinc,
)
from easydiffraction.experiments.components.peak_profiles.pdf_mixins import (
    PairDistributionFunctionBroadeningMixin,
)
from easydiffraction.experiments.components.peak_profiles.tof import TimeOfFlightPseudoVoigt
from easydiffraction.experiments.components.peak_profiles.tof import (
    TimeOfFlightPseudoVoigtBackToBack,
)
from easydiffraction.experiments.components.peak_profiles.tof import (
    TimeOfFlightPseudoVoigtIkedaCarpenter,
)
from easydiffraction.experiments.components.peak_profiles.tof_mixins import (
    IkedaCarpenterAsymmetryMixin,
)
from easydiffraction.experiments.components.peak_profiles.tof_mixins import (
    TimeOfFlightBroadeningMixin,
)

__all__ = [
    # Base / factory
    'PeakBase',
    'PeakFactory',
    # Concrete profiles
    'ConstantWavelengthPseudoVoigt',
    'ConstantWavelengthSplitPseudoVoigt',
    'ConstantWavelengthThompsonCoxHastings',
    'TimeOfFlightPseudoVoigt',
    'TimeOfFlightPseudoVoigtBackToBack',
    'TimeOfFlightPseudoVoigtIkedaCarpenter',
    'PairDistributionFunctionGaussianDampedSinc',
    # Mixins
    'ConstantWavelengthBroadeningMixin',
    'EmpiricalAsymmetryMixin',
    'FcjAsymmetryMixin',
    'TimeOfFlightBroadeningMixin',
    'IkedaCarpenterAsymmetryMixin',
    'PairDistributionFunctionBroadeningMixin',
]
