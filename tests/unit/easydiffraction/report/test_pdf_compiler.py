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

    pdf_compiler._compile_pdf(('tectonic', 'tectonic'), tex_path, pdf_path)

    assert calls[0]['command'] == [
        'tectonic',
        '--outdir',
        str(reports_dir.resolve()),
        'report.tex',
    ]
    assert calls[0]['cwd'] == tex_dir.resolve()
