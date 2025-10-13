# Package Structure (short)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 calculator_base.py
│   │   ├── 📄 calculator_crysfml.py
│   │   ├── 📄 calculator_cryspy.py
│   │   ├── 📄 calculator_factory.py
│   │   └── 📄 calculator_pdffit.py
│   ├── 📁 category_collections
│   │   ├── 📄 __init__.py
│   │   ├── 📄 aliases.py
│   │   ├── 📄 constraints.py
│   │   └── 📄 joint_fit_experiments.py
│   ├── 📁 fitting
│   │   ├── 📄 __init__.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 progress_tracker.py
│   │   └── 📄 results.py
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 minimizer_base.py
│   │   ├── 📄 minimizer_dfols.py
│   │   ├── 📄 minimizer_factory.py
│   │   └── 📄 minimizer_lmfit.py
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   ├── 📄 calculation.py
│   └── 📄 minimization.py
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 categories.py
│   ├── 📄 collections.py
│   ├── 📄 datablocks.py
│   ├── 📄 diagnostics.py
│   ├── 📄 guards.py
│   ├── 📄 identity.py
│   ├── 📄 parameters.py
│   ├── 📄 singletons.py
│   └── 📄 validation.py
├── 📁 crystallography
│   ├── 📄 __init__.py
│   ├── 📄 crystallography.py
│   └── 📄 space_groups.py
├── 📁 experiments
│   ├── 📁 category_collections
│   │   ├── 📁 background_types
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 chebyshev.py
│   │   │   ├── 📄 enums.py
│   │   │   └── 📄 line_segment.py
│   │   ├── 📄 __init__.py
│   │   ├── 📄 background.py
│   │   ├── 📄 excluded_regions.py
│   │   └── 📄 linked_phases.py
│   ├── 📁 category_items
│   │   ├── 📁 instrument_setups
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 cw.py
│   │   │   └── 📄 tof.py
│   │   ├── 📁 peak_profiles
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 cw.py
│   │   │   ├── 📄 cw_mixins.py
│   │   │   ├── 📄 pdf.py
│   │   │   ├── 📄 pdf_mixins.py
│   │   │   ├── 📄 tof.py
│   │   │   └── 📄 tof_mixins.py
│   │   ├── 📄 __init__.py
│   │   ├── 📄 experiment_type.py
│   │   ├── 📄 instrument.py
│   │   └── 📄 peak.py
│   ├── 📁 datastore_types
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 pd.py
│   │   └── 📄 sg.py
│   ├── 📁 experiment_types
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 enums.py
│   │   ├── 📄 instrument_mixin.py
│   │   ├── 📄 pdf.py
│   │   ├── 📄 powder.py
│   │   └── 📄 single_crystal.py
│   ├── 📄 __init__.py
│   ├── 📄 datastore.py
│   ├── 📄 experiment.py
│   └── 📄 experiments.py
├── 📁 io
│   └── 📁 cif
│       ├── 📄 handler.py
│       └── 📄 serialize.py
├── 📁 plotting
│   ├── 📁 plotters
│   │   ├── 📄 __init__.py
│   │   ├── 📄 plotter_ascii.py
│   │   ├── 📄 plotter_base.py
│   │   └── 📄 plotter_plotly.py
│   ├── 📄 __init__.py
│   └── 📄 plotting.py
├── 📁 project
│   ├── 📄 __init__.py
│   ├── 📄 project.py
│   └── 📄 project_info.py
├── 📁 sample_models
│   ├── 📁 category_collections
│   │   ├── 📄 __init__.py
│   │   └── 📄 atom_sites.py
│   ├── 📁 category_items
│   │   ├── 📄 __init__.py
│   │   ├── 📄 cell.py
│   │   └── 📄 space_group.py
│   ├── 📁 sample_model_types
│   │   ├── 📄 __init__.py
│   │   └── 📄 base.py
│   ├── 📄 __init__.py
│   ├── 📄 sample_model.py
│   └── 📄 sample_models.py
├── 📁 summary
│   ├── 📄 __init__.py
│   └── 📄 summary.py
├── 📁 utils
│   ├── 📄 __init__.py
│   ├── 📄 formatting.py
│   ├── 📄 logging.py
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
