#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for writing and reading floating-point wave audio files.
"""

import unittest

import wavfile

from test_module import test_file_path


class TestWavfileFloat(unittest.TestCase):

    def run_test(self, audio_data_in, read_callback, sample_rate,
                 bits_per_sample, num_channels, reference=None):
        filename = test_file_path("tmp.wav")
        with wavfile.open(filename, 'w',
                          sample_rate=sample_rate,
                          bits_per_sample=bits_per_sample,
                          num_channels=num_channels,
                          fmt=wavfile.chunk.WavFormat.IEEE_FLOAT) as wfp:
            wfp: wavfile.wavwrite.WavWrite
            wfp.write(audio_data_in)
            self.assertEqual(wfp.tell(), len(audio_data_in))
            # test overwriting the data
            wfp.seek(0)
            wfp.write(audio_data_in)
            self.assertEqual(wfp.tell(), len(audio_data_in))

        with wavfile.open(filename, 'r') as wfp:
            audio_out = getattr(wfp, read_callback)()

        if reference is None:
            reference = audio_data_in

        self.assertEqual(len(reference), len(audio_out))
        self.assertEqual(len(reference[0]), len(audio_out[0]))
        for i in range(0, len(audio_out)):
            for j in range(0, len(audio_out[0])):
                self.assertAlmostEqual(audio_out[i][j], reference[i][j],
                                       delta=1e-7)

        self.assertEqual(wfp.sample_rate, sample_rate)
        self.assertEqual(wfp.bits_per_sample, bits_per_sample)
        self.assertEqual(wfp.num_channels, num_channels)
        self.assertEqual(wfp.num_frames, len(reference))

    def test_read_write_audio_float_1(self):
        audio_data_in = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.0, 0.0],
            [0.5, 0.5],
            [1.0, 1.0],
        ]
        read_callback = "read"
        sample_rate = 44100
        bits_per_sample = 32
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_float_2(self):
        audio_data_in = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.1, 0.1],
            [-0.5, -0.5],
            [1.0, 1.0],
        ]
        reference = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.1, 0.1],
            [-0.5, -0.5],
            [1.0, 1.0],
        ]
        read_callback = "read_float"
        sample_rate = 44100
        bits_per_sample = 32
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]), reference)

    def test_read_write_audio_float_int(self):
        audio_data_in = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.1, 0.1],
            [-0.5, -0.5],
            [1.0, 1.0],
        ]
        reference = [
            [-2147483648, -2147483648],
            [2147483648, 2147483648],
            [214748368, 214748368],
            [-1073741824, -1073741824],
            [2147483648, 2147483648],
        ]
        read_callback = "read_int"
        sample_rate = 44100
        bits_per_sample = 32
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]), reference)

    def test_read_write_audio_int_float(self):
        audio_data_in = [
            [-2147483648, -2147483648],
            [2147483648, 2147483648],
            [214748368, 214748368],
            [-1073741824, -1073741824],
            [2147483648, 2147483648],
        ]
        reference = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.1, 0.1],
            [-0.5, -0.5],
            [1.0, 1.0],
        ]
        read_callback = "read"
        sample_rate = 44100
        bits_per_sample = 32
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]), reference)

    def test_read_write_audio_float_mono(self):
        audio_data_in = [
            [0],
            [0.1],
            [0.3],
            [-0.1],
            [-0.3],
        ]
        read_callback = "read"
        sample_rate = 32000
        bits_per_sample = 32
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_double_mono(self):
        audio_data_in = [
            [0],
            [0.1],
            [0.3],
            [-0.1],
            [-0.3],
        ]
        read_callback = "read"
        sample_rate = 32000
        bits_per_sample = 64
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_invalid_bitdepth(self):
        audio_data_in = [
            [0],
            [0.1],
            [0.3],
            [-0.1],
            [-0.3],
        ]
        with wavfile.open(test_file_path('tmp.wav'), 'w',
                          sample_rate=44100,
                          bits_per_sample=24,
                          fmt=wavfile.chunk.WavFormat.IEEE_FLOAT,
                          num_channels=len(audio_data_in[0])) as wfp:
            wfp: wavfile.wavwrite.WavWrite
            self.assertRaises(wavfile.Error, wfp.write, audio_data_in)


if __name__ == '__main__':
    unittest.main()
