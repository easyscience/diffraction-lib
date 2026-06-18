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
  Preferred_Orientation  0.0  0.0  1.0  1.0  1.2  0.3
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
    25.6914706, 5.9736294, 1.22302615, 0.229173852,
    0.1085706, 0.4679706, 2.7006289, 13.7895261,
    61.9556739, 244.065071, 842.954471, 2552.29703,
    6774.51643, 15764.3226, 32156.1115, 57500.7109,
    90137.2135, 123867.223, 149222.289, 157588.318,
    145893.367, 118404.58, 84240.8094, 52538.7956,
    28725.835, 13768.4839, 5785.24653, 2130.98593,
    688.062074, 194.781471, 48.3503711, 10.5330294,
    2.04242615, 0.478573852, 0.9179706, 5.0873706,
    26.3395294, 119.968926, 479.075074, 1676.04447,
    5137.46377, 13796.9164, 32462.5054, 66922.2415,
    120864.741, 191247.18, 265128.863, 322021.802,
    342673.088, 319474.837, 260951.507, 186745.169,
    117086.089, 64314.005, 30952.1239, 13050.9333,
    4821.26593, 1560.45533, 442.461474, 109.940871,
    23.9497711, 4.6124294, 1.00182615, 1.50797385,
    7.8673706, 38.9162711, 169.248929, 644.728326,
    2150.85447, 6282.49377, 16068.5432, 35986.7254,
    70571.4747, 121186.011, 182211.76, 239894.94,
    276558.082, 279172.341, 246758.867, 190983.457,
    129431.316,
])


def main() -> None:
    control = compare_to_fullprof(
        'without preferred orientation',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with preferred orientation requested in CFL',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 1: preferred orientation', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 1: preferred orientation', comparisons)


if __name__ == '__main__':
    main()
