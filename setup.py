import setuptools
import atexit
import os
import yaml
import platform
from shutil import copyfile
from setuptools.command.install import install
from setuptools.command.develop import develop

ignored_dependencies = []


def get_dependencies():
    with open("requirements.txt", "r") as fh:
        requirements = fh.read()
        requirements = requirements.split('\n')
        map(lambda r: r.strip(), requirements)
        requirements = [r for r in requirements if r not in ignored_dependencies]
        return requirements


def install_configuration():
    print("Configuring Trip Overview app...")
    path_to_app_data = os.path.join(os.path.expanduser("~"), ".trip_overview")
    path_to_conf = os.path.join(path_to_app_data, "configuration.yaml")
    if not os.path.exists(path_to_app_data):
        print("Create folder", path_to_app_data)
        os.makedirs(path_to_app_data)
    if not os.path.exists(path_to_conf):
        print("Create Trip Overview configuration")
        configuration = {"kilometer_source": "GPS",
                         "folium_site_output_path": ".",
                         "folium_site_output_filename": "trip_overview",
                         "database_filepath": os.path.join(path_to_app_data, "database.db")}
        with open(path_to_conf, 'w+') as file:
            documents = yaml.dump(configuration, file)
            print("Write ", configuration, " in ", path_to_conf)
    else:
        print("TripOverview configuration file already installed")


class PostDevelopCommand(develop):
    def run(self):
        develop.run(self)
        install_configuration()


class PostInstallCommand(install):
    def run(self):
        install.run(self)
        install_configuration()


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
    cmdclass={'install': PostInstallCommand,
              'develop': PostDevelopCommand},
)
