# Package Structure (full)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   ├── 🏷️ class PowderReflnRecord
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
│   │   ├── 📁 fit_parameter_correlations
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class FitParameterCorrelationItem
│   │   │   │   └── 🏷️ class FitParameterCorrelations
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class FitParameterCorrelationsFactory
│   │   ├── 📁 fit_parameters
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class FitParameterItem
│   │   │   │   └── 🏷️ class FitParameters
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class FitParametersFactory
│   │   ├── 📁 fit_result
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class FitResultBase
│   │   │   ├── 📄 bayesian.py
│   │   │   │   └── 🏷️ class BayesianFitResult
│   │   │   ├── 📄 default.py
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class FitResultFactory
│   │   │   └── 📄 lsq.py
│   │   │       └── 🏷️ class LeastSquaresFitResult
│   │   ├── 📁 fitting_mode
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class FittingMode
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class FittingModeFactory
│   │   ├── 📁 joint_fit
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class JointFitItem
│   │   │   │   └── 🏷️ class JointFitCollection
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class JointFitFactory
│   │   ├── 📁 minimizer
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   │   └── 🏷️ class MinimizerCategoryBase
│   │   │   ├── 📄 bayesian_base.py
│   │   │   │   └── 🏷️ class BayesianMinimizerBase
│   │   │   ├── 📄 bumps.py
│   │   │   │   └── 🏷️ class BumpsMinimizer
│   │   │   ├── 📄 bumps_amoeba.py
│   │   │   │   └── 🏷️ class BumpsAmoebaMinimizer
│   │   │   ├── 📄 bumps_de.py
│   │   │   │   └── 🏷️ class BumpsDeMinimizer
│   │   │   ├── 📄 bumps_dream.py
│   │   │   │   └── 🏷️ class BumpsDreamMinimizer
│   │   │   ├── 📄 bumps_lm.py
│   │   │   │   └── 🏷️ class BumpsLmMinimizer
│   │   │   ├── 📄 dfols.py
│   │   │   │   └── 🏷️ class DfolsMinimizer
│   │   │   ├── 📄 emcee.py
│   │   │   │   └── 🏷️ class EmceeMinimizer
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class MinimizerCategoryFactory
│   │   │   ├── 📄 lmfit.py
│   │   │   │   └── 🏷️ class LmfitMinimizer
│   │   │   ├── 📄 lmfit_least_squares.py
│   │   │   │   └── 🏷️ class LmfitLeastSquaresMinimizer
│   │   │   ├── 📄 lmfit_leastsq.py
│   │   │   │   └── 🏷️ class LmfitLeastsqMinimizer
│   │   │   └── 📄 lsq_base.py
│   │   │       └── 🏷️ class LeastSquaresMinimizerBase
│   │   ├── 📁 sequential_fit
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class SequentialFit
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class SequentialFitFactory
│   │   ├── 📁 sequential_fit_extract
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   ├── 🏷️ class SequentialFitExtractItem
│   │   │   │   └── 🏷️ class SequentialFitExtractCollection
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class SequentialFitExtractFactory
│   │   └── 📄 __init__.py
│   ├── 📁 fit_helpers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 _diagnostics.py
│   │   ├── 📄 bayesian.py
│   │   │   ├── 🏷️ class PosteriorPredictiveSummary
│   │   │   ├── 🏷️ class PosteriorSamples
│   │   │   └── 🏷️ class BayesianFitResults
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   │   └── 🏷️ class FitResults
│   │   └── 📄 tracking.py
│   │       ├── 🏷️ class SamplerProgressUpdate
│   │       └── 🏷️ class FitProgressTracker
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   │   ├── 🏷️ class MinimizerFitOptions
│   │   │   └── 🏷️ class MinimizerBase
│   │   ├── 📄 bumps.py
│   │   │   ├── 🏷️ class _BumpsEvaluationLimitError
│   │   │   ├── 🏷️ class _EasyDiffractionFitness
│   │   │   ├── 🏷️ class _BumpsProgressMonitor
│   │   │   └── 🏷️ class BumpsMinimizer
│   │   ├── 📄 bumps_amoeba.py
│   │   │   └── 🏷️ class BumpsAmoebaMinimizer
│   │   ├── 📄 bumps_de.py
│   │   │   └── 🏷️ class BumpsDEMinimizer
│   │   ├── 📄 bumps_dream.py
│   │   │   ├── 🏷️ class _DreamRunContext
│   │   │   ├── 🏷️ class _DreamDriverResult
│   │   │   ├── 🏷️ class _DreamProgressMonitor
│   │   │   └── 🏷️ class BumpsDreamMinimizer
│   │   ├── 📄 bumps_lm.py
│   │   │   └── 🏷️ class BumpsLmMinimizer
│   │   ├── 📄 dfols.py
│   │   │   └── 🏷️ class DfolsMinimizer
│   │   ├── 📄 emcee.py
│   │   │   ├── 🏷️ class _EmceePoolContext
│   │   │   ├── 🏷️ class _EmceeLogProbability
│   │   │   ├── 🏷️ class _EmceeProgressReporter
│   │   │   └── 🏷️ class EmceeMinimizer
│   │   ├── 📄 emcee_defaults.py
│   │   ├── 📄 enums.py
│   │   │   ├── 🏷️ class MinimizerTypeEnum
│   │   │   ├── 🏷️ class InitializationMethodEnum
│   │   │   └── 🏷️ class DreamPopulationInitializationEnum
│   │   ├── 📄 factory.py
│   │   │   └── 🏷️ class MinimizerFactory
│   │   ├── 📄 lmfit.py
│   │   │   └── 🏷️ class LmfitMinimizer
│   │   ├── 📄 lmfit_least_squares.py
│   │   │   └── 🏷️ class LmfitLeastSquaresMinimizer
│   │   └── 📄 lmfit_leastsq.py
│   │       └── 🏷️ class LmfitLeastsqMinimizer
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   │   ├── 🏷️ class UndoFitOutcome
│   │   ├── 🏷️ class AnalysisDisplay
│   │   ├── 🏷️ class _AnalysisOwnerAccessorsMixin
│   │   ├── 🏷️ class _AnalysisPersistedCategoryAccessorsMixin
│   │   └── 🏷️ class Analysis
│   ├── 📄 enums.py
│   │   ├── 🏷️ class FitModeEnum
│   │   ├── 🏷️ class FitResultKindEnum
│   │   └── 🏷️ class FitCorrelationSourceEnum
│   ├── 📄 fitting.py
│   │   ├── 🏷️ class FitterFitOptions
│   │   └── 🏷️ class Fitter
│   └── 📄 sequential.py
│       ├── 🏷️ class SequentialFitExtractRule
│       ├── 🏷️ class SequentialFitTemplate
│       ├── 🏷️ class SequentialProgressState
│       ├── 🏷️ class SequentialProgressContext
│       ├── 🏷️ class _ChunkProgressMetrics
│       └── 🏷️ class SequentialRunPlan
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 category.py
│   │   ├── 🏷️ class CategoryItem
│   │   └── 🏷️ class CategoryCollection
│   ├── 📄 category_owner.py
│   │   └── 🏷️ class CategoryOwner
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
│   ├── 📄 posterior.py
│   │   └── 🏷️ class PosteriorParameterSummary
│   ├── 📄 singleton.py
│   │   ├── 🏷️ class SingletonBase
│   │   └── 🏷️ class ConstraintsHandler
│   ├── 📄 switchable.py
│   │   └── 🏷️ class SwitchableCategoryBase
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
│       ├── 🏷️ class GenericBoolDescriptor
│       ├── 🏷️ class GenericNumericDescriptor
│       ├── 🏷️ class GenericIntegerDescriptor
│       ├── 🏷️ class GenericParameter
│       ├── 🏷️ class StringDescriptor
│       ├── 🏷️ class BoolDescriptor
│       ├── 🏷️ class NumericDescriptor
│       ├── 🏷️ class IntegerDescriptor
│       └── 🏷️ class Parameter
├── 📁 crystallography
│   ├── 📄 __init__.py
│   ├── 📄 crystallography.py
│   └── 📄 space_groups.py
│       └── 🏷️ class _RestrictedUnpickler
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
│   │   │   ├── 📁 calculator
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   └── 🏷️ class Calculator
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class CalculatorCategoryFactory
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
│   │   │   │   ├── 📄 base.py
│   │   │   │   │   └── 🏷️ class ExtinctionBase
│   │   │   │   ├── 📄 becker_coppens.py
│   │   │   │   │   └── 🏷️ class BeckerCoppensExtinction
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class ExtinctionFactory
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
│   │   │   │   │   ├── 🏷️ class TofPseudoVoigt
│   │   │   │   │   ├── 🏷️ class TofJorgensen
│   │   │   │   │   ├── 🏷️ class TofJorgensenVonDreele
│   │   │   │   │   └── 🏷️ class TofDoubleJorgensenVonDreele
│   │   │   │   ├── 📄 tof_mixins.py
│   │   │   │   │   ├── 🏷️ class TofGaussianBroadeningMixin
│   │   │   │   │   ├── 🏷️ class TofLorentzianBroadeningMixin
│   │   │   │   │   ├── 🏷️ class TofBackToBackExponentialMixin
│   │   │   │   │   └── 🏷️ class TofDoubleExponentialMixin
│   │   │   │   ├── 📄 total.py
│   │   │   │   │   └── 🏷️ class TotalGaussianDampedSinc
│   │   │   │   └── 📄 total_mixins.py
│   │   │   │       └── 🏷️ class TotalBroadeningMixin
│   │   │   ├── 📁 refln
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 bragg_pd.py
│   │   │   │   │   ├── 🏷️ class PowderReflnBase
│   │   │   │   │   ├── 🏷️ class PowderCwlRefln
│   │   │   │   │   ├── 🏷️ class PowderTofRefln
│   │   │   │   │   ├── 🏷️ class PowderReflnDataBase
│   │   │   │   │   ├── 🏷️ class PowderCwlReflnData
│   │   │   │   │   └── 🏷️ class PowderTofReflnData
│   │   │   │   ├── 📄 bragg_sc.py
│   │   │   │   │   ├── 🏷️ class Refln
│   │   │   │   │   └── 🏷️ class ReflnData
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class ReflnFactory
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
│   │   │   │   ├── 🏷️ class PeakProfileTypeEnum
│   │   │   │   └── 🏷️ class ExtinctionModelEnum
│   │   │   ├── 📄 factory.py
│   │   │   │   └── 🏷️ class ExperimentFactory
│   │   │   └── 📄 total_pd.py
│   │   │       └── 🏷️ class TotalPdExperiment
│   │   ├── 📄 __init__.py
│   │   └── 📄 collection.py
│   │       └── 🏷️ class Experiments
│   ├── 📁 structure
│   │   ├── 📁 categories
│   │   │   ├── 📁 atom_site_aniso
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   ├── 🏷️ class AtomSiteAniso
│   │   │   │   │   └── 🏷️ class AtomSiteAnisoCollection
│   │   │   │   └── 📄 factory.py
│   │   │   │       └── 🏷️ class AtomSiteAnisoFactory
│   │   │   ├── 📁 atom_sites
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 default.py
│   │   │   │   │   ├── 🏷️ class AtomSite
│   │   │   │   │   └── 🏷️ class AtomSites
│   │   │   │   ├── 📄 enums.py
│   │   │   │   │   └── 🏷️ class AdpTypeEnum
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
│   │   │   ├── 🏷️ class BraggTickSet
│   │   │   ├── 🏷️ class PowderMeasVsCalcSpec
│   │   │   ├── 🏷️ class XAxisType
│   │   │   └── 🏷️ class PlotterBase
│   │   └── 📄 plotly.py
│   │       ├── 🏷️ class PowderCompositeRows
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
│   │   ├── 🏷️ class PosteriorPairPlotStyleEnum
│   │   ├── 🏷️ class _MeasVsCalcPlotOptions
│   │   ├── 🏷️ class _PowderMeasVsCalcSeries
│   │   ├── 🏷️ class _PosteriorDistributionContext
│   │   ├── 🏷️ class _PosteriorPairsContext
│   │   ├── 🏷️ class _CorrelationHeatmapContext
│   │   ├── 🏷️ class _PosteriorPairsLegendState
│   │   ├── 🏷️ class Plotter
│   │   └── 🏷️ class PlotterFactory
│   ├── 📄 progress.py
│   │   ├── 🏷️ class _TerminalLiveHandle
│   │   ├── 🏷️ class ActivityIndicator
│   │   ├── 🏷️ class _ActivityIndicatorContext
│   │   └── 🏷️ class NotebookFitStopControl
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
│   ├── 📄 ascii.py
│   └── 📄 results_sidecar.py
├── 📁 project
│   ├── 📁 categories
│   │   ├── 📁 chart
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class Chart
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class ChartFactory
│   │   ├── 📁 info
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class ProjectInfo
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class ProjectInfoFactory
│   │   ├── 📁 rendering
│   │   ├── 📁 table
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class Table
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class TableFactory
│   │   ├── 📁 verbosity
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 default.py
│   │   │   │   └── 🏷️ class Verbosity
│   │   │   └── 📄 factory.py
│   │   │       └── 🏷️ class VerbosityFactory
│   │   └── 📄 __init__.py
│   ├── 📄 __init__.py
│   ├── 📄 display.py
│   │   ├── 🏷️ class PatternOptionStatus
│   │   ├── 🏷️ class ParameterDisplay
│   │   ├── 🏷️ class FitDisplay
│   │   ├── 🏷️ class PosteriorDisplay
│   │   └── 🏷️ class ProjectDisplay
│   ├── 📄 project.py
│   │   └── 🏷️ class Project
│   ├── 📄 project_config.py
│   │   └── 🏷️ class ProjectConfig
│   └── 📄 project_info.py
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
