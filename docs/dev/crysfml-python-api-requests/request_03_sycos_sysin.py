from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot

FULLPROF_WITHOUT_SYCOS_SYSIN = fullprof_array([
    [69.5, 108.79246],
    [69.846, 163.19774],
    [70.192, 273.32776],
    [70.537, 834.84973],
    [70.883, 9949.96],
    [71.229, 36588.462],
    [71.575, 18752.194],
    [71.921, 1853.9249],
    [72.267, 352.70293],
    [72.612, 203.4048],
    [72.958, 141.03844],
    [73.304, 111.1351],
    [73.65, 98.946122],
    [73.996, 100.56844],
    [74.342, 118.10075],
    [74.688, 164.8138],
    [75.033, 342.38155],
    [75.379, 3533.8202],
    [75.725, 18661.708],
    [76.071, 12663.937],
    [76.417, 1357.9797],
    [76.763, 221.79947],
    [77.108, 121.89745],
    [77.454, 79.756893],
    [77.8, 57.029187],
])

FULLPROF_WITH_SYCOS_SYSIN = fullprof_array([
    [69.5, 86.11846],
    [69.846, 122.79391],
    [70.192, 189.64049],
    [70.537, 340.61313],
    [70.883, 1799.0112],
    [71.229, 18400.809],
    [71.575, 36862.574],
    [71.921, 10189.028],
    [72.267, 865.20486],
    [72.612, 285.2998],
    [72.958, 178.02244],
    [73.304, 128.83944],
    [73.65, 105.48412],
    [73.996, 97.767104],
    [74.342, 103.80035],
    [74.688, 128.1421],
    [75.033, 191.02889],
    [75.379, 601.96087],
    [75.725, 7114.2437],
    [76.071, 20953.762],
    [76.417, 7444.5937],
    [76.763, 622.87097],
    [77.108, 177.57412],
    [77.454, 105.70489],
    [77.8, 71.298787],
])

LAB6_CFL = """
PATTERN_LaB6  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  12.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.623899  1.623899  0.0
  UVWXY  0.143431  -0.52314  0.590412  0.0  0.054515
  GEN_PATT  69.5  0.05  77.8
END_PATTERN_LaB6

PHASE_LaB6  1
  Cell  4.156885  4.156885  4.156885  90.0  90.0  90.0
  SPGR  P m -3 m
  Atom  La  La  0.0  0.0  0.0  0.25812  0.02083
  Atom  B   B   0.19972  0.5  0.5  0.11925  0.125
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LaB6
"""

LAB6_CFL_WITH_REQUESTED_FEATURE = """
PATTERN_LaB6  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.01153  0.24334
  WDT  12.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.623899  1.623899  0.0
  UVWXY  0.143431  -0.52314  0.590412  0.0  0.054515
  GEN_PATT  69.5  0.05  77.8
END_PATTERN_LaB6

PHASE_LaB6  1
  Cell  4.156885  4.156885  4.156885  90.0  90.0  90.0
  SPGR  P m -3 m
  Atom  La  La  0.0  0.0  0.0  0.25812  0.02083
  Atom  B   B   0.19972  0.5  0.5  0.11925  0.125
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_LaB6
"""


def main() -> None:
    control = compare_to_fullprof(
        'control with SyCos=0 and SySin=0',
        LAB6_CFL,
        FULLPROF_WITHOUT_SYCOS_SYSIN,
        x_shift=-0.45778,
    )
    requested = compare_to_fullprof(
        'requested SyCos/SySin enabled in FullProf',
        LAB6_CFL_WITH_REQUESTED_FEATURE,
        FULLPROF_WITH_SYCOS_SYSIN,
        x_shift=-0.45778,
        scale_override=control.scale,
    )
    print_summary('Request 3: SyCos and SySin', [control, requested])
    if should_plot(sys.argv):
        plot_comparisons(
            'Request 3: SyCos and SySin',
            FULLPROF_WITHOUT_SYCOS_SYSIN[:, 0],
            [control, requested],
        )


if __name__ == '__main__':
    main()
