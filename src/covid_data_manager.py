"""These classes read data and order it into a region tree.

What datasets do we want from the COVID-19 data? We want 3 things:
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

The two inner classes — `Region` and `Data` — had a lot of similarities, so
I pulled those out into a `Filter` abstract class. Additionally, in order to
provide for the nicest interface, the `CovidData` class provides column
selection properties, and `Level` & `Region` have convenience functions to
allow for method chaining when initializing/re-accessing inner class instances.

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

from abc import ABC, abstractmethod
import pandas as pd
from base_data_manager import Data


class CovidData(Data, ABC):
    """Provides convenience data column selection property API"""
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
    """Defines a pattern that filters outer data rows based on a column."""
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
    """Represents data at a given granularity level."""

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
        """Represents data from a region, given a granularity level."""
        FILTER_COL = "fips"

        def __init__(self, outer, fips=""):
            super().__init__(outer, fips)

        def _filter(self, fips_col, fips):
            return fips_col.str.startswith(fips)

        def date(self, date):
            """Convenience function to allow for nice method chaining."""
            return self.Date(self, date)

        class Date(Filter):
            """Represents data on a data, from a region, given a level"""
            FILTER_COL = "date"

            def __init__(self, outer, date):
                super().__init__(outer, date)
