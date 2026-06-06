# %% [markdown]
# # Cross-engine verification — neutron powder, constant wavelength (Bragg)
#
# This page calculates the **same** diffraction pattern for one structure
# and one experiment with each supported engine, **without any fitting**,
# and reports how closely the engines agree. It doubles as a regression
# check run by `pixi run script-tests`.

# %%
import numpy as np

import easydiffraction as ed
from easydiffraction.analysis.calculators.support import calculator_support_matrix
from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs

# %% [markdown]
# ## Build the project (La0.5Ba0.5CoO3, HRPT)

# %%
project = ed.Project()
project.structures.add_from_cif_path(ed.download_data(id=1, destination='data'))
project.experiments.add_from_cif_path(ed.download_data(id=2, destination='data'))

experiment = project.experiments['hrpt']

# %% [markdown]
# ## Engines to compare
#
# The calculator support matrix declares which engines can compute this
# instrument condition (`cwl-pd`).

# %%
by_tag = {entry.instrument_tag: entry for entry in calculator_support_matrix()}
declared = sorted(c.value for c in by_tag['cwl-pd'].calculators)
print('Engines declared for cwl-pd:', declared)

ENGINES = ['cryspy', 'crysfml']

# %% [markdown]
# ## Calculate the pattern with each engine (no fitting)

# %%
y_calc_by_engine = {}
for engine in ENGINES:
    experiment.calculator.type = engine
    assert experiment.calculator.type == engine
    _, y_calc, _ = get_reliability_inputs(project.structures, [experiment])
    y_calc_by_engine[engine] = np.asarray(y_calc, dtype=float)
    # Per-engine measured-vs-calculated view (rendered in the docs build).
    project.display.pattern(expt_name='hrpt')

# %% [markdown]
# ## Closeness metrics between engines

# %%
a = y_calc_by_engine['cryspy']
b = y_calc_by_engine['crysfml']

assert a.shape == b.shape, 'engines returned patterns of different length'
assert np.all(np.isfinite(a)) and np.all(np.isfinite(b))

rms = float(np.sqrt(np.mean((a - b) ** 2)))
norm = float(np.sqrt(np.mean(a**2)))
profile_diff_pct = 100.0 * rms / norm if norm else float('nan')
max_deviation = float(np.max(np.abs(a - b)))
intensity_ratio = float(a.sum() / b.sum()) if b.sum() else float('nan')
correlation = float(np.corrcoef(a, b)[0, 1])

print(f'profile difference:                 {profile_diff_pct:.2f} %')
print(f'max point-wise deviation:           {max_deviation:.4g}')
print(f'integrated-intensity ratio (cp/cf): {intensity_ratio:.4f}')
print(f'Pearson correlation:                {correlation:.4f}')

# %% [markdown]
# ## Overlay
#
# Both engines on one chart, in distinct colours and line styles.

# %%
import plotly.graph_objects as go

x = np.arange(a.size)
fig = go.Figure()
fig.add_scatter(x=x, y=a, mode='lines', name='cryspy', line={'color': 'royalblue'})
fig.add_scatter(
    x=x, y=b, mode='lines', name='crysfml', line={'color': 'crimson', 'dash': 'dot'}
)
fig.update_layout(
    title='Calculated patterns: cryspy vs crysfml',
    xaxis_title='point index',
    yaxis_title='Icalc',
)
# Bare expression renders inline in the executed notebook; a no-op as a
# plain script, so `pixi run script-tests` stays headless-safe.
fig

# %% [markdown]
# ## Regression assertions
#
# Both engines compute the same physics for the same structure, so their
# calculated patterns share peak positions and are highly correlated. The
# tolerance is intentionally loose for now and tightened as the
# verification suite matures.

# %%
assert correlation > 0.8, f'cross-engine correlation unexpectedly low: {correlation:.4f}'
