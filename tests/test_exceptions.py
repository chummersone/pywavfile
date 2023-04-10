#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for writing and reading floating-point wave audio files.
"""

import unittest

import wavfile
import wavfile.chunk
import wavfile.exception

from test_module import get_file_path


class TestExceptions(unittest.TestCase):

    def test_empty_file(self):
        filename = get_file_path("empty.wav")
        self.assertRaises(wavfile.exception.Error, wavfile.open, filename, 'r')

    def test_wrong_size(self):
        filename = get_file_path("osc_tri_wrong_size.wav")
        with wavfile.open(filename, 'r') as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertRaises(IOError, wfp.read)

    def test_wrong_chunk_order(self):
        filename = get_file_path("osc_tri_wrong_chunk_order.wav")
        with open(filename, 'rb') as fp:
            self.assertRaises(wavfile.exception.ReadError, wavfile.open, fp)

    def test_riff_wrong_file_type(self):
        self.assertRaises(wavfile.exception.ReadError,
                          wavfile.chunk.RiffChunk, open(__file__, 'rb'))

    def test_fmt_wrong_type(self):
        self.assertRaises(wavfile.exception.ReadError,
                          wavfile.chunk.WavFmtChunk, open(__file__, 'rb'))

    def test_data_wrong_type(self):
        wav = wavfile.wavread.WavRead(open(get_file_path("osc_tri.wav"), 'rb'))
        self.assertRaises(wavfile.exception.ReadError,
                          wavfile.chunk.WavDataChunk,
                          open(__file__, 'rb'),
                          wav._data_chunk.fmt_chunk)

    def test_list_wrong_type(self):
        self.assertRaises(wavfile.exception.ReadError,
                          wavfile.chunk.ListChunk, open(__file__, 'rb'))
