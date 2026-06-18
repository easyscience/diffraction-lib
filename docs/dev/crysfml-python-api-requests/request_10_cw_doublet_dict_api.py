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
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.54056  0.0
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
  Patt_Type  X-rays Powder CW
  Zero_Sy  0.0  0.0  0.0
  WDT  20.0
  Profile_function  TCH_pVoigt
  ASYM  0.0  0.0
  LAMBDA  1.54056  1.5444  0.5
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
    0.0014706, 0.0136294, 0.0430261477, 0.179173852,
    0.5985706, 1.7979706, 4.7306289, 10.8795261,
    21.9256739, 38.7450706, 60.0544706, 81.6070294,
    97.2164261, 101.532574, 92.9814711, 74.6508706,
    52.5435294, 32.4329261, 17.5490739, 8.3179711,
    3.4573706, 1.2600294, 0.409426148, 0.115573852,
    0.0249706, 0.0038711, 0.0065294, 0.00592614771,
    0.0020738523, 0.0114706, 0.0803711, 0.3830294,
    1.45242615, 4.88857385, 14.4579706, 37.4473706,
    84.9495294, 168.868926, 294.155074, 448.964471,
    600.433771, 703.626429, 722.495426, 650.041474,
    512.470871, 354.020271, 214.292929, 113.661826,
    52.8179739, 21.5073706, 7.6767706, 2.3994294,
    0.658826148, 0.154973852, 0.0338711, 0.0032706,
    0.0059294, 0.00532614771, 0.0114738523, 0.0408706,
    0.1797711, 0.6424294, 2.00182615, 5.47797385,
    13.1873706, 27.7862711, 51.2689294, 82.8383261,
    117.204474, 145.223771, 157.583171, 149.745429,
    124.624726, 90.8208739, 57.9602706, 32.3896706,
    15.8618294, 6.80122615, 2.54737385, 0.8367706,
    0.2361706,
])

FULLPROF_REQUESTED = _window_array([
    0.0014706, 0.0136294, 0.0430261477, 0.179173852,
    0.6085706, 1.8179706, 4.8106289, 11.1595261,
    22.7756739, 41.0050706, 65.2644706, 92.1770294,
    116.036426, 130.892574, 133.131471, 122.790871,
    103.163529, 79.0729261, 55.2290739, 35.0079711,
    20.0373706, 10.2900294, 4.70942615, 1.91557385,
    0.6849706, 0.2138711, 0.0665294, 0.0159261477,
    0.0020738523, 0.0114706, 0.0803711, 0.3830294,
    1.46242615, 4.92857385, 14.6179706, 38.0473706,
    87.0095294, 175.088926, 310.565074, 486.894471,
    677.283771, 840.056429, 934.715426, 939.281474,
    857.850871, 715.370271, 545.542929, 379.721826,
    240.057974, 136.957371, 70.0467706, 31.9294294,
    12.9088261, 4.60497385, 1.4438711, 0.4032706,
    0.0959294, 0.0253261477, 0.0114738523, 0.0408706,
    0.1797711, 0.6424294, 2.01182615, 5.54797385,
    13.4273706, 28.5562711, 53.4489294, 88.2383261,
    128.954474, 167.593771, 194.873171, 204.185429,
    194.214726, 168.730874, 134.340271, 97.9596706,
    65.1518294, 39.2412261, 21.2473739, 10.2767706,
    4.4161706,
])


def main() -> None:
    control = compare_to_fullprof(
        'without CW doublet',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with CW doublet in FullProf',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 10: CW doublet dict API', comparisons)
    print(
        'Note: CFL has LAMBDA lambda1 lambda2 ratio syntax; the requested '
        'gap is the equivalent high-level dict input path.'
    )
    if should_plot(sys.argv):
        plot_comparisons('Request 10: CW doublet dict API', comparisons)


if __name__ == '__main__':
    main()
