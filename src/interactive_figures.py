from functools import lru_cache
from abc import ABC
import json
import plotly.graph_objects as go
from data_management import Data, Level


class GeoJSONManager(Data):
    def __init__(self, filepath, encoding="ISO-8859-1"):
        self.filepath = filepath
        self.encoding = encoding

    def _generate_data(self):
        with open(self.filepath, encoding=self.encoding) as response:
            geo_map = json.load(response)
        # `geo_map` is a dict/list translation of a JSON file, which means that
        # it is a deep structure of dicts and lists.

        # Plotly requires each region feature dict in geo_map to have an `id`
        # key, which the geoJSON files are not using. Therefore, we have to
        # manually add these in based on the fips values.
        fips_properties = ["STATE"]
        if "COUNTY" in geo_map["features"][0]["properties"]:
            fips_properties.append("COUNTY")
        for region in geo_map["features"]:
            region["id"] = "".join([region["properties"][fips_property]
                                    for fips_property in fips_properties])
        return geo_map

    @lru_cache
    def region(self, fips_prefix):
        region_features = [feature
                           for feature in self()["features"]
                           if feature["id"].startswith(fips_prefix)]
        region_map = {key: (value
                            if key != "features"
                            else region_features)
                      for (key, value) in self().items()}
        return region_map


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
        if not isinstance(data_manager, Level.Region.Date):
            raise TypeError("Figures expect data from a specific date.")

        self.date_data = data_manager
        self.date = self.date_data.filter

        self.region_data = data_manager.outer
        self.fips = self.region_data.filter

        if self.fips == "":
            self.region_name = "the United States"
        else:
            self.region_name = data_manager.state.iat[0]

    def update(self, data_manager=None):
        if data_manager is not None:
            self._set_data(data_manager)


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

    def __init__(self, data_manager, geojson_manager, col="cases"):
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
            "title": {"text": "{} in {} on {}".format(
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
                               **trace)

        self.fig.update_layout(**layout)


"""
gjson = GeoJSONManager("../data/gz_2010_us_040_00_20m.json")
gjson()

df = Level("../data/us-states.csv").region().date("2020-09-27")
cp = Choropleth(gjson, df)
"""
