# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from textwrap import wrap

from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.serialize import summary_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class Summary:
    """
    Generates reports and exports results from the project.

    This class collects and presents all relevant information about the
    fitted model, experiments, and analysis results.
    """

    def __init__(self, project: object) -> None:
        """
        Initialize the summary with a reference to the project.

        Parameters
        ----------
        project : object
            The Project instance this summary belongs to.
        """
        self.project = project

    @staticmethod
    def _fmt_row(
        pretty_name: str,
        parameter: Parameter,
    ) -> list[str]:
        digits = 8
        value = f'{parameter.value:.{digits}f}'
        uncertainty = parameter.uncertainty
        uncertainty = f'{uncertainty:.{digits}f}' if uncertainty is not None else ''
        return [pretty_name, value, uncertainty]

    # ------------------------------------------
    #  Report Generation
    # ------------------------------------------

    def show_report(self) -> None:
        """Print a full project report covering all sections."""
        self.show_project_info()
        self.show_crystallographic_data()
        self.show_experimental_data()
        self.show_fitting_details()

    def show_project_info(self) -> None:
        """Print the project title and description."""
        console.section('Project info')

        console.paragraph('Title')
        console.print(self.project.info.title)

        if self.project.info.description:
            console.paragraph('Description')
            # log.print('\n'.join(wrap(self.project.info.description,
            # width=80)))
            # TODO: Fix the following lines
            # Ensure description wraps with explicit newlines for tests
            desc_lines = wrap(self.project.info.description, width=60)
            # Use plain print to avoid Left padding that would break
            # newline adjacency checks
            print('\n'.join(desc_lines))

    def show_crystallographic_data(self) -> None:
        """Print crystallographic data for all phases."""
        console.section('Crystallographic data')

        for structure in self.project.structures.values():
            console.paragraph('Phase datablock')
            console.print(f'🧩 {structure.name}')

            console.paragraph('Space group')
            console.print(structure.space_group.name_h_m.value)

            columns_headers = ['Parameter', 'Value', 'Uncertainty']
            columns_alignment = ['left', 'right', 'right']
            columns_data = [
                Summary._fmt_row('a', structure.cell.length_a),
                Summary._fmt_row('b', structure.cell.length_a),
                Summary._fmt_row('c', structure.cell.length_a),
                Summary._fmt_row('α', structure.cell.angle_alpha),  # noqa: RUF001
                Summary._fmt_row('β', structure.cell.angle_beta),
                Summary._fmt_row('γ', structure.cell.angle_gamma),  # noqa: RUF001
            ]
            render_table(
                columns_headers=columns_headers,
                columns_alignment=columns_alignment,
                columns_data=columns_data,
            )

            console.paragraph('Atom sites')
            columns_headers = [
                'label',
                'type',
                'x',
                'y',
                'z',
                'occ',
                'Biso',
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
            atom_table = [
                [
                    site.label.value,
                    site.type_symbol.value,
                    f'{site.fract_x.value:.8f}',
                    f'{site.fract_y.value:.8f}',
                    f'{site.fract_z.value:.8f}',
                    f'{site.occupancy.value:.8f}',
                    f'{site.adp_iso.value:.8f}',
                ]
                for site in structure.atom_sites
            ]
            render_table(
                columns_headers=columns_headers,
                columns_alignment=columns_alignment,
                columns_data=atom_table,
            )

    def show_experimental_data(self) -> None:
        """Print experimental data for all experiments."""
        console.section('Experiments')

        for expt in self.project.experiments.values():
            console.paragraph('Experiment datablock')
            console.print(f'🔬 {expt.name}')

            console.paragraph('Experiment type')
            console.print(
                f'{expt.type.sample_form.value}, '
                f'{expt.type.radiation_probe.value}, '
                f'{expt.type.beam_mode.value}',
                f'{expt.type.scattering_type.value}',
            )

            console.paragraph('Calculation engine')
            console.print(f'{expt.calculator_type}')

            if 'instrument' in expt._public_attrs():
                if 'setup_wavelength' in expt.instrument._public_attrs():
                    console.paragraph('Wavelength')
                    console.print(f'{expt.instrument.setup_wavelength.value:.5f}')
                if 'calib_twotheta_offset' in expt.instrument._public_attrs():
                    console.paragraph('2θ offset')
                    console.print(f'{expt.instrument.calib_twotheta_offset.value:.5f}')

            if 'peak_profile_type' in expt._public_attrs():
                console.paragraph('Profile type')
                console.print(expt.peak_profile_type)

            if 'peak' in expt._public_attrs():
                if 'broad_gauss_u' in expt.peak._public_attrs():
                    console.paragraph('Peak broadening (Gaussian)')
                    columns_headers = ['Parameter', 'Value', 'Uncertainty']
                    columns_alignment = ['left', 'right', 'right']
                    columns_data = [
                        Summary._fmt_row('U', expt.peak.broad_gauss_u),
                        Summary._fmt_row('V', expt.peak.broad_gauss_v),
                        Summary._fmt_row('W', expt.peak.broad_gauss_w),
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )
                if 'broad_lorentz_x' in expt.peak._public_attrs():
                    console.paragraph('Peak broadening (Lorentzian)')
                    # TODO: Some headers capitalize, some don't -
                    #  be consistent
                    columns_headers = ['Parameter', 'Value', 'Uncertainty']
                    columns_alignment = ['left', 'right', 'right']
                    columns_data = [
                        Summary._fmt_row('X', expt.peak.broad_lorentz_x),
                        Summary._fmt_row('Y', expt.peak.broad_lorentz_y),
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )
                if 'asym_empir_1' in expt.peak._public_attrs():
                    console.paragraph('Asymmetry (Empirical)')
                    columns_headers = ['Parameter', 'Value', 'Uncertainty']
                    columns_alignment = ['left', 'right', 'right']
                    columns_data = [
                        Summary._fmt_row('p1', expt.peak.asym_empir_1),
                        Summary._fmt_row('p2', expt.peak.asym_empir_2),
                        Summary._fmt_row('p3', expt.peak.asym_empir_3),
                        Summary._fmt_row('p4', expt.peak.asym_empir_4),
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )

    def show_fitting_details(self) -> None:
        """Print fitting details including engines and metrics."""
        console.section('Fitting')

        console.paragraph('Minimization engine')
        console.print(self.project.analysis.fit.minimizer_type.value)

        console.paragraph('Fit quality')
        columns_headers = ['metric', 'value']
        columns_alignment = ['left', 'right']
        fit_metrics = [
            [
                'Goodness-of-fit (reduced χ²)',
                f'{self.project.analysis.fit_results.reduced_chi_square:.2f}',
            ]
        ]
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=fit_metrics,
        )

    # ------------------------------------------
    #  Exporting
    # ------------------------------------------

    def as_cif(self) -> str:
        """Export fitted data and analysis results as CIF."""
        return summary_to_cif(self)
