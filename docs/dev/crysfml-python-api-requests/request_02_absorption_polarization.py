from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_UNPOLARIZED_NO_ABSORPTION = fullprof_array([
    [37.5, 0.95],
    [37.9, 2.15],
    [38.275, 7.38],
    [38.65, 522.37],
    [39.05, 10.59],
    [39.45, 2.45],
    [39.825, 1.14],
    [40.2, 0.69],
    [40.6, 0.47],
    [41.0, 0.38],
    [41.375, 0.33],
    [41.75, 0.33],
    [42.15, 0.35],
    [42.55, 0.41],
    [42.925, 0.52],
    [43.3, 0.72],
    [43.7, 1.18],
    [44.1, 2.41],
    [44.475, 7.02],
    [44.85, 135.99],
    [45.25, 25.41],
    [45.65, 4.25],
    [46.025, 1.76],
    [46.4, 0.94],
    [46.8, 0.57],
])

FULLPROF_POLARIZED = fullprof_array([
    [37.5, 1.41],
    [37.9, 3.2],
    [38.275, 10.97],
    [38.65, 776.9],
    [39.05, 15.75],
    [39.45, 3.65],
    [39.825, 1.69],
    [40.2, 1.01],
    [40.6, 0.7],
    [41.0, 0.55],
    [41.375, 0.48],
    [41.75, 0.47],
    [42.15, 0.5],
    [42.55, 0.58],
    [42.925, 0.73],
    [43.3, 1.01],
    [43.7, 1.66],
    [44.1, 3.37],
    [44.475, 9.83],
    [44.85, 190.41],
    [45.25, 35.58],
    [45.65, 5.95],
    [46.025, 2.46],
    [46.4, 1.31],
    [46.8, 0.8],
])

FULLPROF_CYLINDER_ABSORPTION = fullprof_array([
    [37.5, 0.23],
    [37.9, 0.52],
    [38.275, 1.77],
    [38.65, 125.02],
    [39.05, 2.53],
    [39.45, 0.59],
    [39.825, 0.27],
    [40.2, 0.16],
    [40.6, 0.11],
    [41.0, 0.09],
    [41.375, 0.08],
    [41.75, 0.08],
    [42.15, 0.08],
    [42.55, 0.1],
    [42.925, 0.12],
    [43.3, 0.17],
    [43.7, 0.29],
    [44.1, 0.58],
    [44.475, 1.7],
    [44.85, 32.95],
    [45.25, 6.16],
    [45.65, 1.03],
    [46.025, 0.43],
    [46.4, 0.23],
    [46.8, 0.14],
])

LIF_CFL = """
PATTERN_LiF  1
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  48.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.54056  0.0
  UVWXY  0.048457  -0.083053  0.04  0.0  0.049268
  GEN_PATT  37.5  0.025  46.8
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

LIF_CFL_WITH_REQUESTED_FEATURES = """
PATTERN_LiF  1
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  48.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.54056  0.0
  UVWXY  0.048457  -0.083053  0.04  0.0  0.049268
  ! FullProf polarization example: Rpolarz=0.5, Cthm=0.8.
  ! FullProf absorption example: Debye-Scherrer cylinder muR=0.9.
  ! pycrysfml CFL API currently exposes neither user-controlled knob.
  GEN_PATT  37.5  0.025  46.8
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
        'control without absorption or polarization',
        LIF_CFL,
        FULLPROF_UNPOLARIZED_NO_ABSORPTION,
    )
    polarized = compare_to_fullprof(
        'requested polarization enabled in FullProf',
        LIF_CFL_WITH_REQUESTED_FEATURES,
        FULLPROF_POLARIZED,
        scale_override=control.scale,
    )
    absorption = compare_to_fullprof(
        'requested absorption enabled in FullProf',
        LIF_CFL_WITH_REQUESTED_FEATURES,
        FULLPROF_CYLINDER_ABSORPTION,
        scale_override=control.scale,
    )
    comparisons = [control, polarized, absorption]
    print_summary('Request 2: absorption and polarization', comparisons)
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 2: absorption and polarization',
            FULLPROF_UNPOLARIZED_NO_ABSORPTION[:, 0],
            comparisons,
        )


if __name__ == '__main__':
    main()
