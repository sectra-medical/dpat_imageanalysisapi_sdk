#!/usr/bin/env python
import os

from setuptools import find_packages, setup

__version__ = os.environ.get("VERSION", "0.1.0")


def _load_requirements(req_file: str):
    print("Requirements", req_file)
    try:
        with open(req_file, "r") as require_file:
            return require_file.read()
    except OSError:
        print(f"[WARNING] {req_file} not found, no requirements in setup.")
        return []


setup(
    name="sectra_dpat_client",
    version=__version__,
    author="Primaa",
    description="Client for Sectra DPAT server",
    install_requires=_load_requirements("requirements.txt"),
    extras_require={"dev": _load_requirements("extra_requirements.txt")},
    packages=find_packages(),
    python_requires=">=3.8",
)
