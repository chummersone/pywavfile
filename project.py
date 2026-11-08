"""
wavfile project information.
"""

import datetime


class ProjectInformation:
    def __init__(
        self, name, description, author, url, email, license, classifiers, python_requires, **kwargs
    ):
        self.name = name
        self.author = author
        self.description = description
        self.url = url
        self.email = email
        self.license = license
        self.classifiers = classifiers
        self.python_requires = python_requires
        self.__dict__.update(kwargs)

    @property
    def copyright(self):
        return f"2022–{datetime.date.today().year:d}, " + self.author

    @property
    def setup_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "author": self.author,
            "author_email": self.email,
            "license": self.license,
            "classifiers": self.classifiers,
            "python_requires": self.python_requires,
        }


information = ProjectInformation(
    name="wavfile",
    description="Read/write wave audio files to/from lists of native Python types.",
    url="https://github.com/chummersone/pywavfile",
    author="Christopher Hummersone",
    email="chummersone@users.noreply.github.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
    ],
    python_requires=">= 3.10",
)
