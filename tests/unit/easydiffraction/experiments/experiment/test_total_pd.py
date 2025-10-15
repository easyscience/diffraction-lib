import numpy as np
import pytest

from easydiffraction.experiments.categories.experiment_type import ExperimentType
from easydiffraction.experiments.experiment.enums import (
    BeamModeEnum,
    RadiationProbeEnum,
    SampleFormEnum,
    ScatteringTypeEnum,
)
from easydiffraction.experiments.experiment.total_pd import TotalPdExperiment


def _mk_type_powder_total():
    return ExperimentType(
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.TOTAL.value,
    )


def test_load_ascii_data_pdf(tmp_path: pytest.TempPathFactory):
    expt = TotalPdExperiment(name="pdf1", type=_mk_type_powder_total())

    # Mock diffpy.utils.parsers.loaddata.loadData by creating a small parser module on sys.path
    data = np.column_stack([
        np.array([0.0, 1.0, 2.0]),
        np.array([10.0, 11.0, 12.0]),
        np.array([0.01, 0.02, 0.03]),
    ])
    f = tmp_path / "g.dat"
    np.savetxt(f, data)

    # Try to import loadData; if diffpy isn't installed, expect ImportError
    try:
        import diffpy.utils.parsers.loaddata as ld  # type: ignore
        has_diffpy = True
    except Exception:
        has_diffpy = False

    if not has_diffpy:
        with pytest.raises(ImportError):
            expt._load_ascii_data_to_experiment(str(f))
        return

    # With diffpy available, load should succeed
    expt._load_ascii_data_to_experiment(str(f))
    assert np.allclose(expt.datastore.x, data[:, 0])
    assert np.allclose(expt.datastore.meas, data[:, 1])
    assert np.allclose(expt.datastore.meas_su, data[:, 2])
