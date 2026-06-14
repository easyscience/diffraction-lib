---
title: Report
icon: material/clipboard-text
---

# :material-clipboard-text: Report

The **Report** section represents the final step in the data processing
workflow. It involves generating a **report** that consolidates the
results of the diffraction data analysis, providing a comprehensive
overview of the model refinement process and its outcomes.

## Contents of the Report

The report includes key details such as:

- Final refined model parameters – Optimized crystallographic and
  instrumental parameters.
- Goodness-of-fit indicators – Metrics such as R-factors, chi-square
  (χ²), and residuals.
- Graphical representation – Visualization of experimental vs.
  calculated diffraction patterns.

## Saving the Report

Reports are written to disk rather than printed. Call a per-format
method directly, or enable formats on `project.report` (see below) so
the next `project.save()` writes them:

```python
# Write an HTML report immediately
project.report.save_html()
```

## Configuring Saved Reports

Report output is controlled by `project.report`, a project-level
configuration category that is saved in `project.edifa`. Regular
`project.save()` calls read this configuration and write the selected
report formats.

| Setting                       | Type   | Meaning                                            |
| ----------------------------- | ------ | -------------------------------------------------- |
| `project.report.cif`          | `bool` | Write an IUCr submission CIF.                      |
| `project.report.html`         | `bool` | Write an HTML report (enabled by default).         |
| `project.report.tex`          | `bool` | Write a TeX report bundle.                         |
| `project.report.pdf`          | `bool` | Write a PDF report when a TeX engine is available. |
| `project.report.html_offline` | `bool` | Embed HTML assets instead of using CDN links.      |

HTML output is enabled by default, so saving a project always writes an
HTML report unless you set `project.report.html = False`. Enable
additional formats through their boolean flags:

```python
project.report.cif = True
project.save()
```

This writes `reports/<project>.html` (enabled by default) and
`reports/<project>.cif` inside the project directory.

When `pdf` is enabled but `tex` is not, the intermediate `reports/tex/`
bundle is written only to build the PDF and removed once the PDF is
produced. It is kept if no TeX engine is available so you can compile it
by hand.

## One-Off Report Saves

Per-format methods write a report without changing the saved
configuration:

```python
project.report.save_html()
project.report.save_cif()
project.report.save_tex()
project.report.save_pdf()
```

`save_pdf()` always writes the TeX bundle first. If no TeX engine is on
`PATH`, EasyDiffraction leaves the `.tex` and `data/` files under
`reports/tex/`, prints a short install hint, and does not raise.

HTML reports load Plotly and MathJax from CDNs by default. Set
`project.report.html_offline = True` to make the HTML report usable
without network access; this embeds Plotly in the HTML and copies the
vendored MathJax bundle next to it, adding about 4.5 MB total.

The command line saves reports from the persisted project configuration
when a fit writes the project back to disk:

```bash
python -m easydiffraction path/to/project fit
```

If `project.edifa` contains `_report.html true`, `_report.tex true`, or
another enabled report flag, `fit` writes those reports as part of the
normal project save. Use the Python per-format methods above for one-off
exports without changing the saved configuration.

<!--
## Exporting the Report

EasyDiffraction allows exporting the report in various formats for
further analysis and documentation:

- Human-readable text format (.txt)
- CIF format (.cif) for integration with crystallographic databases
- PDF format (.pdf) for easy sharing and publication
-->

---

Now that the initial user guide is complete, you can explore the
[EasyDiffraction API](../../api-reference/index.md) for detailed
information on the available classes and methods. Additionally, you can
find practical examples and step-by-step guides in the
[Tutorials](../../tutorials/index.md).
