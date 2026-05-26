---
icon: material/clipboard-text
---

# :material-clipboard-text: Report

The **Report** section represents the final step in the data processing
workflow. It involves generating a **report** that consolidates
the results of the diffraction data analysis, providing a comprehensive
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

## Saving a Submission Report

Regular project saves do not write a report file. To write an IUCr
journal-submission CIF, use:

```python
project.save(report=True)
```

The report is written to `reports/<project>.cif` inside the saved
project directory.

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
