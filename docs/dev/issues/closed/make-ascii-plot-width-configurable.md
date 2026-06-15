# 56. Make ASCII Plot Width Configurable

Closed: the hardcoded `width = 60` and its TODO were removed. ASCII plot
width is now derived from the terminal via `_chart_point_count()`
(`display/plotters/ascii.py:46`, used at `:289`), clamped to a minimum
point count.
