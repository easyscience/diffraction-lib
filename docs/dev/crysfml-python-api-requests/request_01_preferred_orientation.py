from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_WITHOUT_PREFERRED_ORIENTATION = fullprof_array([
    [38.5, 26.5957],
    [38.846, 61.605517],
    [39.192, 723.4369],
    [39.538, 3032.2799],
    [39.883, 180.41803],
    [40.229, 42.009483],
    [40.575, 20.8942],
    [40.921, 12.738917],
    [41.267, 8.8470333],
    [41.612, 6.76595],
    [41.958, 5.6115],
    [42.304, 4.9978833],
    [42.65, 4.7827],
    [42.996, 4.8999167],
    [43.342, 5.4171333],
    [43.688, 6.464375],
    [44.033, 8.4216667],
    [44.379, 12.17305],
    [44.725, 20.2661],
    [45.071, 42.314208],
    [45.417, 246.60397],
    [45.762, 2948.9928],
    [46.108, 358.2634],
    [46.454, 46.542375],
    [46.8, 21.2596],
])

FULLPROF_WITH_PREFERRED_ORIENTATION = fullprof_array([
    [38.5, 25.6857],
    [38.846, 59.44135],
    [39.192, 697.62523],
    [39.538, 2923.9574],
    [39.883, 174.02803],
    [40.229, 40.570317],
    [40.575, 20.2192],
    [40.921, 12.361417],
    [41.267, 8.6237],
    [41.612, 6.63095],
    [41.958, 5.5331667],
    [42.304, 4.9778833],
    [42.65, 4.8027],
    [42.996, 4.9690833],
    [43.342, 5.5354667],
    [43.688, 6.661875],
    [44.033, 8.725],
    [44.379, 12.67055],
    [44.725, 21.1761],
    [45.071, 44.296708],
    [45.417, 258.4973],
    [45.762, 3091.9028],
    [46.108, 375.57673],
    [46.454, 48.758208],
    [46.8, 22.2496],
])

LBCO_CFL = """
PATTERN_LBCO  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  30.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.494  1.494  0.0
  UVWXY  0.081547  -0.115345  0.121125  0.0  0.083038
  GEN_PATT  38.5  0.05  46.8
END_PATTERN_LBCO

PHASE_LBCO  1
  Cell  3.89079  3.89079  3.89079  90.0  90.0  90.0
  SPGR  P m -3 m
  Atom  La  La  0.0  0.0  0.0  0.57511  0.01042
  Atom  Ba  Ba  0.0  0.0  0.0  0.57511  0.01042
  Atom  Co  Co  0.5  0.5  0.5  0.26023  0.02083
  Atom  O   O   0.0  0.5  0.5  1.36662  0.06116
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LBCO
"""

LBCO_CFL_WITH_REQUESTED_FEATURE = """
PATTERN_LBCO  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  30.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.494  1.494  0.0
  UVWXY  0.081547  -0.115345  0.121125  0.0  0.083038
  GEN_PATT  38.5  0.05  46.8
END_PATTERN_LBCO

PHASE_LBCO  1
  Cell  3.89079  3.89079  3.89079  90.0  90.0  90.0
  SPGR  P m -3 m
  Atom  La  La  0.0  0.0  0.0  0.57511  0.01042
  Atom  Ba  Ba  0.0  0.0  0.0  0.57511  0.01042
  Atom  Co  Co  0.5  0.5  0.5  0.26023  0.02083
  Atom  O   O   0.0  0.5  0.5  1.36662  0.06116
  ! FullProf feature: March-Dollase r=1.2, fraction=0.3, axis=(0,0,1).
  ! pycrysfml currently has no parsed/applied CFL knob for this feature.
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LBCO
"""


def main() -> None:
    control = compare_to_fullprof(
        'control without preferred orientation',
        LBCO_CFL,
        FULLPROF_WITHOUT_PREFERRED_ORIENTATION,
        x_shift=0.6204,
    )
    requested = compare_to_fullprof(
        'requested feature enabled in FullProf',
        LBCO_CFL_WITH_REQUESTED_FEATURE,
        FULLPROF_WITH_PREFERRED_ORIENTATION,
        x_shift=0.6204,
        scale_override=control.scale,
    )
    print_summary('Request 1: preferred orientation', [control, requested])
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 1: preferred orientation',
            [control, requested],
        )


if __name__ == '__main__':
    main()
