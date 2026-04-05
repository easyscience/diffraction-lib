# Package Structure (short)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 crysfml.py
│   │   ├── 📄 cryspy.py
│   │   ├── 📄 factory.py
│   │   └── 📄 pdffit.py
│   ├── 📁 categories
│   │   ├── 📁 aliases
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 constraints
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 fit_mode
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 enums.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 fit_mode.py
│   │   ├── 📁 joint_fit_experiments
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   └── 📄 __init__.py
│   ├── 📁 fit_helpers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   └── 📄 tracking.py
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 dfols.py
│   │   ├── 📄 factory.py
│   │   └── 📄 lmfit.py
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   ├── 📄 fitting.py
│   └── 📄 sequential.py
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 category.py
│   ├── 📄 collection.py
│   ├── 📄 datablock.py
│   ├── 📄 diagnostic.py
│   ├── 📄 factory.py
│   ├── 📄 guard.py
│   ├── 📄 identity.py
│   ├── 📄 metadata.py
│   ├── 📄 singleton.py
│   ├── 📄 validation.py
│   └── 📄 variable.py
├── 📁 crystallography
│   ├── 📄 __init__.py
│   ├── 📄 crystallography.py
│   └── 📄 space_groups.py
├── 📁 datablocks
│   ├── 📁 experiment
│   │   ├── 📁 categories
│   │   │   ├── 📁 background
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 chebyshev.py
│   │   │   │   ├── 📄 enums.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 line_segment.py
│   │   │   ├── 📁 data
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 bragg_pd.py
│   │   │   │   ├── 📄 bragg_sc.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 total_pd.py
│   │   │   ├── 📁 diffrn
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 excluded_regions
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 experiment_type
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 extinction
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 shelx.py
│   │   │   ├── 📁 instrument
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 tof.py
│   │   │   ├── 📁 linked_crystal
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 linked_phases
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 peak
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   ├── 📄 cwl_mixins.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   ├── 📄 tof.py
│   │   │   │   ├── 📄 tof_mixins.py
│   │   │   │   ├── 📄 total.py
│   │   │   │   └── 📄 total_mixins.py
│   │   │   └── 📄 __init__.py
│   │   ├── 📁 item
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 bragg_pd.py
│   │   │   ├── 📄 bragg_sc.py
│   │   │   ├── 📄 enums.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 total_pd.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 collection.py
│   ├── 📁 structure
│   │   ├── 📁 categories
│   │   │   ├── 📁 atom_sites
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 cell
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 space_group
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   └── 📄 __init__.py
│   │   ├── 📁 item
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   └── 📄 factory.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 collection.py
│   └── 📄 __init__.py
├── 📁 display
│   ├── 📁 plotters
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ascii.py
│   │   ├── 📄 base.py
│   │   └── 📄 plotly.py
│   ├── 📁 tablers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 pandas.py
│   │   └── 📄 rich.py
│   ├── 📄 __init__.py
│   ├── 📄 base.py
│   ├── 📄 plotting.py
│   ├── 📄 tables.py
│   └── 📄 utils.py
├── 📁 io
│   ├── 📁 cif
│   │   ├── 📄 __init__.py
│   │   ├── 📄 handler.py
│   │   ├── 📄 parse.py
│   │   └── 📄 serialize.py
│   ├── 📄 __init__.py
│   └── 📄 ascii.py
├── 📁 project
│   ├── 📄 __init__.py
│   ├── 📄 project.py
│   └── 📄 project_info.py
├── 📁 summary
│   ├── 📄 __init__.py
│   └── 📄 summary.py
├── 📁 utils
│   ├── 📁 _vendored
│   │   ├── 📁 jupyter_dark_detect
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 detector.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 theme_detect.py
│   ├── 📄 __init__.py
│   ├── 📄 enums.py
│   ├── 📄 environment.py
│   ├── 📄 logging.py
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
