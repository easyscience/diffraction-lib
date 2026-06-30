# 147. Don't Report a PDF Report as Written When No TeX Engine Exists

**Priority:** `[priority] medium`

**Type:** UX

`compile_pdf_report` returns the intended `pdf_path` even when
`_find_engines()` is empty (it only logs a warning). `_save_configured`
appends that path to `report_paths`, and `project.save()` prints it
under "reports/" as if the file were created — but the PDF does not
exist on disk. The scientist sees a PDF listed in the save tree that is
not there.

**Fix:** include only report paths that exist in the printed save tree,
or distinguish "skipped" from "written".

**TODOs / locations:**

- [pdf_compiler.py](../../../../src/easydiffraction/report/pdf_compiler.py#L81)
- [default.py](../../../../src/easydiffraction/project/categories/report/default.py#L274)
- [project.py](../../../../src/easydiffraction/project/project.py#L556)

**Depends on:** nothing.
