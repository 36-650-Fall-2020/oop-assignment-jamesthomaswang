"""A class that creates, manages, and updates choropleths with varying data.

The choropleth plots show case or death rates across a set of regions on a
given day.

Choropleths seem to be the least-well-documented and least-well-supported
trace type in Plotly. I managed to figure out a relatively-optimized method
that works most of the time, but the plots still like to disappear or refuse to
update. I learned a lot about how Plotly is structured by digging through its
source code in order to figure out what is happening, however.

Choropleths have a two-step initialization:
- The `__init__()` function, which creates an empty Plotly figure
- The `update()` function, which adds the data to the figure. This can be
    called many times for every data update. For whatever reason, the figure
    will refuse to show on Jupyter Notebook unless if this is called directly
    from by the Jupyter Notebook.
"""

import plotly.graph_objects as go
from base_figure import Figure
from geojson_manager import GeoJSONManager


class Choropleth(Figure):

    def _col_info(self, col):
        if col == "cases":
            return {
                "colorscale": "Blues",
                "line_color": "rgb(8,48,107)",
                "col_text": "Number of Cases"
            }
        elif col == "deaths":
            return {
                "colorscale": "Reds",
                "line_color": "rgb(103,0,13)",
                "col_text": "Number of Deaths"
            }
        else:
            return {
                "colorscale": "Greens",
                "line_color": "rgb(0,68,27)",
                "col_text": "Undefined"
            }

    def __init__(self, data_manager, geojson_manager: GeoJSONManager,
                 col="cases"):
        self.geojson = geojson_manager
        self.col = col

        trace = {
            "locationmode": "geojson-id",
            "autocolorscale": False,
        }

        layout = {
            "title": {"text": "Building..."},
            "geo": {
                "scope": "usa",
                "projection": {"type": "albers usa"},
                "showlakes": False,
                "showland": False
            }
        }

        self.trace = go.Choropleth(trace)

        super().__init__(data_manager, self.trace, layout)

    def update(self, data_manager=None, col=None):
        super().update(data_manager)

        if col is not None:
            self.col = col

        df = self.date_data
        col_data = df()[self.col]
        col_info = self._col_info(self.col)

        trace = {
            "geojson": self.geojson.region(self.fips),
            "locations": df.fips,
            "z": col_data,
            "zmin": col_data.min(),
            "zmax": col_data.max(),
            "colorscale": col_info["colorscale"],
            "marker_line_color": col_info["line_color"],
            "colorbar_title": col_info["col_text"]
        }

        layout = {
            "title": {"text": ("{} in {}<br>"
                               "on {}<br>"
                               "<em>Click on a region to see more data.</em>"
                               ).format(
                                   col_info["col_text"],
                                   self.region_name,
                                   self.date)},
            "geo": {"fitbounds": "locations"}
        }

        # While setting `fitbounds` to `"locations"` means that the plot zooms
        # into the correct location for nearly all states, it breaks when
        # applied to Alaska. I suspect this is due to the fact that it
        # straddles the International Date Line. Therefore, when Alaska is
        # selected, the map center and zoom level needs to be set manually.
        if self.fips == "02":
            layout["geo"]["fitbounds"] = False
            layout["geo"]["center"] = {"lat": 62, "lon": -162}
            layout["geo"]["projection"] = {"scale": 4}

        self.fig.update_traces(overwrite=True,
                               selector={"type": "choropleth"},
                               **trace)
        self.fig.update_layout(**layout)

    def fips_at_idx(self, idx):
        return self.date_data.fips.iat[idx]
