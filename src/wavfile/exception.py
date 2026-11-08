"""
Package exceptions.
"""


class Error(Exception):
    """Generic package error"""


class ReadError(Error):
    """Package file read error"""


class WriteError(Error):
    """Package file write error"""
