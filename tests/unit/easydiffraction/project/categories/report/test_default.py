# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for project report category behavior."""

from __future__ import annotations


def test_save_configured_reuses_tex_bundle_for_pdf(tmp_path, monkeypatch):
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.report import pdf_compiler

    tex_path = tmp_path / 'reports' / 'tex' / 'demo.tex'
    pdf_path = tmp_path / 'reports' / 'demo.pdf'
    calls = []
    report = Report()
    report.formats = ['tex', 'pdf']

    def fake_save_tex(self):
        del self
        calls.append('tex')
        return tex_path

    def fake_save_pdf(self):
        del self
        msg = 'save_pdf should not regenerate TeX when tex was already saved.'
        raise AssertionError(msg)

    def fake_compile_pdf_report(path):
        calls.append(('pdf', path))
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_text('%PDF', encoding='utf-8')
        return pdf_path

    monkeypatch.setattr(Report, 'save_tex', fake_save_tex)
    monkeypatch.setattr(Report, 'save_pdf', fake_save_pdf)
    monkeypatch.setattr(pdf_compiler, 'compile_pdf_report', fake_compile_pdf_report)

    assert report._save_configured() == [tex_path, pdf_path]
    assert calls == ['tex', ('pdf', tex_path)]


def test_save_configured_omits_missing_compiled_pdf(tmp_path, monkeypatch):
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.report import pdf_compiler

    tex_path = tmp_path / 'reports' / 'tex' / 'demo.tex'
    pdf_path = tmp_path / 'reports' / 'demo.pdf'
    report = Report()
    report.formats = ['tex', 'pdf']

    def fake_save_tex(self):
        del self
        return tex_path

    def fake_compile_pdf_report(path):
        assert path == tex_path
        return pdf_path

    monkeypatch.setattr(Report, 'save_tex', fake_save_tex)
    monkeypatch.setattr(pdf_compiler, 'compile_pdf_report', fake_compile_pdf_report)

    assert report._save_configured() == [tex_path]
