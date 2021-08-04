#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for reading a wave audio file.
"""

import copy
import unittest

import wavfile


class TestWavfileCopy(unittest.TestCase):

    filename = "test-file-1.wav"

    def test_basic_copy_read(self):
        with wavfile.open(self.filename) as wfp:
            wfc = copy.copy(wfp)
            self.assertTrue(wfc._should_close_file)
            self.assertEqual(wfp._fp.name, wfc._fp.name)
            self.assertEqual(wfp._fp.tell(), wfc._fp.tell())
            self.assertEqual(wfp.tell(), wfc.tell())
            self.assertEqual(wfp.num_channels, wfc.num_channels)
            self.assertEqual(wfp.sample_rate, wfc.sample_rate)
            self.assertEqual(wfp.bits_per_sample, wfc.bits_per_sample)
            self.assertEqual(wfp.num_frames, wfc.num_frames)
            wfc.close()

    def test_basic_copy_write(self):
        filename = 'tmp.wav'
        with wavfile.open(filename, 'w', sample_rate=44100, bits_per_sample=16) as wfp:
            wfc = copy.copy(wfp)
            self.assertTrue(wfc._should_close_file)
            self.assertEqual(wfp._fp.name, wfc._fp.name)
            self.assertEqual(wfp._fp.tell(), wfc._fp.tell())
            self.assertEqual(wfp.tell(), wfc.tell())
            wfc.close()
