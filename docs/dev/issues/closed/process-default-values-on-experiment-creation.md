# 24. Process Default Values on Experiment Creation

Closed (#157): the CrysFML calculator no longer fills instrument/peak defaults with inline `... if instrument else 1.0` fallbacks at calculation time (none remain in `analysis/calculators/crysfml.py`); the experiment dict is built from clean attribute maps via `_copy_present_values`. The "process defaults on creation" TODO was removed.
