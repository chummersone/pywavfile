import pathlib
from setuptools import find_packages, setup

with open('src/wavfile/version.py') as f:
    __VERSION__ = ""
    exec(f.read())

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="wavfile",
    version=__VERSION__,
    description="Read/write wave audio files to/from lists of native Python types.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/chummersone/pywavfile",
    author="Christopher Hummersone",
    author_email="chummersone@users.noreply.github.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[],
    entry_points={},
)
