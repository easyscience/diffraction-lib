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
_ENGINE_RUNTIME_FAILURE_MARKERS = (
    'panicked at',
    'event loop thread panicked',
    'Attempted to create a NULL object',
)
_INSTALL_HINT = """PDF skipped: no TeX engine on PATH.
Install one with:
  pixi add tectonic
  conda install -c conda-forge tectonic
  # or any TeX Live distribution (latexmk / pdflatex)
Then re-run project.save() with 'pdf' in project.report.formats or
project.report.save_pdf().
The .tex and data/ bundle remains under reports/tex/."""


def save_pdf_report(
    project: object,
    context: dict[str, object],
) -> pathlib.Path:
    """
    Write a TeX bundle and compile it to PDF when possible.

    Parameters
    ----------
    project : object
        Project instance.
    context : dict[str, object]
        Data returned by ``Report.data_context()``.

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
    tex_path = save_tex_report(project, context)
    return compile_pdf_report(tex_path)


def compile_pdf_report(tex_path: pathlib.Path) -> pathlib.Path:
    """
    Compile an existing TeX report bundle into a PDF report.

    Parameters
    ----------
    tex_path : pathlib.Path
        Path of the written main TeX document.

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
    pdf_path = tex_path.parent.parent / f'{tex_path.stem}.pdf'
    pdf_path.unlink(missing_ok=True)
    engines = _find_engines()
    if not engines:
        log.warning(_INSTALL_HINT)
        return pdf_path

    runtime_failures = []
    for engine in engines:
        runtime_failure = _compile_report_bundle(engine, tex_path, pdf_path)
        if runtime_failure is None:
            return pdf_path
        runtime_failures.append(runtime_failure)
    if runtime_failures:
        _warn_engine_runtime_failure(runtime_failures)
    return pdf_path


def _find_engines() -> list[tuple[str, str]]:
    """Return available TeX engines in preferred order."""
    engines = []
    for engine_name in _ENGINE_ORDER:
        executable = shutil.which(engine_name)
        if executable is not None:
            engines.append((engine_name, executable))
    return engines


def _find_engine() -> tuple[str, str] | None:
    """Return the first available TeX engine."""
    engines = _find_engines()
    if not engines:
        return None
    return engines[0]


def _compile_report_bundle(
    engine: tuple[str, str],
    tex_path: pathlib.Path,
    pdf_path: pathlib.Path,
) -> str | None:
    """Compile figure documents first, then the main report."""
    for figure_tex_path in _figure_tex_paths(tex_path):
        runtime_failure = _compile_pdf(
            engine,
            figure_tex_path,
            figure_tex_path.with_suffix('.pdf'),
        )
        if runtime_failure is not None:
            return runtime_failure
    return _compile_pdf(engine, tex_path, pdf_path)


def _figure_tex_paths(tex_path: pathlib.Path) -> list[pathlib.Path]:
    """Return standalone figure TeX files for a report bundle."""
    data_dir = tex_path.parent / 'data'
    if not data_dir.is_dir():
        return []
    return sorted(data_dir.glob('*.tex'))


def _is_engine_runtime_failure(
    engine_name: str,
    result: subprocess.CompletedProcess[str],
) -> bool:
    """Return whether the TeX engine failed before compilation."""
    if engine_name != 'tectonic':
        return False
    output = f'{result.stderr}\n{result.stdout}'
    return any(marker in output for marker in _ENGINE_RUNTIME_FAILURE_MARKERS)


def _compile_pdf(
    engine: tuple[str, str],
    tex_path: pathlib.Path,
    pdf_path: pathlib.Path,
) -> str | None:
    """Compile one TeX document with a discovered engine."""
    engine_name, executable = engine
    compile_tex_path = tex_path.resolve()
    compile_pdf_path = pdf_path.resolve()
    compile_pdf_path.unlink(missing_ok=True)
    command = _compile_command(
        engine_name,
        executable,
        compile_tex_path,
        compile_pdf_path.parent,
    )
    result = subprocess.run(
        command,
        cwd=compile_tex_path.parent,
        env=_compile_environment(compile_tex_path),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if _is_engine_runtime_failure(engine_name, result):
            return _compiler_error_message(engine_name, tex_path, result)
        msg = _compiler_error_message(engine_name, tex_path, result)
        raise RuntimeError(msg)
    if not compile_pdf_path.is_file():
        msg = (
            f"TeX engine '{engine_name}' completed but did not write "
            f"'{pdf_path}'."
        )
        raise RuntimeError(msg)
    return None


def _warn_engine_runtime_failure(
    failures: list[str],
) -> None:
    """Warn when a TeX engine crashes before compiling LaTeX."""
    details = '\n\n'.join(failures)
    msg = (
        'PDF skipped: the TeX engine failed before LaTeX compilation. '
        'The .tex and data/ bundle remains under reports/tex/.\n'
        f'{details}'
    )
    log.warning(msg)


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
    """Return a TeX subprocess environment."""
    del tex_path
    return os.environ.copy()


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
