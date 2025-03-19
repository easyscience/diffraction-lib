import asciichartpy

class PowderMeasDataMixin:
    def show_meas_chart(self):
        """
        Display the data chart for powder diffraction experiments.
        """
        if not hasattr(self, 'datastore') or self.datastore is None:
            print("No datastore found.")
            return

        meas_data = getattr(self.datastore, 'measured_data', None)
        if not meas_data or not hasattr(meas_data, 'y'):
            print("No measured data to display.")
            return

        print(f"\nMeasured diffraction pattern for {self.id}:\n")
        pattern = meas_data['y']  # Assuming this is an array/list
        chart = asciichartpy.plot(pattern, {'height': 15})
        print(chart)