# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for project report category behavior."""

from __future__ import annotations

import pytest


def test_report_has_no_formats_property(monkeypatch):
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    report = Report()

    with pytest.raises(AttributeError, match="Unknown attribute 'formats'"):
        report.formats


def test_report_save_without_outputs_points_to_boolean_flags():
    from easydiffraction.project.categories.report.default import Report

    report = Report()
    report.html = False

    with pytest.raises(ValueError, match='no formats enabled') as exc_info:
        report.save()

    message = str(exc_info.value)
    assert 'project.report.{cif,html,tex,pdf}' in message
    assert 'project.report.formats' not in message


def test_report_html_enabled_by_default():
    from easydiffraction.project.categories.report.default import Report

    report = Report()
    assert report.html.value is True
    assert report.cif.value is False
    assert report.tex.value is False
    assert report.pdf.value is False


def test_save_configured_reuses_tex_bundle_for_pdf(tmp_path, monkeypatch):
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.report import pdf_compiler

    tex_path = tmp_path / 'reports' / 'tex' / 'demo.tex'
    pdf_path = tmp_path / 'reports' / 'demo.pdf'
    calls = []
    report = Report()
    report.html = False
    report.tex = True
    report.pdf = True

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


def test_save_configured_returns_intended_missing_pdf(tmp_path, monkeypatch):
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.report import pdf_compiler

    tex_path = tmp_path / 'reports' / 'tex' / 'demo.tex'
    pdf_path = tmp_path / 'reports' / 'demo.pdf'
    report = Report()
    report.html = False
    report.tex = True
    report.pdf = True

    def fake_save_tex(self):
        del self
        return tex_path

    def fake_compile_pdf_report(path):
        assert path == tex_path
        return pdf_path

    monkeypatch.setattr(Report, 'save_tex', fake_save_tex)
    monkeypatch.setattr(pdf_compiler, 'compile_pdf_report', fake_compile_pdf_report)

    assert report._save_configured() == [tex_path, pdf_path]
