#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for reading a wave audio file.
"""

import unittest

import wavfile


class TestWavfileRead(unittest.TestCase):

    filename = "osc_tri.wav"
    filename_unsigned = "osc_tri_unsigned.wav"

    def test_file_open_filename(self):
        wfp = wavfile.open(self.filename)
        self.assertEqual(wfp.sample_rate, 44100)
        wfp.close()
        self.assertTrue(wfp._fp.closed)

    def test_file_open_filename_with(self):
        with wavfile.open(self.filename) as wfp:
            fp = wfp
            self.assertEqual(wfp.sample_rate, 44100)
        self.assertTrue(fp._fp.closed)

    def test_file_open_file(self):
        with open(self.filename, "rb") as fp:
            wfp = wavfile.open(fp)
            self.assertEqual(wfp.sample_rate, 44100)
            wfp.close()

    def test_file_open_file_with(self):
        with open(self.filename, "rb") as fp:
            with wavfile.open(fp) as wfp:
                self.assertEqual(wfp.sample_rate, 44100)

    def test_file_num_channels(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.num_channels, 1)

    def test_file_read_num_channels(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(len(wfp.read_int()[0]), 1)

    def test_file_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.num_frames, 4096)

    def test_file_read_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(len(wfp.read_int()), 4096)

    def test_file_bits_per_sample(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.bits_per_sample, 16)

    def test_float_range(self):
        with wavfile.open(self.filename) as wfp:
            audio = wfp.read_float()
            max_abs = max([max([abs(y) for y in x]) for x in audio])
            self.assertTrue(max_abs < 0.7)

    def test_tell(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.tell(), 0)
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)

    def test_seek(self):
        with wavfile.open(self.filename) as wfp:
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(0)
            self.assertEqual(wfp.tell(), 0)
            wfp.seek(4096)
            self.assertEqual(wfp.tell(), 4096)

    def test_seek_whence_0(self):
        with wavfile.open(self.filename) as wfp:
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(0, 0)
            self.assertEqual(wfp.tell(), 0)
            wfp.seek(4096, 0)
            self.assertEqual(wfp.tell(), 4096)

    def test_seek_whence_1(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.tell(), 0)
            wfp.read_int()
            wfp.seek(-1, 1)
            self.assertEqual(wfp.tell(), 4095)
            wfp.seek(-4095, 1)
            self.assertEqual(wfp.tell(), 0)

    def test_seek_whence_2(self):
        with wavfile.open(self.filename) as wfp:
            wfp.seek(0, 2)
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(-4096, 2)
            self.assertEqual(wfp.tell(), 0)

    def test_read_int_blocks(self):
        with wavfile.open(self.filename) as wfp:
            num_frames = 33
            while True:
                audio = wfp.read_int(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or len(audio) == (wfp.num_frames % num_frames))

    def test_read_float_blocks(self):
        with wavfile.open(self.filename) as wfp:
            num_frames = 33
            while True:
                audio = wfp.read_float(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or len(audio) == (wfp.num_frames % num_frames))

    def test_read_short(self):
        with wavfile.open(self.filename_unsigned) as wfp:
            audio = wfp.read_int()
            for i in range(0, len(audio)):
                for j in range(0, len(audio[0])):
                    self.assertTrue(0 <= audio[i][j] < 2**8)


if __name__ == '__main__':
    unittest.main()
