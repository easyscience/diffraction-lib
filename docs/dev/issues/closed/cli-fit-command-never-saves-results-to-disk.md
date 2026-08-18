# 137. CLI `fit` Command Never Saves Results to Disk

Closed after fixing the CLI persistence boundary. `Analysis.fit()`
updates fit state without saving the project. The CLI `fit` command now
calls `project.save()` explicitly after a successful non-`--dry` fit, so
updated results still persist. With `--dry`, the project path is cleared
for the fit and the explicit save is skipped, preventing project files
and fit sidecars from being overwritten.
