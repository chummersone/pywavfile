#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for writing and reading floating-point wave audio files.
"""

import unittest

import wavfile
import wavfile.chunk
import wavfile.exception

from test_module import test_file_path


class TestExceptions(unittest.TestCase):

    def test_empty_file(self):
        filename = test_file_path("empty.wav")
        self.assertRaises(wavfile.exception.Error, wavfile.open, filename, 'r')

    def test_wrong_size(self):
        filename = test_file_path("osc_tri_wrong_size.wav")
        with wavfile.open(filename, 'r') as wfp:
            self.assertRaises(IOError, wfp.read)

    def test_wrong_chunk_order(self):
        filename = test_file_path("osc_tri_wrong_chunk_order.wav")
        with open(filename, 'rb') as fp:
            self.assertRaises(wavfile.exception.ReadError, wavfile.open, fp)
