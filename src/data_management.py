import functools
from abc import ABC, abstractmethod
import pandas as pd
dr"""These classes read data and order it into a region tree.

There are two categories of classes in this module: region classes and data
manager classes. The idea is that a tree of "regions" (countries, states, and
counties), as identified by their FIPS code (ignoring country codes) is lazily
built. Each region instance contains just the data from that region, which is
pulled from the DataManager object. The structure, therefore, looks like this:

      data_manager
+----------------------+
|country_data_manager =|==============> USA             ] class Country(Region)
|                      |                 |
|                      |    +----+----+--|----------+
|                      |    |    |    |    |        |
|  state_data_manager =|==> AL   AK   AR   AZ   …   WY  ] class State(Region)
|                      |    |    /|   /|   /|       /|
|                      |    |    ……   ……   ……       ……  ┐
|                      |    |                           |
|                      |    |------------------+        | class County(Region)
|                      |    |        |         |        |
| county_data_manager =|==> Autaugna Baldwin … Winston  ┘
+----------------------+

    Typical usage example:

    data_manager = DataManager()
    country = Country(data_manager)
    pennsylvania = country.subregion("42")
    allegheny = pennsylvania.subregion("42003")
    print(country().head())
    print(pennsylvania().head())
    print(allegheny().head())
    print(pennsylvania.subregion("42003")().head())
"""


class Region(ABC):
    @property
    @abstractmethod
    def subregion_class(self):
        pass

    def __init__(self, fips, superregion):
        self._fips = fips
        self._superregion = superregion

        self.data_manager = self._superregion.data_manager
        self._data = self.data_manager(self).query("fips == @fips")

    @abstractmethod
    def is_valid_subregion_fips(self, subregion_fips):
        raise NotImplementedError

    @functools.lru_cache
    def subregion(self, subregion_fips):
        if not self.is_valid_subregion_fips(subregion_fips):
            raise ValueError("{} does not belong to a subregion of {} instance"
                             " {}.".format(subregion_fips,
                                           type(self).__name__, self._fips))
        return self.subregion_class(subregion_fips, self)

    def __call__(self):
        return self._data


class County(Region):
    subregion_class = None

    def is_valid_subregion_fips(self, subregion_fips):
        return False

    def subregion(self, subregion_fips):
        raise ValueError("Counties do not have subregions.")


class State(Region):
    subregion_class = County

    def is_valid_subregion_fips(self, subregion_fips):
        return (len(subregion_fips) == 5 and
                subregion_fips.startswith(self._fips))


class Country(Region):
    subregion_class = State

    def __init__(self, data_manager):
        self._fips = 0
        self._superregion = None

        self.data_manager = data_manager
        self._data = self.data_manager(self)

    def is_valid_subregion_fips(self, subregion_fips):
        return len(subregion_fips) == 2


class DataManager():
    class RegionDataManager():
        def __init__(self, filepath):
            self._df = pd.read_csv(filepath)

        def __call__(self):
            return self._df

    def __init__(self):
        self.region_filepaths = {Country: "../data/us.csv",
                                 State: "../data/us-states.csv",
                                 County: "../data/us-counties.csv"}
        self.region_datas = {region_class: self.RegionDataManager(filepath)
                             for (region_class, filepath)
                             in self.region_filepaths.items()}

    def __call__(self, region):
        if not isinstance(region, type):
            region = type(region)
        return self.region_datas[region]()


"""
data_manager = DataManager()
country = Country(data_manager)
pennsylvania = country.subregion("42")
allegheny = pennsylvania.subregion("42003")
print(country().head())
print(pennsylvania().head())
print(allegheny().head())
"""
