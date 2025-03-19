import asciichartpy
import numpy as np

DEFAULT_HEIGHT = 9
DEFAULT_COLORS = {
    'meas': asciichartpy.blue,
    'calc': asciichartpy.red,
    'residual': asciichartpy.green
}

class ChartPlotter:
    def __init__(self, height=DEFAULT_HEIGHT):
        self.height = height

    def plot(self, y_values_list, x_values=None, x_min=None, x_max=None, title='', labels=None):
        """
        General-purpose plotting for one or more curves.
        """

        # Always work with a list of series
        if not isinstance(y_values_list, list) or not isinstance(y_values_list[0], (list, tuple, np.ndarray)):
            y_values_list = [y_values_list]

        # Convert to numpy arrays for easy filtering
        y_values_list = [np.array(series) for series in y_values_list]

        if x_values is not None:
            x_values = np.array(x_values)

            # Validate lengths
            for series in y_values_list:
                if len(series) != len(x_values):
                    raise ValueError(f"x_values and y_values must be the same length. x: {len(x_values)}, y: {len(series)}")

            # Apply x_min/x_max filtering
            if x_min is not None and x_max is not None:
                mask = (x_values >= x_min) & (x_values <= x_max)
                if not np.any(mask):
                    raise ValueError(f"No x values found between {x_min} and {x_max}")

                x_filtered = x_values[mask]
                filtered_series = [series[mask].tolist() for series in y_values_list]
            else:
                x_filtered = x_values
                filtered_series = [series.tolist() for series in y_values_list]

        else:
            # No x-values at all
            filtered_series = [series.tolist() for series in y_values_list]
            x_filtered = None  # Optional, in case you do x-axis ticks elsewhere

        # Configure colors
        if labels:
            colors = [DEFAULT_COLORS.get(label, None) for label in labels]
        else:
            colors = []

        config = {
            'height': self.height,
            'colors': colors
        }

        # Draw the chart
        chart = asciichartpy.plot(filtered_series, config)

        # Print title
        print(f"\n{title}")
        print(f"Displaying data from x = {x_filtered[0]} to {x_filtered[-1]} (filtered {np.sum(mask)} points)")

        # Print legends if labels are present
        if labels:
            legend_str = " | ".join([
                f"{DEFAULT_COLORS[label]}────{asciichartpy.reset} {label.capitalize()}"
                for label in labels
            ])
            print(f"Legend: {legend_str}")

        # Print chart
        print(chart)
