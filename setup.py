"""Setup file for the Python package."""

from __future__ import annotations

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "bmov_to_fm2",
        [
            "src/GameState.cpp",
            "tools/bmov_to_fm2.cpp",
        ],
        include_dirs=[
            "src",
            ".",
        ],
        define_macros=[("PYBIND11", "1")],
        extra_compile_args=["-flto"],
        extra_link_args=["-luuid", "-lz"],
    ),
]

setup(cmdclass={"build_ext": build_ext}, ext_modules=ext_modules)
