#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for the main module.
"""

import os
import pathlib
import unittest

import wavfile


class TestCaseWithFile(unittest.TestCase):

    def assertIsFile(self, path):
        if not pathlib.Path(path).resolve().is_file():
            raise AssertionError("File does not exist: {}".format(str(path)))


class TestModule(TestCaseWithFile):

    def test_write_error(self):
        self.assertRaises(wavfile.WriteError, wavfile.open, 'junk.wav', 'w', fmt=b'junk')

    def test_mode_error(self):
        self.assertRaises(wavfile.Error, wavfile.open, 'junk.wav', 'j')

    def test_read_error(self):
        self.assertRaises(wavfile.Error, wavfile.read, 'osc_tri.wav', fmt='junk')

    def test_split(self):
        wavfile.split('test-file-3.wav')
        filenames = [
            'test-file-3_00.wav',
            'test-file-3_01.wav',
            'test-file-3_02.wav',
            'test-file-3_03.wav',
            'test-file-3_04.wav'
        ]
        for f in filenames:
            self.assertIsFile(f)
            os.remove(f)
