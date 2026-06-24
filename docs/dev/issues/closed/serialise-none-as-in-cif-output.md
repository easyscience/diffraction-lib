# 84. Serialise `None` as `.` in CIF Output

Closed: `io/cif/serialize.py` `format_value` (`:57-58`) maps
`None`/`NaN` to the CIF unknown marker `?` instead of literal `None`,
and `io/cif/parse.py` (`:58`) maps both `?` and `.` back to `None`,
preserving round-trip fidelity. The issue explicitly allowed `?` as an
acceptable encoding.
