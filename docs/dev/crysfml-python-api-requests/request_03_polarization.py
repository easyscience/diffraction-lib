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
  LAMBDA  1.54056  1.54056  0.0
  UVWXY  0.036631  -0.068345  0.131426  0.0  0.0
  CTHM  0.8
  RKK  0.5
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
    0.0014706, 0.0136294, 0.0630261477, 0.219173852,
    0.7485706, 2.2479706, 5.9006289, 13.5695261,
    27.3656739, 48.3650706, 74.9544706, 101.847029,
    121.336426, 126.722574, 116.051471, 93.1708706,
    65.5835294, 40.4729261, 21.8990739, 10.3879711,
    4.3173706, 1.5800294, 0.509426148, 0.135573852,
    0.0349706, 0.0038711, 0.0065294, 0.00592614771,
    0.0020738523, 0.0214706, 0.1003711, 0.4630294,
    1.78242615, 6.01857385, 17.7779706, 46.0473706,
    104.459529, 207.658926, 361.715074, 552.084471,
    738.333771, 865.226429, 888.425426, 799.341474,
    630.180871, 435.320271, 263.502929, 139.761826,
    64.9479739, 26.4473706, 9.4367706, 2.9494294,
    0.808826148, 0.194973852, 0.0438711, 0.0032706,
    0.0059294, 0.00532614771, 0.0114738523, 0.0508706,
    0.2097711, 0.7724294, 2.42182615, 6.64797385,
    15.9873706, 33.6762711, 62.1389294, 100.388326,
    142.044474, 176.003771, 190.983171, 181.485429,
    151.034726, 110.060874, 70.2402706, 39.2596706,
    19.2218294, 8.24122615, 3.08737385, 1.0167706,
    0.2861706,
])


def main() -> None:
    control = compare_to_fullprof(
        'without X-ray polarization',
        CONTROL_CFL,
        FULLPROF_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_to_fullprof(
        'with X-ray polarization requested in CFL',
        REQUESTED_CFL,
        FULLPROF_REQUESTED,
        x_shift=Y2O3_X_SHIFT,
        scale_override=control.scale,
    )
    comparisons = [control, requested]
    print_summary('Request 3: X-ray polarization', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 3: X-ray polarization', comparisons)


if __name__ == '__main__':
    main()
