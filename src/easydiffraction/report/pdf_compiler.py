# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Compile LaTeX report bundles into PDF reports."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

from easydiffraction.report.tex_renderer import save_tex_report
from easydiffraction.utils.logging import log

_ENGINE_ORDER = ('tectonic', 'latexmk', 'pdflatex')
_INSTALL_HINT = """PDF skipped: no TeX engine on PATH.
Install one with:
  pixi add tectonic
  conda install -c conda-forge tectonic
  # or any TeX Live distribution (latexmk / pdflatex)
Then re-run project.save() with 'pdf' in project.report.formats or
project.report.save_pdf()."""


def save_pdf_report(
    project: object,
    context: dict[str, object],
    *,
    style: str = 'iucr',
) -> pathlib.Path:
    """
    Write a TeX bundle and compile it to PDF when possible.

    Parameters
    ----------
    project : object
        Project instance.
    context : dict[str, object]
        Data returned by ``Report.data_context()``.
    style : str, default='iucr'
        Report template style.

    Returns
    -------
    pathlib.Path
        Path of the PDF report, or the intended PDF path when no TeX
        engine is available.

    Raises
    ------
    RuntimeError
        If a discovered TeX engine fails to compile the report.
    """
    tex_path = save_tex_report(project, context, style=style)
    pdf_path = tex_path.parent.parent / f'{tex_path.stem}.pdf'
    engine = _find_engine()
    if engine is None:
        log.warning(_INSTALL_HINT)
        return pdf_path

    _compile_pdf(engine, tex_path, pdf_path)
    return pdf_path


def _find_engine() -> tuple[str, str] | None:
    """Return the first available TeX engine."""
    for engine_name in _ENGINE_ORDER:
        executable = shutil.which(engine_name)
        if executable is not None:
            return engine_name, executable
    return None


def _compile_pdf(
    engine: tuple[str, str],
    tex_path: pathlib.Path,
    pdf_path: pathlib.Path,
) -> None:
    """Compile one TeX document with a discovered engine."""
    engine_name, executable = engine
    command = _compile_command(engine_name, executable, tex_path, pdf_path.parent)
    result = subprocess.run(
        command,
        cwd=tex_path.parent,
        env=_compile_environment(tex_path),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        msg = _compiler_error_message(engine_name, tex_path, result)
        raise RuntimeError(msg)
    if not pdf_path.is_file():
        msg = (
            f"TeX engine '{engine_name}' completed but did not write "
            f"'{pdf_path}'."
        )
        raise RuntimeError(msg)


def _compile_command(
    engine_name: str,
    executable: str,
    tex_path: pathlib.Path,
    pdf_dir: pathlib.Path,
) -> list[str]:
    """Return the compile command for one engine."""
    if engine_name == 'tectonic':
        return [executable, '--outdir', str(pdf_dir), tex_path.name]
    if engine_name == 'latexmk':
        return [
            executable,
            '-pdf',
            '-interaction=nonstopmode',
            '-halt-on-error',
            f'-outdir={pdf_dir}',
            tex_path.name,
        ]
    return [
        executable,
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-output-directory',
        str(pdf_dir),
        tex_path.name,
    ]


def _compile_environment(tex_path: pathlib.Path) -> dict[str, str]:
    """Return a TeX subprocess environment with vendored styles."""
    environment = os.environ.copy()
    styles_dir = tex_path.parent / 'styles'
    texinputs = environment.get('TEXINPUTS', '')
    environment['TEXINPUTS'] = f'{styles_dir}{os.pathsep}{texinputs}'
    return environment


def _compiler_error_message(
    engine_name: str,
    tex_path: pathlib.Path,
    result: subprocess.CompletedProcess[str],
) -> str:
    """Return a concise compiler failure message."""
    details = (result.stderr or result.stdout).strip()
    if len(details) > 4000:
        details = details[-4000:]
    return (
        f"TeX engine '{engine_name}' failed while compiling '{tex_path}'.\n"
        f'{details}'
    )
