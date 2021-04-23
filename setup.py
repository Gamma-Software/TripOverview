import setuptools
from pathlib import Path

ignored_dependencies = []


def get_dependencies():
    with open("requirements.txt", "r") as fh:
        requirements = fh.read()
        requirements = requirements.split('\n')
        map(lambda r: r.strip(), requirements)
        requirements = [r for r in requirements if r not in ignored_dependencies]
        return requirements


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
            "trip_overview=src.overview:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ],
    author="ValentinRudloff",
    author_email="valentin.rudloff.perso@gmail.com",
    python_requires=">=3.6",
    packages=setuptools.find_packages(),
    install_requires=get_dependencies(),
    zip_safe=False,
    include_package_data=True,
    project_urls={
        "Site prototype": "https://gamma-software.github.io/",
        "Source Code": "https://github.com/Gamma-Software/TripOverview",
    }
)
