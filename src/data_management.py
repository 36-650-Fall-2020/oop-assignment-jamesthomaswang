"""These classes read data and order it into a region tree.

There are two categories of classes in this module: region classes and data
manager classes. The idea is that a tree of "regions" (country, states, and
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

import pandas as pd
from abc import ABC, abstractmethod
import functools


class Level(ABC):
    LOWER_LEVEL_CLASS = None

    @property
    @abstractmethod
    def DATA_FILE_PATH(self): pass

    def __init__(self, upper_level):
        self.upper_level = upper_level

        self.is_uppermost_level = self.upper_level is None
        self.is_lowermost_level = self.LOWER_LEVEL_CLASS is None

    def __call__(self):
        return self.data

    @functools.cached_property
    def lower_level(self):
        if self.is_lowermost_level:
            raise ValueError("This level is the lowest level.")
        return (self.LOWER_LEVEL_CLASS)(self)

    @functools.cached_property
    def data(self):
        return pd.read_csv(self.DATA_FILE_PATH,
                           parse_dates=["date"],
                           dtype={"fips": pd.StringDtype()})

    @functools.lru_cache
    def date(self, date):
        return self()[self()["date"] == date]

    @functools.lru_cache(maxsize=50)
    def set_region(self, fips):
        self.region = self.Region(self, fips)
        return self.region

    class Region():
        def __init__(self, outer, fips=None):
            self.outer = outer
            self.fips = fips

            if self.outer.is_uppermost_level:
                self.data = self.outer()
                self.subregion_data = self.outer.lower_level()
                return

            self.data = self.outer()[self.outer()["fips"] == self.fips]

            if self.data.empty:
                raise ValueError(
                    "{} is not a valid FIPS code.".format(self.fips))

            if self.outer.is_lowermost_level:
                self.subregion_data = None
                return

            self.subregion_data = self.outer.lower_level()[
                self.outer.lower_level()["fips"].str.startswith(self.fips)
            ]

        def __call__(self):
            return self.data

        def subregions(self):
            return self.subregion_data

        def date(self, date):
            return self.subregion_data[self.subregion_data['date'] == date]


class County(Level):
    DATA_FILE_PATH = "../data/us-counties.csv"


class State(Level):
    LOWER_LEVEL_CLASS = County
    DATA_FILE_PATH = "../data/us-states.csv"


class Country(Level):
    LOWER_LEVEL_CLASS = State
    DATA_FILE_PATH = "../data/us.csv"

    def __init__(self):
        super().__init__(None)
        self.set_region(0)


"""
country = Country()  # Note that country.region is automatically set
print(country().head())
print(country.region().head())
print(country.region.subregions().head())
print(country.region.date("2020-09-27").head())

states = country.lower_level
print(states().head())
states.set_region("06")
print(states.region().head())
states.set_region("42")
print(states.region().head())
print(states.region.subregions().head())
print(states.region.date("2020-09-27").head())

counties = states.lower_level
print(counties().head())
counties.set_region("42003")
print(counties.region().head())
# """
