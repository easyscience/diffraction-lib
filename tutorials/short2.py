from easydiffraction import Experiment
from easydiffraction import Experiments
from easydiffraction import Logger
from easydiffraction import Project
from easydiffraction import SampleModel
from easydiffraction import SampleModels
from easydiffraction.experiments.collections.background import LineSegmentBackground
from easydiffraction.experiments.collections.background import Point
from easydiffraction.experiments.collections.linked_phases import LinkedPhase
from easydiffraction.experiments.collections.linked_phases import LinkedPhases
from easydiffraction.sample_models.collections.atom_sites import AtomSite
from easydiffraction.sample_models.collections.atom_sites import AtomSites
from easydiffraction.sample_models.components.cell import Cell
from easydiffraction.sample_models.components.space_group import SpaceGroup

Logger.configure(mode=Logger.Mode.LOG, level=Logger.Level.DEBUG)
Logger.configure(mode=Logger.Mode.RAISE, level=Logger.Level.DEBUG)

sg = SpaceGroup()
sg.name_h_m = 'P n m a'
sg.it_coordinate_system_code = 'cab'

cell = Cell()
cell.length_a = 5.4603

site = AtomSite()
site.type_symbol = 'Si'

sites = AtomSites()
sites.add(site)

model = SampleModel(name='mdl')
model.space_group = sg
model.cell = cell
model.atom_sites = sites


print(model.parameters)

models = SampleModels()
# models.add(model)
models.add_from_cif_path('tutorials/data/lbco.cif')

print(models)
for p in models.parameters:
    print(p)
print(models.as_cif)

exp = Experiment(name='hrpt', data_path='tutorials/data/hrpt_lbco.xye')
print(exp)

linked_phases = LinkedPhases()
linked_phase = LinkedPhase(id='lbco', scale=10.0)
linked_phases.add(linked_phase)

exp.linked_phases = linked_phases

exp.instrument.setup_wavelength = 1.494
exp.instrument.calib_twotheta_offset = 0.6

exp.peak.broad_gauss_u = 0.1
exp.peak.broad_gauss_v = -0.1
exp.peak.broad_gauss_w = 0.1
exp.peak.broad_lorentz_y = 0.1

bkg = LineSegmentBackground()
point1 = Point(x=10, y=170)
point2 = Point(x=165, y=170)
bkg.add(point1)
bkg.add(point2)
# exp.background.add(bkg)
exp.background = bkg

# exp.background.add(x=10, y=170)
# exp.background.add(x=30, y=170)
# exp.background.add(x=50, y=170)
# exp.background.add(x=110, y=170)
# exp.background.add(x=165, y=170)

experiments = Experiments()
print(experiments)

experiments.add(exp)
print(experiments)
for p in experiments.parameters:
    print(p)
# print(experiments.as_cif)


proj = Project(name='PROJ')
print(proj)

proj.sample_models = models
proj.experiments = experiments


# proj.plotter.engine = 'plotly'

proj.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41)


models['lbco'].cell.length_a.free = True

models['lbco'].atom_sites['La'].b_iso.free = True
models['lbco'].atom_sites['Ba'].b_iso.free = True
models['lbco'].atom_sites['Co'].b_iso.free = True
models['lbco'].atom_sites['O'].b_iso.free = True

exp.instrument.calib_twotheta_offset.free = True

exp.peak.broad_gauss_u.free = True
exp.peak.broad_gauss_v.free = True
exp.peak.broad_gauss_w.free = True
exp.peak.broad_lorentz_y.free = True

exp.background['10'].y.free = True
exp.background['165'].y.free = True

exp.linked_phases['lbco'].scale.free = True


print('----', models['lbco'].cell.length_a.free)
proj.analysis.show_free_params()
proj.analysis.fit()

proj.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41)
