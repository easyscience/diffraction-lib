# 112. Suppress the Redundant Row-Index Column in Tables

**Priority:** `[priority] low`

**Type:** Display / UX

`TableRenderer._prepare_dataframe` bumps the DataFrame index to 1-based,
and both the Rich and pandas backends always render it as the first
column. For tables that already carry an explicit identifier — e.g.
`list_tutorials`, whose `id` column duplicates that 1-based counter —
the leading index column is redundant and reads as a duplicate.

**Fix:** add an opt-out (e.g. a `show_index` flag on the render path) so
callers with their own id column can hide the auto-generated index, or
only render the index column when no explicit id column is present.

**Depends on:** nothing.
