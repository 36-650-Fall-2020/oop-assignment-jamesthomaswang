"""An abstract class that creates, manages, and updates Plotly figures.

What does an interactive Plotly FigureWidget, as used in Jupyter Notebook,
require? It needs to be able to create a Plotly figure, trace, and layout, and
update with new data when the user changes a parameter. Additionally, it needs
to be able to register a click event callback function to react to user clicks.
This abstract function implements these requirements.
"""

from abc import ABC
import plotly.graph_objects as go
from covid_data_manager import Level


class Figure(ABC):
    def __init__(self, data_manager, traces=None, layout=None):
        self.fig = go.FigureWidget(data=traces, layout=layout)

        self._set_data(data_manager)

    def on_click(self, callback_fn, trace=None):
        if trace is None:
            trace = self.fig.data[0]
        trace.on_click(callback_fn)

    def __call__(self):
        return self.fig

    def _set_data(self, data_manager):
        if isinstance(data_manager, Level.Region.Date):
            self.date_data = data_manager
            self.date = self.date_data.filter

            self.region_data = data_manager.outer
            self.fips = self.region_data.filter
        elif isinstance(data_manager, Level.Region):
            self.region_data = data_manager
            self.fips = self.region_data.filter

        if self.fips == "":
            self.region_name = "the United States"
        elif not data_manager().empty:
            self.region_name = data_manager.state.iat[0]
            if len(self.fips) > 2:
                self.region_name = "{}, {}".format(
                    data_manager()["county"].iat[0],
                    self.region_name
                )

    def update(self, data_manager=None):
        if data_manager is not None:
            self._set_data(data_manager)
