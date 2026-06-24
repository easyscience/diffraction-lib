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
│   │   ├── 📄 pdffit.py
│   │   └── 📄 support.py
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
│   ├── 📁 corrections
│   │   ├── 📄 __init__.py
│   │   ├── 📄 absorption.py
│   │   └── 📄 polarization.py
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
│   ├── 📄 sequential.py
│   └── 📄 verification.py
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
│   │   │   ├── 📁 absorption
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 cylinder_hewat.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   └── 📄 none.py
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
│   │   │   ├── 📁 data_range
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   ├── 📄 sc.py
│   │   │   │   └── 📄 tof.py
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
│   │   │   ├── 📁 linked_phases
│   │   │   ├── 📁 linked_structure
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
│   │   │   ├── 📁 linked_structures
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
│   │   │   ├── 📁 pref_orient
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   └── 📄 factory.py
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
│   │   ├── 📁 assets
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
│   ├── 📄 links.py
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
│   ├── 📁 edi
│   │   ├── 📄 __init__.py
│   │   └── 📄 serialize.py
│   ├── 📄 __init__.py
│   ├── 📄 ascii.py
│   └── 📄 results_sidecar.py
├── 📁 project
│   ├── 📁 categories
│   │   ├── 📁 info
│   │   ├── 📁 metadata
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
│   └── 📄 project_metadata.py
├── 📁 report
│   ├── 📁 templates
│   │   ├── 📁 html
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
│   ├── 📄 __init__.py
│   ├── 📄 enums.py
│   ├── 📄 environment.py
│   ├── 📄 logging.py
│   ├── 📄 matplotlib_config.py
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
