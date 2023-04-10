#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for copying a WavRead object.
"""

import copy
import itertools
import unittest

import wavfile

from test_module import get_file_path


class TestWavReadCopy(unittest.TestCase):

    filename = get_file_path("test-file-1.wav")

    def test_basic_copy(self):
        with wavfile.open(self.filename) as wfp:
            wfc = copy.copy(wfp)
            self.assertTrue(wfc._should_close_file)
            self.assertEqual(wfp.fp.name, wfc.fp.name)
            self.assertEqual(wfp.fp.tell(), wfc.fp.tell())
            self.assertEqual(wfp.tell(), wfc.tell())
            self.assertEqual(wfp.num_channels, wfc.num_channels)
            self.assertEqual(wfp.sample_rate, wfc.sample_rate)
            self.assertEqual(wfp.bits_per_sample, wfc.bits_per_sample)
            self.assertEqual(wfp.num_frames, wfc.num_frames)
            wfc.close()

    def test_copy_content(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            wfc = copy.copy(wfp)
            num_frames = 1
            for x, y in itertools.zip_longest(wfp.iter_int(num_frames),
                                              wfc.iter_int(num_frames)):
                self.assertListEqual(x[0], y[0])
