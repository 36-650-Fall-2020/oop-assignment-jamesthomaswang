"""A class that reads and preps GeoJSON data for use in Plotly choropleths."""

from functools import lru_cache
import json
from base_data_manager import Data


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
