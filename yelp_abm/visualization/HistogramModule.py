import os

import numpy as np

from mesa.visualization.ModularVisualization import VisualizationElement, CHART_JS_FILE


class HistogramModule(VisualizationElement):
    package_includes = [CHART_JS_FILE]
    local_includes = ["HistogramModule.js"]
    local_dir = os.path.dirname(__file__)

    def __init__(self, bins, canvas_height, canvas_width):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        new_element = "new HistogramModule({}, {}, {})"
        new_element = new_element.format(list(range(bins)), canvas_width, canvas_height)
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        num_customers_vals = [
            restaurant.num_customers for restaurant in model.restaurant_schedule.agents
        ]
        hist, bin_edges = np.histogram(num_customers_vals, bins=self.bins)
        bin_w = (max(bin_edges) - min(bin_edges)) / (len(bin_edges) - 1)
        bin_labels = np.arange(min(bin_edges) + bin_w / 2, max(bin_edges), bin_w)
        return {
            "hist": hist.tolist(),
            "bin_labels": [int(x) for x in bin_labels],
            "label": "Number of Customers",
        }
