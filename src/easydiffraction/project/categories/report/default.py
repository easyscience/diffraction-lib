# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project report display facade."""

from __future__ import annotations

from collections.abc import Iterable
from textwrap import wrap
from typing import TYPE_CHECKING

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.iucr_writer import iucr_report_path
from easydiffraction.io.cif.iucr_writer import write_iucr_cif
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.report.factory import ReportFactory
from easydiffraction.report.check import ReportCheckResult
from easydiffraction.report.check import check_report
from easydiffraction.report.enums import ReportFormatEnum
from easydiffraction.report.enums import ReportStyleEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_object_help
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    import pathlib

    from easydiffraction.core.variable import Parameter


REPORT_STYLE_OPTIONS = [member.value for member in ReportStyleEnum]


@ReportFactory.register
class Report(CategoryItem):
    """
    Generates reports and exports results from the project.

    This class collects and presents all relevant information about the
    fitted model, experiments, and analysis results.
    """

    _category_code = 'report'

    type_info = TypeInfo(
        tag='default',
        description='Project report category',
    )

    def __init__(self) -> None:
        """Initialize report-output configuration descriptors."""
        super().__init__()

        self._cif = BoolDescriptor(
            name='cif',
            description='Whether to write CIF reports when saving.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_report.cif']),
        )
        self._html = BoolDescriptor(
            name='html',
            description='Whether to write HTML reports when saving.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_report.html']),
        )
        self._tex = BoolDescriptor(
            name='tex',
            description='Whether to write TeX reports when saving.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_report.tex']),
        )
        self._pdf = BoolDescriptor(
            name='pdf',
            description='Whether to write PDF reports when saving.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_report.pdf']),
        )
        self._style = StringDescriptor(
            name='style',
            description='Report template style.',
            value_spec=AttributeSpec(
                default=ReportStyleEnum.default().value,
                validator=MembershipValidator(allowed=REPORT_STYLE_OPTIONS),
            ),
            cif_handler=CifHandler(names=['_report.style']),
        )
        self._html_offline = BoolDescriptor(
            name='html_offline',
            description='Whether HTML reports should embed assets.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_report.html_offline']),
        )

    @property
    def cif(self) -> BoolDescriptor:
        """Whether to write CIF reports when saving."""
        return self._cif

    @cif.setter
    def cif(self, value: bool) -> None:
        self._cif.value = value

    @property
    def html(self) -> BoolDescriptor:
        """Whether to write HTML reports when saving."""
        return self._html

    @html.setter
    def html(self, value: bool) -> None:
        self._html.value = value

    @property
    def tex(self) -> BoolDescriptor:
        """Whether to write TeX reports when saving."""
        return self._tex

    @tex.setter
    def tex(self, value: bool) -> None:
        self._tex.value = value

    @property
    def pdf(self) -> BoolDescriptor:
        """Whether to write PDF reports when saving."""
        return self._pdf

    @pdf.setter
    def pdf(self, value: bool) -> None:
        self._pdf.value = value

    @property
    def style(self) -> StringDescriptor:
        """Report template style."""
        return self._style

    @style.setter
    def style(self, value: str) -> None:
        self._style.value = ReportStyleEnum(value).value

    @property
    def html_offline(self) -> BoolDescriptor:
        """Whether HTML reports should embed assets."""
        return self._html_offline

    @html_offline.setter
    def html_offline(self, value: bool) -> None:
        self._html_offline.value = value

    @property
    def formats(self) -> list[ReportFormatEnum]:
        """Enabled report-output formats."""
        formats = []
        if self._cif.value:
            formats.append(ReportFormatEnum.CIF)
        if self._html.value:
            formats.append(ReportFormatEnum.HTML)
        if self._tex.value:
            formats.append(ReportFormatEnum.TEX)
        if self._pdf.value:
            formats.append(ReportFormatEnum.PDF)
        return formats

    @formats.setter
    def formats(
        self,
        formats: Iterable[ReportFormatEnum | str] | ReportFormatEnum | str,
    ) -> None:
        if isinstance(formats, (ReportFormatEnum, str)):
            values = [formats]
        else:
            values = list(formats)
        enabled = {ReportFormatEnum(value) for value in values}
        self.cif = ReportFormatEnum.CIF in enabled
        self.html = ReportFormatEnum.HTML in enabled
        self.tex = ReportFormatEnum.TEX in enabled
        self.pdf = ReportFormatEnum.PDF in enabled

    @property
    def project(self) -> object:
        """Project owning this report category."""
        return self._parent

    def help(self) -> None:
        """Print available report methods."""
        render_object_help(self)

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
                Report._fmt_row('a', structure.cell.length_a),
                Report._fmt_row('b', structure.cell.length_a),
                Report._fmt_row('c', structure.cell.length_a),
                Report._fmt_row('α', structure.cell.angle_alpha),  # noqa: RUF001
                Report._fmt_row('β', structure.cell.angle_beta),
                Report._fmt_row('γ', structure.cell.angle_gamma),  # noqa: RUF001
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
            console.print(f'{expt.calculator.type}')

            if 'instrument' in expt._public_attrs():
                if 'setup_wavelength' in expt.instrument._public_attrs():
                    console.paragraph('Wavelength')
                    console.print(f'{expt.instrument.setup_wavelength.value:.5f}')
                if 'calib_twotheta_offset' in expt.instrument._public_attrs():
                    console.paragraph('2θ offset')
                    console.print(f'{expt.instrument.calib_twotheta_offset.value:.5f}')

            if 'peak' in expt._public_attrs():
                console.paragraph('Profile type')
                console.print(expt.peak.type)

            if 'peak' in expt._public_attrs():
                if 'broad_gauss_u' in expt.peak._public_attrs():
                    console.paragraph('Peak broadening (Gaussian)')
                    columns_headers = ['Parameter', 'Value', 'Uncertainty']
                    columns_alignment = ['left', 'right', 'right']
                    columns_data = [
                        Report._fmt_row('U', expt.peak.broad_gauss_u),
                        Report._fmt_row('V', expt.peak.broad_gauss_v),
                        Report._fmt_row('W', expt.peak.broad_gauss_w),
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
                        Report._fmt_row('X', expt.peak.broad_lorentz_x),
                        Report._fmt_row('Y', expt.peak.broad_lorentz_y),
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
                        Report._fmt_row('p1', expt.peak.asym_empir_1),
                        Report._fmt_row('p2', expt.peak.asym_empir_2),
                        Report._fmt_row('p3', expt.peak.asym_empir_3),
                        Report._fmt_row('p4', expt.peak.asym_empir_4),
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
        console.print(self.project.analysis.minimizer.type)

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

    def save(self, *, check: bool = False) -> pathlib.Path:
        """
        Write the IUCr submission report.

        Parameters
        ----------
        check : bool, default=False
            Whether to validate the written report.

        Returns
        -------
        pathlib.Path
            Path of the written report CIF.
        """
        report_path = write_iucr_cif(self.project)
        if check:
            self.check(path=report_path)
        return report_path

    def check(self, path: str | pathlib.Path | None = None) -> ReportCheckResult:
        """
        Validate the IUCr submission report.

        Parameters
        ----------
        path : str | pathlib.Path | None, default=None
            Report path. Defaults to ``reports/<project>.cif``.

        Returns
        -------
        ReportCheckResult
            Validation result with errors and warnings.
        """
        report_path = iucr_report_path(self.project, path)
        result = check_report(report_path)
        for warning in result.warnings:
            log.warning(warning)
        if result.errors:
            log.error('\n'.join(result.errors), exc_type=ValueError)
        return result
