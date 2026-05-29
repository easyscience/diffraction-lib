---
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

## Viewing the Report

Users can print the report using:

```python
# Generate and print the report
project.report.show_report()
```

<!--
This command will display a structured report of the analysis results,
including model parameters, fit statistics, and data visualizations.
-->

## Configuring Saved Reports

Report output is controlled by `project.report`, a project-level
configuration category that is saved in `project.cif`. Regular
`project.save()` calls read this configuration and write the selected
report formats.

| Setting | Type | Meaning |
| --- | --- | --- |
| `project.report.cif` | `bool` | Write an IUCr submission CIF. |
| `project.report.html` | `bool` | Write an HTML report. |
| `project.report.tex` | `bool` | Write a TeX report bundle. |
| `project.report.pdf` | `bool` | Write a PDF report when a TeX engine is available. |
| `project.report.html_offline` | `bool` | Embed HTML assets instead of using CDN links. |

The `formats` property is a compact way to set the four format flags:

```python
project.report.formats = ['html', 'cif']
project.save()
```

This writes `reports/<project>.html` and `reports/<project>.cif` inside
the project directory.

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

The command line mirrors the same split:

```bash
ed save path/to/project
ed save-report path/to/project --html --tex --pdf
```

`ed save` uses the persisted `project.report` configuration.
`ed save-report` is for one-off exports and requires at least one of
`--cif`, `--html`, `--tex`, or `--pdf`.

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
