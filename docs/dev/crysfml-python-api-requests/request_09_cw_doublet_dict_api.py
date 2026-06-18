from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_SINGLE_WAVELENGTH = fullprof_array([
    [64.5, 1.1],
    [64.579, 1.3016667],
    [64.658, 1.55],
    [64.737, 1.88],
    [64.817, 2.3266667],
    [64.896, 2.9616667],
    [64.975, 3.89],
    [65.054, 5.33],
    [65.133, 7.7533333],
    [65.213, 12.255],
    [65.292, 22.06],
    [65.371, 56.21],
    [65.45, 322.35],
    [65.529, 630.49667],
    [65.608, 146.95667],
    [65.688, 34.19],
    [65.767, 16.606667],
    [65.846, 9.845],
    [65.925, 6.49],
    [66.004, 4.5983333],
    [66.083, 3.43],
    [66.163, 2.65],
    [66.242, 2.11],
    [66.321, 1.7183333],
    [66.4, 1.43],
])

FULLPROF_CW_DOUBLET = fullprof_array([
    [64.5, 1.5],
    [64.579, 1.7466667],
    [64.658, 2.07],
    [64.737, 2.495],
    [64.817, 3.0533333],
    [64.896, 3.8416667],
    [64.975, 4.97],
    [65.054, 6.69],
    [65.133, 9.5166667],
    [65.213, 14.64],
    [65.292, 25.456667],
    [65.371, 61.41],
    [65.45, 331.22],
    [65.529, 649.61667],
    [65.608, 239.53667],
    [65.688, 360.065],
    [65.767, 148.91],
    [65.846, 33.756667],
    [65.925, 16.53],
    [66.004, 10.32],
    [66.083, 7.1033333],
    [66.163, 5.2],
    [66.242, 3.9766667],
    [66.321, 3.1483333],
    [66.4, 2.55],
])

LIF_SINGLE_WAVELENGTH_CFL = """
PATTERN_LiF  1
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  48.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.54056  0.0
  UVWXY  0.048457  -0.083053  0.04  0.0  0.049268
  GEN_PATT  64.5  0.025  66.4
END_PATTERN_LiF

PHASE_LiF  1
  Cell  4.0267  4.0267  4.0267  90.0  90.0  90.0
  SPGR  F m -3 m
  Atom  Li1  Li  0.0  0.0  0.0  1.2  0.02083
  Atom  F1   F   0.5  0.5  0.5  0.8  0.02083
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LiF
"""

LIF_CW_DOUBLET_CFL = """
PATTERN_LiF  1
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  48.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.5444  0.5
  UVWXY  0.048457  -0.083053  0.04  0.0  0.049268
  GEN_PATT  64.5  0.025  66.4
END_PATTERN_LiF

PHASE_LiF  1
  Cell  4.0267  4.0267  4.0267  90.0  90.0  90.0
  SPGR  F m -3 m
  Atom  Li1  Li  0.0  0.0  0.0  1.2  0.02083
  Atom  F1   F   0.5  0.5  0.5  0.8  0.02083
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LiF
"""


def main() -> None:
    control = compare_to_fullprof(
        'control single wavelength through CFL',
        LIF_SINGLE_WAVELENGTH_CFL,
        FULLPROF_SINGLE_WAVELENGTH,
    )
    requested = compare_to_fullprof(
        'native CFL doublet, requested for dict API',
        LIF_CW_DOUBLET_CFL,
        FULLPROF_CW_DOUBLET,
        scale_override=control.scale,
    )
    print_summary('Request 9: CW doublet dict API', [control, requested])
    print(
        'Note: CFL has LAMBDA lambda1 lambda2 ratio syntax, but this '
        'installed pycrysfml result is not FullProf-equivalent here; '
        'the dict API still has no equivalent input path.'
    )
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 9: CW doublet dict API',
            [control, requested],
        )


if __name__ == '__main__':
    main()
