"""An abstract base class that represents a data management object.

Note that these every data management class — `Level`, `Region`, `Date`,
`GeoJSONManager` — share a few attributes:
- Each instances represents, one-to-one, a single dataset.
- They are all read-only; i.e. parameters and values cannot be changed after
    initialization. Data should never be changed by outside forces.
- The data each instance represents can be accessed by calling the instance
    like a function; e.g. `states = Level("../us-states.csv"); states()`. This
    allows for some very nice method chaining.
- The CovidData classes represent a level within a tree: `Level` > `Region` >
    `Date`. Let this implied tree be called the "data hierarchy tree".
    `GeoJSONManager` is an exception, as in that case there is no filtering or
    further analysis required beyond reading and cleaning the data.
- They are all parameter-dependent singleton classes; i.e. new instances will
    be created only if their initialization parameters are new. There is no
    point in recalculating these datasets every time they are needed, or
    reading data from a file twice. dditionally, this means that each instance
    is a unique node in the data hierarchy tree.
- They are all lazy; i.e. the data is not calculated until it is accessed for
    the first time, and nested class instances are not created until they are
    needed. This would reduce initial load time on a GUI interface.
    Additonally, this means that we create only the required branches of the
    data hierarchy tree.

Therefore, `Data` is an abstract class that implements all of this with minimal
overriding by child classes. A simple data manager class can simply define
`_generate_data()` and `__init__()` and have all the functionality listed
before.
"""

from functools import lru_cache
from abc import ABC, abstractmethod


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
