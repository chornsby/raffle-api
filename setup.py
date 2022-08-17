from setuptools import find_packages, setup

setup(
    name="raffle-api",
    version="0.0.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"console_scripts": ["raffle-cli=raffle.cli:app"]},
    package_data={"raffle": ["migrations/*.sql", "queries/*.sql"]},
)
