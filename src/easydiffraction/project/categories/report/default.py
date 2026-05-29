# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project report display facade."""

from __future__ import annotations

from textwrap import wrap
from typing import TYPE_CHECKING

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.iucr_writer import write_iucr_cif
from easydiffraction.project.categories.report.factory import ReportFactory
from easydiffraction.report.data_context import build_report_data_context
from easydiffraction.report.enums import ReportFormatEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_object_help
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    import pathlib

    from easydiffraction.core.variable import Parameter


_NO_REPORT_FORMATS_MESSAGE = (
    'project.report.save() called with no formats enabled. '
    'Set project.report.{cif,html,tex,pdf} = True, or call a per-format '
    'method directly (project.report.save_html(), etc.).'
)


class _ReportDisplayMixin:
    """Console display methods for report categories."""

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

            columns_headers = ['Parameter', 'Value', 'Uncertainty', 'Unit']
            columns_alignment = ['left', 'right', 'right', 'left']
            columns_data = [
                self._fmt_row('a', structure.cell.length_a),
                self._fmt_row('b', structure.cell.length_b),
                self._fmt_row('c', structure.cell.length_c),
                self._fmt_row('α', structure.cell.angle_alpha),  # noqa: RUF001
                self._fmt_row('β', structure.cell.angle_beta),
                self._fmt_row('γ', structure.cell.angle_gamma),  # noqa: RUF001
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
                f'{expt.type.beam_mode.value}, '
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
                    columns_headers = ['Parameter', 'Value', 'Uncertainty', 'Unit']
                    columns_alignment = ['left', 'right', 'right', 'left']
                    columns_data = [
                        self._fmt_row('U', expt.peak.broad_gauss_u),
                        self._fmt_row('V', expt.peak.broad_gauss_v),
                        self._fmt_row('W', expt.peak.broad_gauss_w),
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
                    columns_headers = ['Parameter', 'Value', 'Uncertainty', 'Unit']
                    columns_alignment = ['left', 'right', 'right', 'left']
                    columns_data = [
                        self._fmt_row('X', expt.peak.broad_lorentz_x),
                        self._fmt_row('Y', expt.peak.broad_lorentz_y),
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )
                if 'asym_empir_1' in expt.peak._public_attrs():
                    console.paragraph('Asymmetry (Empirical)')
                    columns_headers = ['Parameter', 'Value', 'Uncertainty', 'Unit']
                    columns_alignment = ['left', 'right', 'right', 'left']
                    columns_data = [
                        self._fmt_row('p1', expt.peak.asym_empir_1),
                        self._fmt_row('p2', expt.peak.asym_empir_2),
                        self._fmt_row('p3', expt.peak.asym_empir_3),
                        self._fmt_row('p4', expt.peak.asym_empir_4),
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


@ReportFactory.register
class Report(_ReportDisplayMixin, CategoryItem):
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
    def html_offline(self) -> BoolDescriptor:
        """Whether HTML reports should embed assets."""
        return self._html_offline

    @html_offline.setter
    def html_offline(self, value: bool) -> None:
        self._html_offline.value = value

    def _enabled_formats(self) -> list[ReportFormatEnum]:
        """Return report-output formats enabled by boolean flags."""
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

    @property
    def project(self) -> object:
        """Project owning this report category."""
        return self._parent

    def data_context(self) -> dict[str, object]:
        """Return shared report-rendering data."""
        return build_report_data_context(self.project)

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
        units = parameter.resolve_display_units('gui')
        return [pretty_name, value, uncertainty, units]

    def save_cif(self) -> pathlib.Path:
        """
        Write the IUCr submission report.

        Returns
        -------
        pathlib.Path
            Path of the written report CIF.
        """
        return write_iucr_cif(self.project)

    def save_html(self, *, offline: bool = False) -> pathlib.Path:
        """
        Write the HTML report.

        Parameters
        ----------
        offline : bool, default=False
            Whether to embed assets in the HTML report.

        Returns
        -------
        pathlib.Path
            Path of the written HTML report.
        """
        from easydiffraction.report.html_renderer import save_html_report  # noqa: PLC0415

        return save_html_report(self.project, self.data_context(), offline=offline)

    def as_html(self, *, offline: bool = False) -> str:
        """
        Render the HTML report.

        Parameters
        ----------
        offline : bool, default=False
            Whether to embed HTML JavaScript assets.

        Returns
        -------
        str
            Complete HTML report document.
        """
        from easydiffraction.report.html_renderer import render_html_report  # noqa: PLC0415

        return render_html_report(self.data_context(), offline=offline)

    def save_tex(self) -> pathlib.Path:
        """
        Write the TeX report.

        Returns
        -------
        pathlib.Path
            Path of the written TeX report.
        """
        from easydiffraction.report.tex_renderer import save_tex_report  # noqa: PLC0415

        return save_tex_report(self.project, self.data_context())

    def as_tex(self) -> str:
        """
        Render the TeX report.

        Returns
        -------
        str
            Complete TeX report document.
        """
        from easydiffraction.report.tex_renderer import render_tex_report  # noqa: PLC0415

        return render_tex_report(self.data_context())

    def save_pdf(self) -> pathlib.Path:
        """
        Write the PDF report.

        Returns
        -------
        pathlib.Path
            Path of the PDF report, or the intended PDF path when no TeX
            engine is available.
        """
        from easydiffraction.report.pdf_compiler import save_pdf_report  # noqa: PLC0415

        return save_pdf_report(self.project, self.data_context())

    def save(self) -> list[pathlib.Path]:
        """
        Write all configured report formats.

        Returns
        -------
        list[pathlib.Path]
            Paths of written report files.

        Raises
        ------
        ValueError
            If no report formats are configured. ``project.save()`` is
            the no-op-on-empty entry point.
        """
        report_paths = self._save_configured()
        if not report_paths:
            raise ValueError(_NO_REPORT_FORMATS_MESSAGE)
        return report_paths

    def _save_configured(self) -> list[pathlib.Path]:
        """
        Write enabled formats, returning quietly when none are set.
        """
        report_paths = []
        tex_path = None
        for report_format in self._enabled_formats():
            if report_format is ReportFormatEnum.CIF:
                report_paths.append(self.save_cif())
            elif report_format is ReportFormatEnum.HTML:
                report_paths.append(self.save_html(offline=bool(self.html_offline.value)))
            elif report_format is ReportFormatEnum.TEX:
                tex_path = self.save_tex()
                report_paths.append(tex_path)
            elif report_format is ReportFormatEnum.PDF:
                if tex_path is None:
                    pdf_path = self.save_pdf()
                else:
                    from easydiffraction.report.pdf_compiler import (  # noqa: PLC0415
                        compile_pdf_report,
                    )

                    pdf_path = compile_pdf_report(tex_path)
                report_paths.append(pdf_path)
        return report_paths
