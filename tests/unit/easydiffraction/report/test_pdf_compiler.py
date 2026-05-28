# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import subprocess


def test_compile_pdf_runs_from_tex_dir_with_absolute_output(tmp_path, monkeypatch):
    from easydiffraction.report import pdf_compiler

    reports_dir = tmp_path / 'reports'
    tex_dir = reports_dir / 'tex'
    tex_dir.mkdir(parents=True)
    tex_path = tex_dir / 'report.tex'
    pdf_path = reports_dir / 'report.pdf'
    tex_path.write_text(r'\documentclass{article}', encoding='utf-8')
    calls = []

    def fake_run(
        command,
        *,
        cwd,
        env,
        text,
        capture_output,
        check,
    ):
        calls.append(
            {
                'command': command,
                'cwd': cwd,
                'env': env,
                'text': text,
                'capture_output': capture_output,
                'check': check,
            },
        )
        pdf_path.write_text('%PDF', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0, '', '')

    monkeypatch.setattr(pdf_compiler.subprocess, 'run', fake_run)

    assert pdf_compiler._compile_pdf(('tectonic', 'tectonic'), tex_path, pdf_path) is None

    assert calls[0]['command'] == [
        'tectonic',
        '--outdir',
        str(reports_dir.resolve()),
        'report.tex',
    ]
    assert calls[0]['cwd'] == tex_dir.resolve()


def test_compile_pdf_report_skips_tectonic_runtime_failure(tmp_path, monkeypatch):
    from easydiffraction.report import pdf_compiler

    reports_dir = tmp_path / 'reports'
    tex_dir = reports_dir / 'tex'
    tex_dir.mkdir(parents=True)
    tex_path = tex_dir / 'report.tex'
    pdf_path = reports_dir / 'report.pdf'
    tex_path.write_text(r'\documentclass{article}', encoding='utf-8')
    pdf_path.write_text('%PDF stale', encoding='utf-8')
    warnings = []

    def fake_run(
        command,
        *,
        cwd,
        env,
        text,
        capture_output,
        check,
    ):
        del cwd, env, text, capture_output, check
        return subprocess.CompletedProcess(
            command,
            101,
            '',
            'panicked at Attempted to create a NULL object',
        )

    monkeypatch.setattr(pdf_compiler, '_find_engines', lambda: [('tectonic', 'tectonic')])
    monkeypatch.setattr(pdf_compiler.subprocess, 'run', fake_run)
    monkeypatch.setattr(pdf_compiler.log, 'warning', warnings.append)

    assert pdf_compiler.compile_pdf_report(tex_path) == pdf_path
    assert not pdf_path.exists()
    assert warnings
    assert warnings[0].startswith('PDF skipped:')


def test_compile_pdf_report_uses_fallback_after_runtime_failure(tmp_path, monkeypatch):
    from easydiffraction.report import pdf_compiler

    reports_dir = tmp_path / 'reports'
    tex_dir = reports_dir / 'tex'
    tex_dir.mkdir(parents=True)
    tex_path = tex_dir / 'report.tex'
    pdf_path = reports_dir / 'report.pdf'
    tex_path.write_text(r'\documentclass{article}', encoding='utf-8')

    def fake_run(
        command,
        *,
        cwd,
        env,
        text,
        capture_output,
        check,
    ):
        del cwd, env, text, capture_output, check
        if command[0] == 'tectonic':
            return subprocess.CompletedProcess(
                command,
                101,
                '',
                'event loop thread panicked',
            )
        pdf_path.write_text('%PDF', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0, '', '')

    def fail_warning(message):
        raise AssertionError(message)

    monkeypatch.setattr(
        pdf_compiler,
        '_find_engines',
        lambda: [('tectonic', 'tectonic'), ('pdflatex', 'pdflatex')],
    )
    monkeypatch.setattr(pdf_compiler.subprocess, 'run', fake_run)
    monkeypatch.setattr(pdf_compiler.log, 'warning', fail_warning)

    assert pdf_compiler.compile_pdf_report(tex_path) == pdf_path
    assert pdf_path.is_file()
