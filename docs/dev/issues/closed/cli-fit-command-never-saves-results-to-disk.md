# 137. CLI `fit` Command Never Saves Results to Disk

Closed on re-verification — **not a defect**. `Analysis.fit()` auto-saves via `self.project.save()` in `_run_single` / `_run_joint` / `_run_sequential` (`analysis.py:2661,2688,2727`) whenever the project path is set. The CLI `fit` command's non-`--dry` path leaves `project.info.path` set, so results persist; `--dry` nulls the path to suppress saving (asserted by `test_cli_fit_dry_clears_path`). The original audit finding read the CLI in isolation and missed `fit()`'s internal save; no code change is needed.
