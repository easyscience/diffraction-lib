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
│   │       ├── 🏷️ class _TerminalLiveHandle
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
│   ├── 📄 metadata.py
│   │   ├── 🏷️ class TypeInfo
│   │   ├── 🏷️ class Compatibility
│   │   └── 🏷️ class CalculatorSupport
│   ├── 📄 singleton.py
│   │   ├── 🏷️ class SingletonBase
│   │   ├── 🏷️ class UidMapHandler
│   │   └── 🏷️ class ConstraintsHandler
│   ├── 📄 validation.py
│   │   ├── 🏷️ class DataTypeHints
│   │   ├── 🏷️ class DataTypes
│   │   ├── 🏷️ class ValidationStage
│   │   ├── 🏷️ class ValidatorBase
│   │   ├── 🏷️ class TypeValidator
│   │   ├── 🏷️ class RangeValidator
│   │   ├── 🏷️ class MembershipValidator
│   │   ├── 🏷️ class RegexValidator
│   │   └── 🏷️ class AttributeSpec
│   └── 📄 variable.py
│       ├── 🏷️ class GenericDescriptorBase
│       ├── 🏷️ class GenericStringDescriptor
│       ├── 🏷️ class GenericNumericDescriptor
│       ├── 🏷️ class GenericParameter
│       ├── 🏷️ class StringDescriptor
│       ├── 🏷️ class NumericDescriptor
│       └── 🏷️ class Parameter
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
│   │   │   │   │   └── 🏷️ class BackgroundBase
│   │   │   │   ├── 📄 chebyshev.py
│   │   │   │   │   ├── 🏷️ class PolynomialTerm
│   │   │   │   │   └── 🏷️ class ChebyshevPolynomialBackground
│   │   │   │   ├── 📄 enums.py
│   │   │   │   │   └── 🏷️ class BackgroundTypeEnum
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class BackgroundFactory
│   │   │   │   └── 📄 line_segment.py
│   │   │   │       ├── 🏷️ class LineSegment
│   │   │   │       └── 🏷️ class LineSegmentBackground
│   │   │   ├── 📁 data
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 bragg_pd.py
│   │   │   │   │   ├── 🏷️ class PdDataPointBaseMixin
│   │   │   │   │   ├── 🏷️ class PdCwlDataPointMixin
│   │   │   │   │   ├── 🏷️ class PdTofDataPointMixin
│   │   │   │   │   ├── 🏷️ class PdCwlDataPoint
│   │   │   │   │   ├── 🏷️ class PdTofDataPoint
│   │   │   │   │   ├── 🏷️ class PdDataBase
│   │   │   │   │   ├── 🏷️ class PdCwlData
│   │   │   │   │   └── 🏷️ class PdTofData
│   │   │   │   ├── 📄 bragg_sc.py
│   │   │   │   │   ├── 🏷️ class Refln
│   │   │   │   │   └── 🏷️ class ReflnData
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class DataFactory
│   │   │   │   └── 📄 total_pd.py
│   │   │   │       ├── 🏷️ class TotalDataPoint
│   │   │   │       ├── 🏷️ class TotalDataBase
│   │   │   │       └── 🏷️ class TotalData
│   │   │   ├── 📁 instrument
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   │   └── 🏷️ class InstrumentBase
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   │   ├── 🏷️ class CwlInstrumentBase
│   │   │   │   │   ├── 🏷️ class CwlScInstrument
│   │   │   │   │   └── 🏷️ class CwlPdInstrument
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class InstrumentFactory
│   │   │   │   └── 📄 tof.py
│   │   │   │       ├── 🏷️ class TofScInstrument
│   │   │   │       └── 🏷️ class TofPdInstrument
│   │   │   ├── 📁 peak
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   │   └── 🏷️ class PeakBase
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   │   ├── 🏷️ class CwlPseudoVoigt
│   │   │   │   │   ├── 🏷️ class CwlSplitPseudoVoigt
│   │   │   │   │   └── 🏷️ class CwlThompsonCoxHastings
│   │   │   │   ├── 📄 cwl_mixins.py
│   │   │   │   │   ├── 🏷️ class CwlBroadeningMixin
│   │   │   │   │   ├── 🏷️ class EmpiricalAsymmetryMixin
│   │   │   │   │   └── 🏷️ class FcjAsymmetryMixin
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class PeakFactory
│   │   │   │   ├── 📄 tof.py
│   │   │   │   │   ├── 🏷️ class TofPseudoVoigt
│   │   │   │   │   ├── 🏷️ class TofPseudoVoigtIkedaCarpenter
│   │   │   │   │   └── 🏷️ class TofPseudoVoigtBackToBack
│   │   │   │   ├── 📄 tof_mixins.py
│   │   │   │   │   ├── 🏷️ class TofBroadeningMixin
│   │   │   │   │   └── 🏷️ class IkedaCarpenterAsymmetryMixin
│   │   │   │   ├── 📄 total.py
│   │   │   │   │   └── 🏷️ class TotalGaussianDampedSinc
│   │   │   │   └── 📄 total_mixins.py
│   │   │   │       └── 🏷️ class TotalBroadeningMixin
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 excluded_regions.py
│   │   │   │   ├── 🏷️ class ExcludedRegion
│   │   │   │   └── 🏷️ class ExcludedRegions
│   │   │   ├── 📄 experiment_type.py
│   │   │   │   └── 🏷️ class ExperimentType
│   │   │   ├── 📄 extinction.py
│   │   │   │   └── 🏷️ class Extinction
│   │   │   ├── 📄 linked_crystal.py
│   │   │   │   └── 🏷️ class LinkedCrystal
│   │   │   └── 📄 linked_phases.py
│   │   │       ├── 🏷️ class LinkedPhase
│   │   │       └── 🏷️ class LinkedPhases
│   │   ├── 📁 item
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   ├── 🏷️ class ExperimentBase
│   │   │   │   ├── 🏷️ class ScExperimentBase
│   │   │   │   └── 🏷️ class PdExperimentBase
│   │   │   ├── 📄 bragg_pd.py
│   │   │   │   └── 🏷️ class BraggPdExperiment
│   │   │   ├── 📄 bragg_sc.py
│   │   │   │   ├── 🏷️ class CwlScExperiment
│   │   │   │   └── 🏷️ class TofScExperiment
│   │   │   ├── 📄 enums.py
│   │   │   │   ├── 🏷️ class SampleFormEnum
│   │   │   │   ├── 🏷️ class ScatteringTypeEnum
│   │   │   │   ├── 🏷️ class RadiationProbeEnum
│   │   │   │   ├── 🏷️ class BeamModeEnum
│   │   │   │   ├── 🏷️ class CalculatorEnum
│   │   │   │   └── 🏷️ class PeakProfileTypeEnum
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class ExperimentFactory
│   │   │   └── 📄 total_pd.py
│   │   │       └── 🏷️ class TotalPdExperiment
│   │   ├── 📄 __init__.py
│   │   └── 📄 collection.py
│   │       └── 🏷️ class Experiments
│   ├── 📁 structure
│   │   ├── 📁 categories
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 atom_sites.py
│   │   │   │   ├── 🏷️ class AtomSite
│   │   │   │   └── 🏷️ class AtomSites
│   │   │   ├── 📄 cell.py
│   │   │   │   └── 🏷️ class Cell
│   │   │   └── 📄 space_group.py
│   │   │       └── 🏷️ class SpaceGroup
│   │   ├── 📁 item
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class Structure
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class StructureFactory
│   │   ├── 📄 __init__.py
│   │   └── 📄 collection.py
│   │       └── 🏷️ class Structures
│   └── 📄 __init__.py
├── 📁 display
│   ├── 📁 plotters
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ascii.py
│   │   │   └── 🏷️ class AsciiPlotter
│   │   ├── 📄 base.py
│   │   │   ├── 🏷️ class XAxisType
│   │   │   └── 🏷️ class PlotterBase
│   │   └── 📄 plotly.py
│   │       └── 🏷️ class PlotlyPlotter
│   ├── 📁 tablers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   └── 🏷️ class TableBackendBase
│   │   ├── 📄 pandas.py
│   │   │   └── 🏷️ class PandasTableBackend
│   │   └── 📄 rich.py
│   │       └── 🏷️ class RichTableBackend
│   ├── 📄 __init__.py
│   ├── 📄 base.py
│   │   ├── 🏷️ class RendererBase
│   │   └── 🏷️ class RendererFactoryBase
│   ├── 📄 plotting.py
│   │   ├── 🏷️ class PlotterEngineEnum
│   │   ├── 🏷️ class Plotter
│   │   └── 🏷️ class PlotterFactory
│   ├── 📄 tables.py
│   │   ├── 🏷️ class TableEngineEnum
│   │   ├── 🏷️ class TableRenderer
│   │   └── 🏷️ class TableRendererFactory
│   └── 📄 utils.py
│       └── 🏷️ class JupyterScrollManager
├── 📁 io
│   ├── 📁 cif
│   │   ├── 📄 __init__.py
│   │   ├── 📄 handler.py
│   │   │   └── 🏷️ class CifHandler
│   │   ├── 📄 parse.py
│   │   └── 📄 serialize.py
│   └── 📄 __init__.py
├── 📁 project
│   ├── 📄 __init__.py
│   ├── 📄 project.py
│   │   └── 🏷️ class Project
│   └── 📄 project_info.py
│       └── 🏷️ class ProjectInfo
├── 📁 summary
│   ├── 📄 __init__.py
│   └── 📄 summary.py
│       └── 🏷️ class Summary
├── 📁 utils
│   ├── 📁 _vendored
│   │   ├── 📁 jupyter_dark_detect
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 detector.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 theme_detect.py
│   ├── 📄 __init__.py
│   ├── 📄 environment.py
│   ├── 📄 logging.py
│   │   ├── 🏷️ class IconifiedRichHandler
│   │   ├── 🏷️ class ConsoleManager
│   │   ├── 🏷️ class LoggerConfig
│   │   ├── 🏷️ class ExceptionHookManager
│   │   ├── 🏷️ class Logger
│   │   └── 🏷️ class ConsolePrinter
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
