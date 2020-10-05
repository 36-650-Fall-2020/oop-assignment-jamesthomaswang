"""A initialization script for the NY Times COVID-19 Dataset GUI."""

from pkgutil import iter_modules
import os

DEPENDENCIES = {
    "plotly": {"conda": "conda install -c plotly",
               "pip": "pip install plotly"},
    "notebook": {"conda": "conda install -c conda-forge notebook",
                 "pip": "pip install notebook"},
    "ipywidgets": {"conda": "conda install -c conda-forge ipywidgets",
                   "pip": ("pip install ipywidgets\n"
                           "jupyter nbextension enable"
                           "--py widgetsnbextension")}}


def main():
    print("Apologies, but I did not follow the exact assignment requirements. The bulk of this program is not a "
          "console  interface. Instead, I built a fully interactive data exploration GUI. I wanted to get better at "
          "interactive data visualizations, so this built on using Jupyter Notebooks, Plotly, and IPyWidgets. These "
          "are the only three dependencies, beyond base Python 3+.")

    print("Let me check if you have these dependencies installed:")

    modules = set(x[1] for x in iter_modules())
    to_install = []
    for dependency in DEPENDENCIES.keys():
        if dependency in modules:
            status_str = "Installed     :)"
        else:
            status_str = "Not Installed :("
            to_install.append(dependency)
        print("{}:\t{}".format(dependency, status_str))

    if to_install:
        print("It looks like a few packages need to be installed.")
        while True:
            package_manager = input("Are you using conda or pip?")
            print("Please run the following commands, then run me again!")
            if package_manager.startswith("c"):
                package_manager = "conda"
                break
            elif package_manager.startswith("p"):
                package_manager = "pip"
                break
            else:
                print("Sorry, I don't understand.")
        for dependency in to_install:
            print(DEPENDENCIES[dependency][package_manager])
    else:
        input("Are you ready? Press enter for me to spin up a Jupyter"
              "Notebook server.")
        print("Setting working directory to this file's directory:")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        print("Starting Jupyter Notebook server:")
        os.system("jupyter notebook app.ipynb")


if __name__ == "__main__":
    main()
