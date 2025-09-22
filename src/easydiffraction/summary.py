# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from textwrap import wrap
from typing import List

from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import section
from easydiffraction.utils.utils import render_table


class Summary:
    """Generates reports and exports results from the project.

    This class collects and presents all relevant information about the
    fitted model, experiments, and analysis results.
    """

    def __init__(self, project) -> None:
        """Initialize the summary with a reference to the project.

        Args:
            project: The Project instance this summary belongs to.
        """
        self.project = project

    # ------------------------------------------
    #  Report Generation
    # ------------------------------------------

    def show_report(self) -> None:
        self.show_project_info()
        self.show_crystallographic_data()
        self.show_experimental_data()
        self.show_fitting_details()

    def show_project_info(self) -> None:
        """Print the project title and description."""
        print(section('Project info'))

        print(paragraph('Title'))
        print(self.project.info.title)

        if self.project.info.description:
            print(paragraph('Description'))
            print('\n'.join(wrap(self.project.info.description, width=60)))

    def show_crystallographic_data(self) -> None:
        """Print crystallographic data including phase datablocks, space
        groups, cell parameters, and atom sites.
        """
        print(section('Crystallographic data'))

        for model in self.project.sample_models._models.values():
            print(paragraph('Phase datablock'))
            print(f'🧩 {model.name}')

            print(paragraph('Space group'))
            print(model.space_group.name_h_m.value)

            print(paragraph('Cell parameters'))
            columns_alignment: List[str] = ['left', 'right']
            cell_data = [
                [k.replace('length_', '').replace('angle_', ''), f'{v:.5f}']
                for k, v in model.cell.as_dict.items()
            ]
            render_table(
                columns_alignment=columns_alignment,
                columns_data=cell_data,
            )

            print(paragraph('Atom sites'))
            columns_headers = [
                'Label',
                'Type',
                'fract_x',
                'fract_y',
                'fract_z',
                'Occupancy',
                'B_iso',
            ]
            columns_alignment = [
                'left',
                'left',
                'right',
                'right',
                'right',
                'right',
                'right',
            ]
            atom_table = []
            for site in model.atom_sites:
                atom_table.append([
                    site.label.value,
                    site.type_symbol.value,
                    f'{site.fract_x.value:.5f}',
                    f'{site.fract_y.value:.5f}',
                    f'{site.fract_z.value:.5f}',
                    f'{site.occupancy.value:.5f}',
                    f'{site.b_iso.value:.5f}',
                ])
            render_table(
                columns_headers=columns_headers,
                columns_alignment=columns_alignment,
                columns_data=atom_table,
            )

    def show_experimental_data(self) -> None:
        """Print experimental data including experiment datablocks,
        types, instrument settings, and peak profile information.
        """
        print(section('Experiments'))

        for expt in self.project.experiments._experiments.values():
            print(paragraph('Experiment datablock'))
            print(f'🔬 {expt.name}')

            print(paragraph('Experiment type'))
            print(
                f'{expt.type.sample_form.value}, '
                f'{expt.type.radiation_probe.value}, '
                f'{expt.type.beam_mode.value}'
            )

            if 'instrument' in expt._class_public_attrs:
                if 'setup_wavelength' in expt.instrument._class_public_attrs:
                    print(paragraph('Wavelength'))
                    print(f'{expt.instrument.setup_wavelength.value:.5f}')
                if 'calib_twotheta_offset' in expt.instrument._class_public_attrs:
                    print(paragraph('2θ offset'))
                    print(f'{expt.instrument.calib_twotheta_offset.value:.5f}')

            if 'peak_profile_type' in expt._class_public_attrs:
                print(paragraph('Profile type'))
                print(expt.peak_profile_type)

            if 'peak' in expt._class_public_attrs:
                if 'broad_gauss_u' in expt.peak:
                    print(paragraph('Peak broadening (Gaussian)'))
                    columns_alignment = ['left', 'right']
                    columns_data = [
                        ['U', f'{expt.peak.broad_gauss_u.value:.5f}'],
                        ['V', f'{expt.peak.broad_gauss_v.value:.5f}'],
                        ['W', f'{expt.peak.broad_gauss_w.value:.5f}'],
                    ]
                    render_table(
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )
                if 'broad_lorentz_x' in expt.peak:
                    print(paragraph('Peak broadening (Lorentzian)'))
                    columns_alignment = ['left', 'right']
                    columns_data = [
                        ['X', f'{expt.peak.broad_lorentz_x.value:.5f}'],
                        ['Y', f'{expt.peak.broad_lorentz_y.value:.5f}'],
                    ]
                    render_table(
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )

    def show_fitting_details(self) -> None:
        """Print fitting details including calculation and minimization
        engines, and fit quality metrics.
        """
        print(section('Fitting'))

        print(paragraph('Calculation engine'))
        print(self.project.analysis.current_calculator)

        print(paragraph('Minimization engine'))
        print(self.project.analysis.current_minimizer)

        print(paragraph('Fit quality'))
        columns_alignment = ['left', 'right']
        fit_metrics = [
            [
                'Goodness-of-fit (reduced χ²)',
                f'{self.project.analysis.fit_results.reduced_chi_square:.2f}',
            ]
        ]
        render_table(
            columns_alignment=columns_alignment,
            columns_data=fit_metrics,
        )

    # ------------------------------------------
    #  Exporting
    # ------------------------------------------

    def as_cif(self) -> str:
        """Export the final fitted data and analysis results as CIF
        format.
        """
        return 'To be added...'
