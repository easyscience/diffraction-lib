# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project report output configuration and file export."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.io.cif.iucr_writer import write_iucr_cif
from easydiffraction.project.categories.report.factory import ReportFactory
from easydiffraction.report.data_context import build_report_data_context
from easydiffraction.report.enums import ReportFormatEnum
from easydiffraction.utils.utils import render_object_help

if TYPE_CHECKING:
    import pathlib


_NO_REPORT_FORMATS_MESSAGE = (
    'project.report.save() called with no formats enabled. '
    'Set project.report.{cif,html,tex,pdf} = True, or call a per-format '
    'method directly (project.report.save_html(), etc.).'
)


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
            tags=TagSpec(edi_names=['_report.cif']),
        )
        self._html = BoolDescriptor(
            name='html',
            description='Whether to write HTML reports when saving.',
            value_spec=AttributeSpec(default=True),
            tags=TagSpec(edi_names=['_report.html']),
        )
        self._tex = BoolDescriptor(
            name='tex',
            description='Whether to write TeX reports when saving.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(edi_names=['_report.tex']),
        )
        self._pdf = BoolDescriptor(
            name='pdf',
            description='Whether to write PDF reports when saving.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(edi_names=['_report.pdf']),
        )
        self._html_offline = BoolDescriptor(
            name='html_offline',
            description='Whether HTML reports should embed assets.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(edi_names=['_report.html_offline']),
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

        return render_html_report(self.data_context(), offline=offline, project=self.project)

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
                    report_paths.append(pdf_path)
                    self._discard_intermediate_tex_bundle(pdf_path)
                else:
                    from easydiffraction.report.pdf_compiler import (  # noqa: PLC0415
                        compile_pdf_report,
                    )

                    pdf_path = compile_pdf_report(tex_path)
                    report_paths.append(pdf_path)
        return report_paths

    def _discard_intermediate_tex_bundle(self, pdf_path: pathlib.Path) -> None:
        """
        Remove the TeX bundle left behind by a PDF-only build.

        Compiling a PDF requires writing the ``.tex`` and ``data/``
        bundle under ``reports/tex/``. When ``tex`` output is not
        requested, that bundle is only a build intermediate, so delete
        it once the PDF exists. A failed compile (no PDF) keeps the
        bundle so it can be inspected or compiled by hand.
        """
        import shutil  # noqa: PLC0415

        from easydiffraction.report.tex_renderer import tex_report_path  # noqa: PLC0415

        if not pdf_path.exists():
            return
        tex_dir = tex_report_path(self.project).parent
        if tex_dir.is_dir():
            shutil.rmtree(tex_dir)
