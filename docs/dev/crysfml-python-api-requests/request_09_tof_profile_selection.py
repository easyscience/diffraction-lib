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

NO_TOF_PROFILE_SELECTION_API = (
    'The inspected Python TOF path does not expose selectable '
    'Jorgensen versus Jorgensen-von-Dreele profile functions, and CFL '
    'profile selection cannot be validated until TOF CFL intensities work.'
)


def main() -> None:
    control = compare_to_fullprof(
        'without TOF profile-selection request',
        Y2O3_CFL_NEUTRON_BETA,
        FULLPROF_Y2O3_BETA_CONTROL,
        x_shift=Y2O3_X_SHIFT,
    )
    requested = compare_unavailable(
        'with TOF profile selection requested',
        FULLPROF_Y2O3_BETA_CONTROL,
        NO_TOF_PROFILE_SELECTION_API,
    )
    comparisons = [control, requested]
    print_summary('Request 9: TOF profile selection', comparisons)
    if should_plot(sys.argv):
        plot_comparisons('Request 9: TOF profile selection', comparisons)


if __name__ == '__main__':
    main()
