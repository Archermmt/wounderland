import os
import shutil
from setuptools import setup, find_packages

project_name = "wounderland"

# install the package
setup(
    name=project_name,
    description="Wounderland project",
    author="mengtong",
    version="0.1.0",
    packages=find_packages(),
)

# clean up after build
for dir_name in ["build", project_name + ".egg-info", "__pycache__", "dist"]:
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
