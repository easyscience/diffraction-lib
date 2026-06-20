# 174. Bulk Write-Back of Calculated Intensity During Fits

**Priority:** `[priority] medium`

**Type:** Performance

After the Wyckoff (issue 172) and included-point-mask (issue 173)
caches, profiling of a minimizer iteration shows the remaining cost is
the per-point data model. One large piece is writing the calculator
result back into the data: `_set_intensity_calc` (and `_set_intensity_bkg`)
loop over the included points and assign through each point's guarded
`NumericDescriptor` (`p.intensity_calc._value = v`), so every iteration
pays hundreds of thousands of guarded `__setattr__` / `value` calls
(`core/guard.py:__setattr__` and `core/variable.py:value` dominate the
post-cache profile).

The calculated intensity is a derived per-iteration array; it does not
need per-point validation on the hot path.

**Fix:** provide a bulk write path for the calculated arrays
(`intensity_calc`, `intensity_bkg`) that assigns the numpy array once
(or writes `_value` in a tight loop bypassing guard machinery) instead
of going through the guarded descriptor per point. Keep the public
read API (`data.intensity_calc`) unchanged.

**TODOs / locations:**

- `PdDataBase._set_intensity_calc` / `_set_intensity_bkg`
  (`src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`).
- Ensure the bulk path preserves restored/serialized state and the
  excluded-point handling (only included points are written).
- Add a test that bulk write matches the current per-point write.

**Depends on:** nothing; localized to the powder data category.

**Recommended-priority note:** Marked **medium** — a clear per-iteration
fit win on top of issues 172/173, but smaller than those and touching
the data hot path, so it needs care.
