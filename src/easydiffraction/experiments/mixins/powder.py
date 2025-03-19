from easydiffraction.utils.chart_plotter import ChartPlotter

class PowderExperimentMixin:
    def show_meas_chart(self, x_min=None, x_max=None):
        pattern = self.datastore.pattern

        if pattern.meas is None or pattern.x is None:
            print(f"No measured data available for experiment {self.id}")
            return

        import numpy as np
        print(f"pattern.x shape: {np.shape(pattern.x)}")
        print(f"pattern.meas shape: {np.shape(pattern.meas)}")

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.meas],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=f"Measured diffraction pattern for {self.id}",
            labels=['meas']
        )