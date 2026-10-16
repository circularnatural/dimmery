"""Stamp the built package with the git commit it came from (see src/dimmery/buildinfo.py)."""

import importlib.util
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent


def _buildinfo():
    spec = importlib.util.spec_from_file_location("dimmery_buildinfo", ROOT / "src/dimmery/buildinfo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildPy(build_py):
    def run(self):
        super().run()
        info = _buildinfo().from_git(ROOT)
        if info:
            target = Path(self.build_lib) / "dimmery" / "_buildinfo.py"
            target.write_text(f"INFO = {info!r}\n")


setup(cmdclass={"build_py": BuildPy})
