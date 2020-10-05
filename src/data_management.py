"""These classes read data and order it into a region tree.

What datasets do we want? We want 3 things:
- Given a granularity level (country, state, county), all data at that
    granularity (i.e. all state-by-state data across US, or all county-by-
    county data across the US)
- Given a granularity level and a region (as defined by a FIPS code), all data
    within that region at that granularity (i.e. all state-level data for
    Pennsylvania, or all county-level data for Pennsylvania)
- Given a granularity level, a region, and a date, all data from that date,
    within that region, at that granularity (i.e. all county-level data for
    Pennsylvania on October 1st, 2020.)

In order to implement this, we have a series of nested classes, each
representing a filter on the dataset. The outermost class is `Level`, and it
represents the data at a given granularity level (and is responsible for
reading the data files). Inside `Level` is `Region`, which represents data that
is within a region with given FIPS code, with the outer `Level`'s granularity
level. Finally, inside `Region` is `Date`, which represents data from a given
date, within `Region`'s region, and with `Level`'s granularity level.

Note that these three classes — `Level`, `Region`, `Date` — share a few
attributes:
- Their instances each represent a single dataset.
- They are all read-only; i.e. parameters and values cannot be changed after
    initialization. Data should never be changed by outside forces.
- The data each instance represents can be accessed by calling the instance
    like a function; e.g. `states = Level("../us-states.csv"); states()`. This
    is purely for convenience and aesthetics.
- They each represent a level within a tree: `Level` > `Region` > `Date`. Let
    this implied tree be called the "data hierarchy tree".
- They are all parameter-dependent singleton classes; i.e. new instances will
    be created only if their initialization parameters are new. There is no
    point in recalculating these datasets every time they are needed.
    Additionally, this means that each instance is a unique node in the data
    hierarchy tree.
- They are all lazy; i.e. the data is not calculated until it is accessed for
    the first time, and nested class instances are not created until they are
    needed. This would reduce initial load time on a GUI interface.
    Additonally, this means that we create only the required branches of the
    data hierarchy tree.

    Typical usage example:

    country = Level("../data/us.csv")
    state = Level("../data/us-states.csv")
    county = Level("../data/us-counties.csv")

    print(country())
    print(country.region().date("2020-09-27")())
    print(state.region().date("2020-09-27")())
    print(state.region("42").date("2020-09-27")())
    print(county.region("42").date("2020-09-27")())
    print(county.region("42003").date("2020-09-27")())
"""

from functools import lru_cache
from abc import ABC, abstractmethod
import pandas as pd


class Data(ABC):
    """Defines lazy, callable, read-only, parameter-based singleton pattern.

    All child classes must define a _generate_data() function. This is lazily
    called when the read-only `data` property is first accessed.

    The data can be accessed by calling the instance like a function.

    If the initialization parameters are not new, the previous instance will be
    used instead.
    """

    @lru_cache
    def __new__(cls, *args, **kwargs):
        """Implements parameter-based singletons.

        This uses (abuses) `functools.lru_cache` to memoize the `__new__()`
        magic function, called immediately before `__init__()`."""
        return super().__new__(cls)

    def __call__(self):
        """Returns the instance's dataset."""
        return self.data

    @abstractmethod
    def _generate_data(self):
        """Generates the data represented by the instance.

        Note that this must be customized by every child class.

        Returns:
            pd.DataFrame: The data represented by an instance of this class.
        """
        pass

    @property
    def data(self):
        """The instance's dataset, lazily generated."""
        if not hasattr(self, "_data"):
            self._data = self._generate_data()
        return self._data


class CovidData(Data, ABC):
    @property
    def date(self):
        return self()["date"]

    @property
    def fips(self):
        return self()["fips"]

    @property
    def cases(self):
        return self()["cases"]

    @property
    def deaths(self):
        return self()["deaths"]


class Filter(CovidData, ABC):
    """Defines pattern that filters outer data rows based on a column."""
    @property
    @abstractmethod
    def FILTER_COL(self): pass

    def __init__(self, outer, filter_value):
        self.outer = outer
        self.filter = filter_value

    def _generate_data(self):
        if self.FILTER_COL in self.outer():
            return self.outer()[
                self._filter(self.outer()[self.FILTER_COL], self.filter)
            ]
        else:
            return self.outer()

    def _filter(self, filter_col, filter_value):
        """Selects which rows to filter based on `FILTER_COL`.

        Args:
            filter_col (pd.Series): The outer class instance's `FILTER_COL`
                data column.
            filter (Any): The filter_value as given in `__init__()`.

        Returns:
            pd.Series(bool): Boolean of whether or not each row is going to be
                kept. The `Filter` class implements a reasonable default of
                `filter_col == filter_value`.
        """
        return filter_col == filter_value

    @property
    def state(self):
        return self()["state"]


class Level(CovidData):
    def __init__(self, filepath):
        self.filepath = filepath

    def _generate_data(self):
        return pd.read_csv(self.filepath,
                           parse_dates=["date"],
                           dtype={"fips": pd.StringDtype()})

    def region(self, fips=""):
        """Convenience function to allow for nice method chaining."""
        return self.Region(self, fips)

    class Region(Filter):
        FILTER_COL = "fips"

        def __init__(self, outer, fips=""):
            super().__init__(outer, fips)

        def _filter(self, fips_col, fips):
            return fips_col.str.startswith(fips)

        def date(self, date):
            """Convenience function to allow for nice method chaining."""
            return self.Date(self, date)

        class Date(Filter):
            FILTER_COL = "date"

            def __init__(self, outer, date):
                super().__init__(outer, date)
