# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

from numpy.testing import assert_almost_equal


TEMP_DIR = tempfile.gettempdir()


def test_neutron_pd_cwl_lbco_crysfml(tmp_path) -> None:
    import easydiffraction as ed

    # Create a project from CIF files
    project = ed.Project()
    project.structures.add_from_cif_path(ed.download_data(id=1, destination='data'))
    project.experiments.add_from_cif_path(ed.download_data(id=2, destination='data'))

    # Set constraints
    project.analysis.aliases.create(
        label='biso_La',
        param=project.structures['lbco'].atom_sites['La'].b_iso,
    )
    project.analysis.aliases.create(
        label='biso_Ba',
        param=project.structures['lbco'].atom_sites['Ba'].b_iso,
    )

    project.analysis.aliases.create(
        label='occ_La',
        param=project.structures['lbco'].atom_sites['La'].occupancy,
    )
    project.analysis.aliases.create(
        label='occ_Ba',
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

    # Change calculator
    project.experiments['hrpt'].calculator_type = 'crysfml'

    # Compare calculator
    assert project.experiments['hrpt'].calculator_type == 'crysfml'

    # Perform Analysis 1
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.07,
        decimal=1,
    )


if __name__ == '__main__':
    test_neutron_pd_cwl_lbco_crysfml()
