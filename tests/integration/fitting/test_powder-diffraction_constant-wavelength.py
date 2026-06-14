# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def test_single_fit_neutron_pd_cwl_lbco() -> None:
    # Set structure
    model = StructureFactory.from_scratch(name='lbco')
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.88
    model.atom_sites.create(
        id='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.1,
    )

    # Set experiment
    data_path = download_data('meas-lbco-hrpt', destination=TEMP_DIR)

    expt = ExperimentFactory.from_data_path(
        name='hrpt',
        data_path=data_path,
    )

    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0

    expt.peak.broad_gauss_u = 0.1
    expt.peak.broad_gauss_v = -0.1
    expt.peak.broad_gauss_w = 0.2
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0

    expt.linked_structures.create(structure_id='lbco', scale=5.0)

    expt.background.create(id='1', position=10, intensity=170)
    expt.background.create(id='2', position=165, intensity=170)

    # Create project
    project = Project()
    project.structures.add(model)
    project.experiments.add(expt)

    # Prepare for fitting
    project.analysis.minimizer.type = 'lmfit'

    # ------------ 1st fitting ------------

    # Select fitting parameters
    model.cell.length_a.free = True
    expt.linked_structures['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['1'].intensity.free = True
    expt.background['2'].intensity.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=5.79,
        decimal=1,
    )

    # ------------ 2nd fitting ------------

    # Select fitting parameters
    expt.peak.broad_gauss_u.free = True
    expt.peak.broad_gauss_v.free = True
    expt.peak.broad_gauss_w.free = True
    expt.peak.broad_lorentz_y.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=4.41,
        decimal=1,
    )

    # ------------ 3rd fitting ------------

    # Select fitting parameters
    model.atom_sites['La'].adp_iso.free = True
    model.atom_sites['Ba'].adp_iso.free = True
    model.atom_sites['Co'].adp_iso.free = True
    model.atom_sites['O'].adp_iso.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=1.3,
        decimal=1,
    )


def test_single_fit_neutron_pd_cwl_lbco_with_constraints() -> None:
    # Set structure
    model = StructureFactory.from_scratch(name='lbco')

    space_group = model.space_group
    space_group.name_h_m = 'P m -3 m'

    cell = model.cell
    cell.length_a = 3.8909

    atom_sites = model.atom_sites
    atom_sites.create(
        id='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=1.0,
        occupancy=0.5,
    )
    atom_sites.create(
        id='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=1.0,
        occupancy=0.5,
    )
    atom_sites.create(
        id='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=1.0,
    )
    atom_sites.create(
        id='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=1.0,
    )

    # Set experiment
    data_path = download_data('meas-lbco-hrpt', destination=TEMP_DIR)

    expt = ExperimentFactory.from_data_path(
        name='hrpt',
        data_path=data_path,
    )

    instrument = expt.instrument
    instrument.setup_wavelength = 1.494
    instrument.calib_twotheta_offset = 0.6225

    peak = expt.peak
    peak.broad_gauss_u = 0.0834
    peak.broad_gauss_v = -0.1168
    peak.broad_gauss_w = 0.123
    peak.broad_lorentz_x = 0
    peak.broad_lorentz_y = 0.0797

    background = expt.background
    background.create(id='10', position=10, intensity=174.3)
    background.create(id='20', position=20, intensity=159.8)
    background.create(id='30', position=30, intensity=167.9)
    background.create(id='50', position=50, intensity=166.1)
    background.create(id='70', position=70, intensity=172.3)
    background.create(id='90', position=90, intensity=171.1)
    background.create(id='110', position=110, intensity=172.4)
    background.create(id='130', position=130, intensity=182.5)
    background.create(id='150', position=150, intensity=173.0)
    background.create(id='165', position=165, intensity=171.1)

    expt.linked_structures.create(structure_id='lbco', scale=9.0976)

    # Create project
    project = Project()
    project.structures.add(model)
    project.experiments.add(expt)

    # Prepare for fitting
    project.analysis.minimizer.type = 'lmfit'

    # ------------ 1st fitting ------------

    # Select fitting parameters
    atom_sites['La'].occupancy.free = True
    atom_sites['Ba'].occupancy.free = True
    atom_sites['La'].adp_iso.free = True
    atom_sites['Ba'].adp_iso.free = True
    atom_sites['Co'].adp_iso.free = True
    atom_sites['O'].adp_iso.free = True

    # Compare parameter values before fit
    assert_almost_equal(atom_sites['La'].adp_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['Ba'].adp_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['Co'].adp_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['O'].adp_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, 0.5, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, 0.5, decimal=2)

    # Perform fit
    project.analysis.fit()

    # Compare parameter values after fit
    assert_almost_equal(atom_sites['La'].adp_iso.value, desired=15.0945, decimal=2)
    assert_almost_equal(atom_sites['Ba'].adp_iso.value, desired=0.5226, decimal=2)
    assert_almost_equal(atom_sites['Co'].adp_iso.value, desired=0.2398, decimal=2)
    assert_almost_equal(atom_sites['O'].adp_iso.value, desired=1.4049, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, desired=0.011, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, desired=1.3206, decimal=2)

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=1.24,
        decimal=1,
    )

    # ------------ 2nd fitting ------------

    # Set aliases for parameters
    project.analysis.aliases.create(
        id='biso_La',
        param=atom_sites['La'].adp_iso,
    )
    project.analysis.aliases.create(
        id='biso_Ba',
        param=atom_sites['Ba'].adp_iso,
    )
    project.analysis.aliases.create(
        id='occ_La',
        param=atom_sites['La'].occupancy,
    )
    project.analysis.aliases.create(
        id='occ_Ba',
        param=atom_sites['Ba'].occupancy,
    )

    # Set constraints
    project.analysis.constraints.create(expression='biso_Ba = biso_La')
    project.analysis.constraints.create(expression='occ_Ba = 1 - occ_La')

    # Perform fit
    project.analysis.fit()

    # Compare parameter values after fit
    assert_almost_equal(atom_sites['La'].adp_iso.value, desired=0.5443, decimal=2)
    assert_almost_equal(atom_sites['Ba'].adp_iso.value, desired=0.5443, decimal=2)
    assert_almost_equal(atom_sites['Co'].adp_iso.value, desired=0.2335, decimal=2)
    assert_almost_equal(atom_sites['O'].adp_iso.value, desired=1.4056, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, desired=0.5274, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, desired=0.4726, decimal=2)

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=1.24,
        decimal=1,
    )


def test_fit_neutron_pd_cwl_hs() -> None:
    # Set structure
    model = StructureFactory.from_scratch(name='hs')
    model.space_group.name_h_m = 'R -3 m'
    model.space_group.coord_system_code = 'h'
    model.cell.length_a = 6.8615
    model.cell.length_c = 14.136
    model.atom_sites.create(
        id='Zn',
        type_symbol='Zn',
        fract_x=0,
        fract_y=0,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.1,
    )
    model.atom_sites.create(
        id='Cu',
        type_symbol='Cu',
        fract_x=0.5,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='e',
        adp_iso=1.2,
    )
    model.atom_sites.create(
        id='O',
        type_symbol='O',
        fract_x=0.206,
        fract_y=-0.206,
        fract_z=0.061,
        wyckoff_letter='h',
        adp_iso=0.7,
    )
    model.atom_sites.create(
        id='Cl',
        type_symbol='Cl',
        fract_x=0,
        fract_y=0,
        fract_z=0.197,
        wyckoff_letter='c',
        adp_iso=1.1,
    )
    model.atom_sites.create(
        id='H',
        type_symbol='2H',
        fract_x=0.132,
        fract_y=-0.132,
        fract_z=0.09,
        wyckoff_letter='h',
        adp_iso=2.3,
    )

    # Set experiment
    data_path = download_data('meas-hs-hrpt', destination=TEMP_DIR)

    expt = ExperimentFactory.from_data_path(name='hrpt', data_path=data_path)

    expt.instrument.setup_wavelength = 1.89
    expt.instrument.calib_twotheta_offset = 0.0

    expt.peak.broad_gauss_u = 0.1579
    expt.peak.broad_gauss_v = -0.3571
    expt.peak.broad_gauss_w = 0.3498
    expt.peak.broad_lorentz_x = 0.2927
    expt.peak.broad_lorentz_y = 0

    expt.background.create(id='1', position=4.4196, intensity=648.413)
    expt.background.create(id='2', position=6.6207, intensity=523.788)
    expt.background.create(id='3', position=10.4918, intensity=454.938)
    expt.background.create(id='4', position=15.4634, intensity=435.913)
    expt.background.create(id='5', position=45.6041, intensity=472.972)
    expt.background.create(id='6', position=74.6844, intensity=486.606)
    expt.background.create(id='7', position=103.4187, intensity=472.409)
    expt.background.create(id='8', position=121.6311, intensity=496.734)
    expt.background.create(id='9', position=159.4116, intensity=473.146)

    expt.linked_structures.create(structure_id='hs', scale=0.492)

    # Create project
    project = Project()
    project.structures.add(model)
    project.experiments.add(expt)

    # Prepare for fitting
    project.analysis.minimizer.type = 'lmfit'

    # ------------ 1st fitting ------------

    # Select fitting parameters
    model.cell.length_a.free = True
    model.cell.length_c.free = True
    expt.linked_structures['hs'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.11,
        decimal=1,
    )

    # ------------ 2nd fitting ------------

    # Select fitting parameters
    expt.peak.broad_gauss_u.free = True
    expt.peak.broad_gauss_v.free = True
    expt.peak.broad_gauss_w.free = True
    expt.peak.broad_lorentz_x.free = True
    for point in expt.background:
        point.intensity.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.11,
        decimal=1,
    )

    # ------------ 3rd fitting ------------

    # Select fitting parameters
    model.atom_sites['O'].fract_x.free = True
    model.atom_sites['O'].fract_z.free = True
    model.atom_sites['Cl'].fract_z.free = True
    model.atom_sites['H'].fract_x.free = True
    model.atom_sites['H'].fract_z.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.11,
        decimal=1,
    )

    # ------------ 3rd fitting ------------

    # Select fitting parameters
    model.atom_sites['Zn'].adp_iso.free = True
    model.atom_sites['Cu'].adp_iso.free = True
    model.atom_sites['O'].adp_iso.free = True
    model.atom_sites['Cl'].adp_iso.free = True
    model.atom_sites['H'].adp_iso.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.11,
        decimal=1,
    )

    # ed-6 regression: O and H sit on R-3m 'h' = (x,-x,z), so after freeing
    # and refining fract_x, fract_y must stay slaved to -fract_x (on-site).
    # Operator-form coords_xyz wrongly freed fract_y and let them drift.
    assert_almost_equal(
        model.atom_sites['O'].fract_y.value,
        desired=-model.atom_sites['O'].fract_x.value,
        decimal=6,
    )
    assert_almost_equal(
        model.atom_sites['H'].fract_y.value,
        desired=-model.atom_sites['H'].fract_x.value,
        decimal=6,
    )


def test_single_fit_neutron_pd_cwl_lbco_with_constraints_from_project(tmp_path) -> None:
    import easydiffraction as ed

    # Create a project from CIF files
    project = ed.Project()
    project.structures.add_from_cif_path(ed.download_data('struct-lbco', destination='data'))
    project.experiments.add_from_edi_path(ed.download_data('expt-lbco-hrpt', destination='data'))

    # Set constraints
    project.analysis.aliases.create(
        id='biso_La',
        param=project.structures['lbco'].atom_sites['La'].adp_iso,
    )
    project.analysis.aliases.create(
        id='biso_Ba',
        param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
    )

    project.analysis.aliases.create(
        id='occ_La',
        param=project.structures['lbco'].atom_sites['La'].occupancy,
    )
    project.analysis.aliases.create(
        id='occ_Ba',
        param=project.structures['lbco'].atom_sites['Ba'].occupancy,
    )

    project.analysis.constraints.create(expression='biso_Ba = biso_La')
    project.analysis.constraints.create(expression='occ_Ba = 1 - occ_La')

    # More fit patams
    project.structures['lbco'].atom_sites['La'].occupancy.free = True

    # Save to a directory
    proj_dir = str(tmp_path / 'lbco_project')
    project.save_as(proj_dir)

    # Load Project from Directory
    project = ed.Project.load(proj_dir)

    # Perform Analysis
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=1.28,
        decimal=1,
    )


if __name__ == '__main__':
    test_fit_neutron_pd_cwl_hs()
    test_single_fit_neutron_pd_cwl_lbco()
    test_single_fit_neutron_pd_cwl_lbco_with_constraints()
