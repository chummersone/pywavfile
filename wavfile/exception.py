#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package exceptions.
"""


class Error(Exception):
    """Generic package error"""
    pass


class ReadError(Error):
    """Package file read error"""
    pass


class WriteError(Error):
    """Package file write error"""
    pass
