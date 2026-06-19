from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


from cfl_common import compare_to_fullprof
from cfl_common import fullprof_array
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot


WINDOW_START = 55.5
WINDOW_STEP = 0.05
Y2O3_X_SHIFT = -0.01625


def _window_array(intensities: list[float]) -> np.ndarray:
    return fullprof_array([
        [WINDOW_START + WINDOW_STEP * index, intensity]
        for index, intensity in enumerate(intensities)
    ])


# Edit these CFL blocks to experiment with CrysFML output.
CONTROL_CFL = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  55.51625  0.05  59.51625
END_PATTERN_Y2O3

PHASE_Y2O3  1
  Cell  10.605744  10.605744  10.605744  90.0  90.0  90.0
  SPGR  I a -3
  Atom  Y1  Y  -0.03236  0.0  0.25  0.0  0.5
  Atom  Y2  Y   0.25     0.25 0.25  0.0  0.16667
  Atom  O1  O   0.39072  0.15204  0.38030  0.0  1.0
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_Y2O3
"""

REQUESTED_CFL = """
PATTERN_Y2O3  1
  Patt_Type  Neutrons Powder CW
  Zero_Sy  0.0  0.01153  0.24334
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54822  1.54822  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  GEN_PATT  55.51625  0.05  59.51625
END_PATTERN_Y2O3

PHASE_Y2O3  1
  Cell  10.605744  10.605744  10.605744  90.0  90.0  90.0
  SPGR  I a -3
  Atom  Y1  Y  -0.03236  0.0  0.25  0.0  0.5
  Atom  Y2  Y   0.25     0.25 0.25  0.0  0.16667
  Atom  O1  O   0.39072  0.15204  0.38030  0.0  1.0
  Contributes_to_patterns  1
  Scale_Factors  1.0
END_PHASE_Y2O3
"""

# Generated with FullProf 8.40 from the PCR files in fullprof/.
FULLPROF_CONTROL = _window_array([
    1.8614706, 0.4336294, 0.0930261477, 0.0191738523,
    0.0085706, 0.0579706, 0.3406289, 1.70952615,
    7.68567385, 30.2850706, 104.584471, 316.667029,
    840.526426, 1955.90257, 3989.66147, 7134.21087,
    11183.4735, 15368.4129, 18514.2491, 19552.238,
    18101.2274, 14690.65, 10451.8994, 6518.57557,
    3564.05497, 1708.27387, 717.786529, 264.395926,
    85.3720739, 24.1614706, 6.0003711, 1.3130294,
    0.252426148, 0.0685738523, 0.1779706, 0.9973706,
    5.1995294, 23.6689261, 94.5050739, 330.644471,
    1013.50377, 2721.82643, 6404.13543, 13202.2715,
    23843.9409, 37728.8403, 52304.0629, 63527.7818,
    67601.818, 63025.3174, 51479.9568, 36840.6894,
    23098.4988, 12687.725, 6106.16387, 2574.66327,
    951.125929, 307.845326, 87.2814739, 21.6908706,
    4.7197711, 0.9124294, 0.181826148, 0.187973852,
    0.9573706, 4.7162711, 20.5289294, 78.1983261,
    260.854474, 761.923771, 1948.76317, 4364.40543,
    8558.77473, 14697.2009, 22098.2803, 29093.9897,
    33540.4218, 33857.4812, 29926.4274, 23162.0968,
    15697.1762,
])

FULLPROF_REQUESTED = _window_array([
    190.591471, 75.9536294, 26.5530261, 8.13917385,
    2.1885706, 0.5179706, 0.1106289, 0.0195261477,
    0.0056738523, 0.0450706, 0.2444706, 1.2770294,
    5.88642615, 23.7625739, 84.0914711, 260.850871,
    709.343529, 1691.01293, 3534.10907, 6474.51797,
    10398.1474, 14639.5, 18068.3094, 19549.2556,
    18542.145, 15417.3739, 11237.8365, 7180.85593,
    4022.25207, 1975.15147, 850.260371, 320.873029,
    106.152426, 30.7785739, 7.8279706, 1.7473706,
    0.3495294, 0.0789261477, 0.115073852, 0.6544706,
    3.5037707, 16.496429, 68.055426, 245.981474,
    778.920871, 2161.00027, 5252.69293, 11186.0318,
    20871.568, 34117.5474, 48861.5268, 61308.7594,
    67397.6188, 64912.675, 54774.6839, 40494.5633,
    26228.8859, 14884.3353, 7399.80147, 3223.28087,
    1230.10977, 411.302429, 120.491826, 30.9179739,
    6.9573706, 1.3762711, 0.2589294, 0.138326148,
    0.574473852, 2.9437707, 13.3131706, 52.7854293,
    183.344726, 557.670874, 1485.15027, 3463.26967,
    7071.68183, 12643.8812, 19795.7074, 27137.2268,
    32574.7162,
])


def main() -> None:
    control = compare_to_fullprof(
        'without SyCos/SySin shifts',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with SyCos/SySin shifts requested in CFL',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 4: SyCos/SySin shifts', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 4: SyCos/SySin shifts', comparisons)


if __name__ == '__main__':
    main()
