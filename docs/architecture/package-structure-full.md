# Package Structure (full)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class CalculatorBase
│   │   ├── 📄 crysfml.py
│   │   │   └── 🏷️ class CrysfmlCalculator
│   │   ├── 📄 cryspy.py
│   │   │   └── 🏷️ class CryspyCalculator
│   │   ├── 📄 factory.py
│   │   │   └── 🏷️ class CalculatorFactory
│   │   └── 📄 pdffit.py
│   │       └── 🏷️ class PdffitCalculator
│   ├── 📁 categories
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
│   ├── 📁 fit_helpers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   │   └── 🏷️ class FitResults
│   │   └── 📄 tracking.py
│   │       └── 🏷️ class FitProgressTracker
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class MinimizerBase
│   │   ├── 📄 dfols.py
│   │   │   └── 🏷️ class DfolsMinimizer
│   │   ├── 📄 factory.py
│   │   │   └── 🏷️ class MinimizerFactory
│   │   └── 📄 lmfit.py
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
│   ├── 📄 category.py
│   │   ├── 🏷️ class CategoryItem
│   │   └── 🏷️ class CategoryCollection
│   ├── 📄 collection.py
│   │   └── 🏷️ class CollectionBase
│   ├── 📄 datablock.py
│   │   ├── 🏷️ class DatablockItem
│   │   └── 🏷️ class DatablockCollection
│   ├── 📄 diagnostic.py
│   │   └── 🏷️ class Diagnostics
│   ├── 📄 factory.py
│   │   └── 🏷️ class FactoryBase
│   ├── 📄 guard.py
│   │   └── 🏷️ class GuardedBase
│   ├── 📄 identity.py
│   │   └── 🏷️ class Identity
│   ├── 📄 parameters.py
│   │   ├── 🏷️ class GenericDescriptorBase
│   │   ├── 🏷️ class GenericStringDescriptor
│   │   ├── 🏷️ class GenericNumericDescriptor
│   │   ├── 🏷️ class GenericParameter
│   │   ├── 🏷️ class StringDescriptor
│   │   ├── 🏷️ class NumericDescriptor
│   │   └── 🏷️ class Parameter
│   ├── 📄 singletons.py
│   │   ├── 🏷️ class SingletonBase
│   │   ├── 🏷️ class UidMapHandler
│   │   └── 🏷️ class ConstraintsHandler
│   └── 📄 validation.py
│       ├── 🏷️ class DataTypes
│       ├── 🏷️ class ValidationStage
│       ├── 🏷️ class ValidatorBase
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
│   ├── 📁 categories
│   │   ├── 📁 background
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class BackgroundBase
│   │   │   ├── 📄 chebyshev.py
│   │   │   │   ├── 🏷️ class PolynomialTerm
│   │   │   │   └── 🏷️ class ChebyshevPolynomialBackground
│   │   │   ├── 📄 enums.py
│   │   │   │   └── 🏷️ class BackgroundTypeEnum
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class BackgroundFactory
│   │   │   └── 📄 line_segment.py
│   │   │       ├── 🏷️ class LineSegment
│   │   │       └── 🏷️ class LineSegmentBackground
│   │   ├── 📁 instrument
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class InstrumentBase
│   │   │   ├── 📄 cwl.py
│   │   │   │   └── 🏷️ class CwlInstrument
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class InstrumentFactory
│   │   │   └── 📄 tof.py
│   │   │       └── 🏷️ class TofInstrument
│   │   ├── 📁 peak
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class PeakBase
│   │   │   ├── 📄 cwl.py
│   │   │   │   ├── 🏷️ class CwlPseudoVoigt
│   │   │   │   ├── 🏷️ class CwlSplitPseudoVoigt
│   │   │   │   └── 🏷️ class CwlThompsonCoxHastings
│   │   │   ├── 📄 cwl_mixins.py
│   │   │   │   ├── 🏷️ class CwlBroadeningMixin
│   │   │   │   ├── 🏷️ class EmpiricalAsymmetryMixin
│   │   │   │   └── 🏷️ class FcjAsymmetryMixin
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class PeakFactory
│   │   │   ├── 📄 tof.py
│   │   │   │   ├── 🏷️ class TofPseudoVoigt
│   │   │   │   ├── 🏷️ class TofPseudoVoigtIkedaCarpenter
│   │   │   │   └── 🏷️ class TofPseudoVoigtBackToBack
│   │   │   ├── 📄 tof_mixins.py
│   │   │   │   ├── 🏷️ class TofBroadeningMixin
│   │   │   │   └── 🏷️ class IkedaCarpenterAsymmetryMixin
│   │   │   ├── 📄 total.py
│   │   │   │   └── 🏷️ class TotalGaussianDampedSinc
│   │   │   └── 📄 total_mixins.py
│   │   │       └── 🏷️ class TotalBroadeningMixin
│   │   ├── 📄 __init__.py
│   │   ├── 📄 excluded_regions.py
│   │   │   ├── 🏷️ class ExcludedRegion
│   │   │   └── 🏷️ class ExcludedRegions
│   │   ├── 📄 experiment_type.py
│   │   │   └── 🏷️ class ExperimentType
│   │   └── 📄 linked_phases.py
│   │       ├── 🏷️ class LinkedPhase
│   │       └── 🏷️ class LinkedPhases
│   ├── 📁 datastore
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class DatastoreBase
│   │   ├── 📄 factory.py
│   │   │   └── 🏷️ class DatastoreFactory
│   │   ├── 📄 pd.py
│   │   │   └── 🏷️ class PdDatastore
│   │   └── 📄 sc.py
│   │       └── 🏷️ class ScDatastore
│   ├── 📁 experiment
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   ├── 🏷️ class ExperimentBase
│   │   │   └── 🏷️ class PdExperimentBase
│   │   ├── 📄 bragg_pd.py
│   │   │   └── 🏷️ class BraggPdExperiment
│   │   ├── 📄 bragg_sc.py
│   │   │   └── 🏷️ class BraggScExperiment
│   │   ├── 📄 enums.py
│   │   │   ├── 🏷️ class SampleFormEnum
│   │   │   ├── 🏷️ class ScatteringTypeEnum
│   │   │   ├── 🏷️ class RadiationProbeEnum
│   │   │   ├── 🏷️ class BeamModeEnum
│   │   │   └── 🏷️ class PeakProfileTypeEnum
│   │   ├── 📄 factory.py
│   │   │   └── 🏷️ class ExperimentFactory
│   │   ├── 📄 instrument_mixin.py
│   │   │   └── 🏷️ class InstrumentMixin
│   │   └── 📄 total_pd.py
│   │       └── 🏷️ class TotalPdExperiment
│   ├── 📄 __init__.py
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
│   ├── 📁 categories
│   │   ├── 📄 __init__.py
│   │   ├── 📄 atom_sites.py
│   │   │   ├── 🏷️ class AtomSite
│   │   │   └── 🏷️ class AtomSites
│   │   ├── 📄 cell.py
│   │   │   └── 🏷️ class Cell
│   │   └── 📄 space_group.py
│   │       └── 🏷️ class SpaceGroup
│   ├── 📁 sample_model
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class SampleModelBase
│   │   └── 📄 factory.py
│   │       └── 🏷️ class SampleModelFactory
│   ├── 📄 __init__.py
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
