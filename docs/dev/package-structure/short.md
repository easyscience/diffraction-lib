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
│   │   ├── 📁 fit_parameter_correlations
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 fit_parameters
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 fit_result
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 bayesian.py
│   │   │   ├── 📄 default.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 lsq.py
│   │   ├── 📁 fitting_mode
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 joint_fit
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 minimizer
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 bayesian_base.py
│   │   │   ├── 📄 bumps.py
│   │   │   ├── 📄 bumps_amoeba.py
│   │   │   ├── 📄 bumps_de.py
│   │   │   ├── 📄 bumps_dream.py
│   │   │   ├── 📄 bumps_lm.py
│   │   │   ├── 📄 dfols.py
│   │   │   ├── 📄 emcee.py
│   │   │   ├── 📄 factory.py
│   │   │   ├── 📄 lmfit.py
│   │   │   ├── 📄 lmfit_least_squares.py
│   │   │   ├── 📄 lmfit_leastsq.py
│   │   │   └── 📄 lsq_base.py
│   │   ├── 📁 sequential_fit
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 sequential_fit_extract
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 software
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   └── 📄 __init__.py
│   ├── 📁 fit_helpers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 _diagnostics.py
│   │   ├── 📄 bayesian.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   └── 📄 tracking.py
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 bumps.py
│   │   ├── 📄 bumps_amoeba.py
│   │   ├── 📄 bumps_de.py
│   │   ├── 📄 bumps_dream.py
│   │   ├── 📄 bumps_lm.py
│   │   ├── 📄 dfols.py
│   │   ├── 📄 emcee.py
│   │   ├── 📄 emcee_defaults.py
│   │   ├── 📄 enums.py
│   │   ├── 📄 factory.py
│   │   ├── 📄 lmfit.py
│   │   ├── 📄 lmfit_least_squares.py
│   │   └── 📄 lmfit_leastsq.py
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   ├── 📄 enums.py
│   ├── 📄 fitting.py
│   └── 📄 sequential.py
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 category.py
│   ├── 📄 category_owner.py
│   ├── 📄 collection.py
│   ├── 📄 datablock.py
│   ├── 📄 diagnostic.py
│   ├── 📄 display_handler.py
│   ├── 📄 errors.py
│   ├── 📄 factory.py
│   ├── 📄 guard.py
│   ├── 📄 identity.py
│   ├── 📄 metadata.py
│   ├── 📄 posterior.py
│   ├── 📄 singleton.py
│   ├── 📄 switchable.py
│   ├── 📄 units_vocabulary.py
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
│   │   │   │   ├── 📄 estimate.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 line_segment.py
│   │   │   ├── 📁 calculator
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 data
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 bragg_pd.py
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
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 becker_coppens.py
│   │   │   │   └── 📄 factory.py
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
│   │   │   ├── 📁 refln
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 bragg_pd.py
│   │   │   │   ├── 📄 bragg_sc.py
│   │   │   │   └── 📄 factory.py
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
│   │   │   ├── 📁 atom_site_aniso
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 atom_sites
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   ├── 📄 enums.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 cell
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 geom
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 space_group
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 space_group_wyckoff
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
│   ├── 📁 structure
│   │   ├── 📁 assets
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 colors.py
│   │   │   ├── 📄 elements.py
│   │   │   └── 📄 radii.py
│   │   ├── 📁 renderers
│   │   │   ├── 📁 vendor
│   │   │   │   └── 📁 threejs
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 ascii.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 raster.py
│   │   │   └── 📄 threejs.py
│   │   ├── 📁 templates
│   │   ├── 📄 __init__.py
│   │   ├── 📄 builder.py
│   │   ├── 📄 enums.py
│   │   ├── 📄 scene.py
│   │   └── 📄 viewing.py
│   ├── 📁 tablers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 pandas.py
│   │   └── 📄 rich.py
│   ├── 📄 __init__.py
│   ├── 📄 base.py
│   ├── 📄 plotting.py
│   ├── 📄 progress.py
│   ├── 📄 tables.py
│   ├── 📄 theme.py
│   └── 📄 utils.py
├── 📁 io
│   ├── 📁 cif
│   │   ├── 📄 __init__.py
│   │   ├── 📄 handler.py
│   │   ├── 📄 iucr_transformers.py
│   │   ├── 📄 iucr_writer.py
│   │   ├── 📄 parse.py
│   │   └── 📄 serialize.py
│   ├── 📄 __init__.py
│   ├── 📄 ascii.py
│   └── 📄 results_sidecar.py
├── 📁 project
│   ├── 📁 categories
│   │   ├── 📁 info
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 rendering_plot
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 rendering_structure
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 rendering_table
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 report
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 structure_style
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 structure_view
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   ├── 📁 verbosity
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   └── 📄 factory.py
│   │   └── 📄 __init__.py
│   ├── 📄 __init__.py
│   ├── 📄 display.py
│   ├── 📄 project.py
│   ├── 📄 project_config.py
│   └── 📄 project_info.py
├── 📁 report
│   ├── 📁 templates
│   │   ├── 📁 html
│   │   │   └── 📁 vendor
│   │   └── 📁 tex
│   ├── 📄 __init__.py
│   ├── 📄 data_context.py
│   ├── 📄 enums.py
│   ├── 📄 fit_plot.py
│   ├── 📄 html_renderer.py
│   ├── 📄 pdf_compiler.py
│   ├── 📄 style.py
│   └── 📄 tex_renderer.py
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
│   ├── 📄 matplotlib_config.py
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
