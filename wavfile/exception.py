#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package exceptions.
"""


class Error(Exception):
    pass


class ReadError(Error):
    pass


class WriteError(Error):
    pass
