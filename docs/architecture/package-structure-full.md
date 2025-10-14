# Package Structure (full)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 calculator_base.py
│   │   │   └── 🏷️ class CalculatorBase
│   │   ├── 📄 calculator_crysfml.py
│   │   │   └── 🏷️ class CrysfmlCalculator
│   │   ├── 📄 calculator_cryspy.py
│   │   │   └── 🏷️ class CryspyCalculator
│   │   ├── 📄 calculator_factory.py
│   │   │   └── 🏷️ class CalculatorFactory
│   │   └── 📄 calculator_pdffit.py
│   │       └── 🏷️ class PdffitCalculator
│   ├── 📁 category_collections
│   │   ├── 📄 __init__.py
│   │   ├── 📄 aliases.py
│   │   │   ├── 🏷️ class Alias
│   │   │   └── 🏷️ class Aliases
│   │   ├── 📄 constraints.py
│   │   │   ├── 🏷️ class Constraint
│   │   │   └── 🏷️ class Constraints
│   │   └── 📄 joint_fit_experiments.py
│   │       ├── 🏷️ class JointFitExperiment
│   │       └── 🏷️ class JointFitExperiments
│   ├── 📁 fit_support
│   │   ├── 📄 __init__.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   │   └── 🏷️ class FitResults
│   │   └── 📄 tracking.py
│   │       └── 🏷️ class FittingProgressTracker
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 minimizer_base.py
│   │   │   └── 🏷️ class MinimizerBase
│   │   ├── 📄 minimizer_dfols.py
│   │   │   └── 🏷️ class DfolsMinimizer
│   │   ├── 📄 minimizer_factory.py
│   │   │   └── 🏷️ class MinimizerFactory
│   │   └── 📄 minimizer_lmfit.py
│   │       └── 🏷️ class LmfitMinimizer
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   │   └── 🏷️ class Analysis
│   ├── 📄 calculation.py
│   │   └── 🏷️ class Calculator
│   └── 📄 fitting.py
│       └── 🏷️ class Fitter
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 categories.py
│   │   ├── 🏷️ class CategoryItem
│   │   └── 🏷️ class CategoryCollection
│   ├── 📄 collections.py
│   │   └── 🏷️ class CollectionBase
│   ├── 📄 datablocks.py
│   │   ├── 🏷️ class DatablockItem
│   │   └── 🏷️ class DatablockCollection
│   ├── 📄 diagnostics.py
│   │   └── 🏷️ class Diagnostics
│   ├── 📄 guards.py
│   │   └── 🏷️ class GuardedBase
│   ├── 📄 identity.py
│   │   └── 🏷️ class Identity
│   ├── 📄 parameters.py
│   │   ├── 🏷️ class GenericDescriptorBase
│   │   ├── 🏷️ class GenericDescriptorStr
│   │   ├── 🏷️ class GenericDescriptorFloat
│   │   ├── 🏷️ class GenericParameter
│   │   ├── 🏷️ class DescriptorStr
│   │   ├── 🏷️ class DescriptorFloat
│   │   └── 🏷️ class Parameter
│   ├── 📄 singletons.py
│   │   ├── 🏷️ class BaseSingleton
│   │   ├── 🏷️ class UidMapHandler
│   │   └── 🏷️ class ConstraintsHandler
│   └── 📄 validation.py
│       ├── 🏷️ class DataTypes
│       ├── 🏷️ class ValidationStage
│       ├── 🏷️ class BaseValidator
│       ├── 🏷️ class TypeValidator
│       ├── 🏷️ class RangeValidator
│       ├── 🏷️ class MembershipValidator
│       ├── 🏷️ class RegexValidator
│       └── 🏷️ class AttributeSpec
├── 📁 crystallography
│   ├── 📄 __init__.py
│   ├── 📄 crystallography.py
│   └── 📄 space_groups.py
├── 📁 experiments
│   ├── 📁 category_collections
│   │   ├── 📁 background_types
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class BackgroundBase
│   │   │   ├── 📄 chebyshev.py
│   │   │   │   ├── 🏷️ class PolynomialTerm
│   │   │   │   └── 🏷️ class ChebyshevPolynomialBackground
│   │   │   ├── 📄 enums.py
│   │   │   │   └── 🏷️ class BackgroundTypeEnum
│   │   │   └── 📄 line_segment.py
│   │   │       ├── 🏷️ class Point
│   │   │       └── 🏷️ class LineSegmentBackground
│   │   ├── 📄 __init__.py
│   │   ├── 📄 background.py
│   │   │   └── 🏷️ class BackgroundFactory
│   │   ├── 📄 excluded_regions.py
│   │   │   ├── 🏷️ class ExcludedRegion
│   │   │   └── 🏷️ class ExcludedRegions
│   │   └── 📄 linked_phases.py
│   │       ├── 🏷️ class LinkedPhase
│   │       └── 🏷️ class LinkedPhases
│   ├── 📁 category_items
│   │   ├── 📁 instrument_setups
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class InstrumentBase
│   │   │   ├── 📄 cw.py
│   │   │   │   └── 🏷️ class ConstantWavelengthInstrument
│   │   │   └── 📄 tof.py
│   │   │       └── 🏷️ class TimeOfFlightInstrument
│   │   ├── 📁 peak_profiles
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class PeakBase
│   │   │   ├── 📄 cw.py
│   │   │   │   ├── 🏷️ class ConstantWavelengthPseudoVoigt
│   │   │   │   ├── 🏷️ class ConstantWavelengthSplitPseudoVoigt
│   │   │   │   └── 🏷️ class ConstantWavelengthThompsonCoxHastings
│   │   │   ├── 📄 cw_mixins.py
│   │   │   │   ├── 🏷️ class ConstantWavelengthBroadeningMixin
│   │   │   │   ├── 🏷️ class EmpiricalAsymmetryMixin
│   │   │   │   └── 🏷️ class FcjAsymmetryMixin
│   │   │   ├── 📄 pdf.py
│   │   │   │   └── 🏷️ class PairDistributionFunctionGaussianDampedSinc
│   │   │   ├── 📄 pdf_mixins.py
│   │   │   │   └── 🏷️ class PairDistributionFunctionBroadeningMixin
│   │   │   ├── 📄 tof.py
│   │   │   │   ├── 🏷️ class TimeOfFlightPseudoVoigt
│   │   │   │   ├── 🏷️ class TimeOfFlightPseudoVoigtIkedaCarpenter
│   │   │   │   └── 🏷️ class TimeOfFlightPseudoVoigtBackToBack
│   │   │   └── 📄 tof_mixins.py
│   │   │       ├── 🏷️ class TimeOfFlightBroadeningMixin
│   │   │       └── 🏷️ class IkedaCarpenterAsymmetryMixin
│   │   ├── 📄 __init__.py
│   │   ├── 📄 experiment_type.py
│   │   │   └── 🏷️ class ExperimentType
│   │   ├── 📄 instrument.py
│   │   │   └── 🏷️ class InstrumentFactory
│   │   └── 📄 peak.py
│   │       └── 🏷️ class PeakFactory
│   ├── 📁 datastore_types
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class BaseDatastore
│   │   ├── 📄 powder.py
│   │   │   └── 🏷️ class PowderDatastore
│   │   └── 📄 single_crystal.py
│   │       └── 🏷️ class SingleCrystalDatastore
│   ├── 📁 experiment_types
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   ├── 🏷️ class BaseExperiment
│   │   │   └── 🏷️ class BasePowderExperiment
│   │   ├── 📄 enums.py
│   │   │   ├── 🏷️ class SampleFormEnum
│   │   │   ├── 🏷️ class ScatteringTypeEnum
│   │   │   ├── 🏷️ class RadiationProbeEnum
│   │   │   ├── 🏷️ class BeamModeEnum
│   │   │   └── 🏷️ class PeakProfileTypeEnum
│   │   ├── 📄 instrument_mixin.py
│   │   │   └── 🏷️ class InstrumentMixin
│   │   ├── 📄 pdf.py
│   │   │   └── 🏷️ class PairDistributionFunctionExperiment
│   │   ├── 📄 powder.py
│   │   │   └── 🏷️ class PowderExperiment
│   │   └── 📄 single_crystal.py
│   │       └── 🏷️ class SingleCrystalExperiment
│   ├── 📄 __init__.py
│   ├── 📄 datastore.py
│   │   └── 🏷️ class DatastoreFactory
│   ├── 📄 experiment.py
│   │   ├── 🏷️ class ExperimentFactory
│   │   └── 🏷️ class Experiment
│   └── 📄 experiments.py
│       └── 🏷️ class Experiments
├── 📁 io
│   └── 📁 cif
│       ├── 📄 handler.py
│       │   └── 🏷️ class CifHandler
│       └── 📄 serialize.py
├── 📁 plotting
│   ├── 📁 plotters
│   │   ├── 📄 __init__.py
│   │   ├── 📄 plotter_ascii.py
│   │   │   └── 🏷️ class AsciiPlotter
│   │   ├── 📄 plotter_base.py
│   │   │   └── 🏷️ class PlotterBase
│   │   └── 📄 plotter_plotly.py
│   │       └── 🏷️ class PlotlyPlotter
│   ├── 📄 __init__.py
│   └── 📄 plotting.py
│       ├── 🏷️ class Plotter
│       └── 🏷️ class PlotterFactory
├── 📁 project
│   ├── 📄 __init__.py
│   ├── 📄 project.py
│   │   └── 🏷️ class Project
│   └── 📄 project_info.py
│       └── 🏷️ class ProjectInfo
├── 📁 sample_models
│   ├── 📁 category_collections
│   │   ├── 📄 __init__.py
│   │   └── 📄 atom_sites.py
│   │       ├── 🏷️ class AtomSite
│   │       └── 🏷️ class AtomSites
│   ├── 📁 category_items
│   │   ├── 📄 __init__.py
│   │   ├── 📄 cell.py
│   │   │   └── 🏷️ class Cell
│   │   └── 📄 space_group.py
│   │       └── 🏷️ class SpaceGroup
│   ├── 📁 sample_model_types
│   │   ├── 📄 __init__.py
│   │   └── 📄 base.py
│   │       └── 🏷️ class BaseSampleModel
│   ├── 📄 __init__.py
│   ├── 📄 sample_model.py
│   │   ├── 🏷️ class SampleModelFactory
│   │   └── 🏷️ class SampleModel
│   └── 📄 sample_models.py
│       └── 🏷️ class SampleModels
├── 📁 summary
│   ├── 📄 __init__.py
│   └── 📄 summary.py
│       └── 🏷️ class Summary
├── 📁 utils
│   ├── 📄 __init__.py
│   ├── 📄 formatting.py
│   ├── 📄 logging.py
│   │   └── 🏷️ class Logger
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
