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
│   │   ├── 📁 aliases
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class Alias
│   │   │   │   └── 🏷️ class Aliases
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class AliasesFactory
│   │   ├── 📁 constraints
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class Constraint
│   │   │   │   └── 🏷️ class Constraints
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class ConstraintsFactory
│   │   ├── 📁 fit_mode
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 enums.py
│   │   │   │   └── 🏷️ class FitModeEnum
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class FitModeFactory
│   │   │   └── 📄 fit_mode.py
│   │   │       └── 🏷️ class FitMode
│   │   ├── 📁 joint_fit_experiments
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class JointFitExperiment
│   │   │   │   └── 🏷️ class JointFitExperiments
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class JointFitExperimentsFactory
│   │   └── 📄 __init__.py
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
│   │   ├── 🏷️ class AnalysisDisplay
│   │   └── 🏷️ class Analysis
│   ├── 📄 fitting.py
│   │   └── 🏷️ class Fitter
│   └── 📄 sequential.py
│       └── 🏷️ class SequentialFitTemplate
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
│   │   │   ├── 📁 diffrn
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class DefaultDiffrn
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class DiffrnFactory
│   │   │   ├── 📁 excluded_regions
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   ├── 🏷️ class ExcludedRegion
│   │   │   │   │   └── 🏷️ class ExcludedRegions
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class ExcludedRegionsFactory
│   │   │   ├── 📁 experiment_type
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class ExperimentType
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class ExperimentTypeFactory
│   │   │   ├── 📁 extinction
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class ExtinctionFactory
│   │   │   │   └── 📄 becker_coppens.py
│   │   │   │       └── 🏷️ class BeckerCoppensExtinction
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
│   │   │   ├── 📁 linked_crystal
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class LinkedCrystal
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class LinkedCrystalFactory
│   │   │   ├── 📁 linked_phases
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   ├── 🏷️ class LinkedPhase
│   │   │   │   │   └── 🏷️ class LinkedPhases
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class LinkedPhasesFactory
│   │   │   ├── 📁 peak
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   │   └── 🏷️ class PeakBase
│   │   │   │   ├── 📄 cwl.py
│   │   │   │   │   ├── 🏷️ class CwlPseudoVoigt
│   │   │   │   │   ├── 🏷️ class CwlPseudoVoigtEmpiricalAsymmetry
│   │   │   │   │   └── 🏷️ class CwlThompsonCoxHastings
│   │   │   │   ├── 📄 cwl_mixins.py
│   │   │   │   │   ├── 🏷️ class CwlBroadeningMixin
│   │   │   │   │   ├── 🏷️ class EmpiricalAsymmetryMixin
│   │   │   │   │   └── 🏷️ class FcjAsymmetryMixin
│   │   │   │   ├── 📄 factory.py
│   │   │   │   │   └── 🏷️ class PeakFactory
│   │   │   │   ├── 📄 tof.py
│   │   │   │   │   ├── 🏷️ class TofJorgensen
│   │   │   │   │   └── 🏷️ class TofJorgensenVonDreele
│   │   │   │   ├── 📄 tof_mixins.py
│   │   │   │   │   ├── 🏷️ class TofGaussianBroadeningMixin
│   │   │   │   │   ├── 🏷️ class TofLorentzianBroadeningMixin
│   │   │   │   │   └── 🏷️ class TofBackToBackExponentialMixin
│   │   │   │   ├── 📄 total.py
│   │   │   │   │   └── 🏷️ class TotalGaussianDampedSinc
│   │   │   │   └── 📄 total_mixins.py
│   │   │   │       └── 🏷️ class TotalBroadeningMixin
│   │   │   └── 📄 __init__.py
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
│   │   │   ├── 📁 atom_sites
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   ├── 🏷️ class AtomSite
│   │   │   │   │   └── 🏷️ class AtomSites
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class AtomSitesFactory
│   │   │   ├── 📁 cell
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class Cell
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class CellFactory
│   │   │   ├── 📁 space_group
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class SpaceGroup
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class SpaceGroupFactory
│   │   │   └── 📄 __init__.py
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
│   ├── 📄 __init__.py
│   └── 📄 ascii.py
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
│   ├── 📄 enums.py
│   │   └── 🏷️ class VerbosityEnum
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
