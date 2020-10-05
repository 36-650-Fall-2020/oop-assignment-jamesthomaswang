"""A class that creates, manages, updates coronavirus case & death line plots.

These plots show the number of cases and deaths from COVID-19 by date, in a
given region and with a given level of data granularity.
"""

import plotly.graph_objects as go
from base_figure import Figure


class LineFigure(Figure):
    def __init__(self, data_manager):
        self.traces = [
            go.Scatter(name="Cases", mode="lines",
                       line_color="rgb(8,48,107)"),
            go.Scatter(name="Deaths", mode="lines",
                       line_color="rgb(165,15,21)")]
        layout = {
            "title": {"text": "Building..."}
        }

        super().__init__(data_manager, self.traces, layout)

    def update(self, data_manager=None, col=None):
        super().update(data_manager)

        self.fig.update_traces(overwrite=True,
                               selector={"name": "Cases"},
                               x=self.region_data()["date"],
                               y=self.region_data.cases)

        self.fig.update_traces(overwrite=True,
                               selector={"name": "Deaths"},
                               x=self.region_data()["date"],
                               y=self.region_data.deaths)

        self.fig.update_layout(
            title=("Number of Cases & Deaths from COVID-19<br>"
                   "in {}<br>"
                   "<em>Click to select the date represented<br>"
                   "in the map data.</em>"
                   ).format(self.region_name),
            xaxis_title="Date",
            yaxis_title="Number of Cases/Deaths",
            hovermode="x unified"
        )
