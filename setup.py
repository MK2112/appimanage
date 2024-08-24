#!/usr/bin/env python3

from setuptools import setup, find_packages

# References https://github.com/niess/python-appimage/blob/master/setup.py
setup(
    name="appimanage",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "xdg",
    ],
    entry_points={
        "console_scripts": ["appimanage=appimanage.main:main"],
    },
    author="MK2112",
    author_email="apps.mk2112@gmail.com",
    description="CLI-based integration manager for AppImages on Linux",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MK2112/appimanage",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)
