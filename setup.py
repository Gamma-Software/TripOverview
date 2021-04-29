import setuptools
import atexit
import os
import platform
from shutil import copyfile
from setuptools.command.install import install

ignored_dependencies = []


def get_dependencies():
    with open("requirements.txt", "r") as fh:
        requirements = fh.read()
        requirements = requirements.split('\n')
        map(lambda r: r.strip(), requirements)
        requirements = [r for r in requirements if r not in ignored_dependencies]
        return requirements


def _post_install():
    print("Configuring Trip Overview app...")
    path_to_conf_linux = os.path.join(os.path.expanduser("~"), "/.trip_overview/configuration.yaml")
    path_to_conf_win = os.path.join(os.path.expanduser("~"), r"\.trip_overview\configuration.yaml")
    if platform.system() == "Windows":
        src = os.path.join(os.getcwd(), "data/default_configuration.yaml")
        path_to_conf = path_to_conf_linux
    else:
        src = os.path.join(os.getcwd(), r"data/default_configuration.yaml")
        path_to_conf = path_to_conf_win
    if not os.path.exists(path_to_conf):
        print("The default configuration file is not installed")
        print("Add TripOverview default, ", src, " configuration to ", path_to_conf)
        copyfile(src, path_to_conf)
    else:
        print("TripOverview configuration file already installed")


class NewInstall(install):
    def __init__(self, *args, **kwargs):
        super(NewInstall, self).__init__(*args, **kwargs)
        atexit.register(_post_install)


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trip_overview",
    version="0.0.0",
    description="Create a map in html, save gps position",
    long_description_content_type="text/markdown",
    url="https://github.com/Gamma-Software/TripOverview",
    entry_points={
        "console_scripts": [
            "trip_overview=src.overview.overview:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ],
    author="Valentin Rudloff",
    author_email="valentin.rudloff.perso@gmail.com",
    python_requires=">=3.6",
    packages=setuptools.find_packages(),
    install_requires=get_dependencies(),
    zip_safe=False,
    include_package_data=True,
    project_urls={
        "Site prototype": "https://gamma-software.github.io/",
        "Source Code": "https://github.com/Gamma-Software/TripOverview",
    },
    cmdclass={'install': NewInstall},
)
