from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfl_common import compare_to_fullprof
from cfl_common import compare_unavailable
from cfl_common import plot_comparisons
from cfl_common import print_summary
from cfl_common import should_plot
from y2o3_common import FULLPROF_Y2O3_BETA_CONTROL
from y2o3_common import Y2O3_CFL_NEUTRON_BETA
from y2o3_common import Y2O3_X_SHIFT

NO_TOF_PATTERN_API = (
    'The inspected patterns_simulation CFL path does not produce a '
    'matching TOF powder profile. This evidence keeps the common Y2O3 '
    '56-60 degree window for the chart and records the TOF API gap.'
)


def main() -> None:
    control = compare_to_fullprof(
        'without TOF patterns_simulation request',
        Y2O3_CFL_NEUTRON_BETA,
        FULLPROF_Y2O3_BETA_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_unavailable(
        'with TOF patterns_simulation requested',
        FULLPROF_Y2O3_BETA_CONTROL,
        NO_TOF_PATTERN_API,
    )
    comparisons = [control, requested]
    print_summary('Request 8: TOF patterns_simulation', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 8: TOF patterns_simulation', comparisons)


if __name__ == '__main__':
    main()
