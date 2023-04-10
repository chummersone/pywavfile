#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for reading a wave audio file.
"""

import unittest

import wavfile

from test_module import get_file_path


class TestWavfileRead(unittest.TestCase):

    filename = get_file_path("osc_tri.wav")
    filename_unsigned = get_file_path("osc_tri_unsigned.wav")

    def test_file_open_filename(self):
        wfp = wavfile.open(self.filename)
        self.assertEqual(wfp.sample_rate, 44100)
        self.assertEqual(wfp.format, wavfile.chunk.WavFormat.PCM)
        wfp.close()
        self.assertTrue(wfp.fp.closed)

    def test_file_open_filename_with(self):
        with wavfile.open(self.filename) as wfp:
            fp = wfp
            self.assertEqual(wfp.sample_rate, 44100)
        self.assertTrue(fp.fp.closed)

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
            wfp: wavfile.wavread.WavRead
            self.assertEqual(len(wfp.read_int()[0]), 1)

    def test_file_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.num_frames, 4096)

    def test_file_duration(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.duration, 4096 / 44100)

    def test_file_hms(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.hms, '0:00:00.09')

    def test_file_read_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(len(wfp.read_int()), 4096)

    def test_file_bits_per_sample(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.bits_per_sample, 16)

    def test_float_range(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            audio = wfp.read_float()
            max_abs = max([max([abs(y) for y in x]) for x in audio])
            self.assertTrue(max_abs < 0.7)

    def test_tell(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.tell(), 0)
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)

    def test_seek(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(0)
            self.assertEqual(wfp.tell(), 0)
            wfp.seek(4096)
            self.assertEqual(wfp.tell(), 4096)

    def test_seek_whence_0(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(0, 0)
            self.assertEqual(wfp.tell(), 0)
            wfp.seek(4096, 0)
            self.assertEqual(wfp.tell(), 4096)

    def test_seek_whence_1(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.tell(), 0)
            wfp.read_int()
            wfp.seek(-1, 1)
            self.assertEqual(wfp.tell(), 4095)
            wfp.seek(-4095, 1)
            self.assertEqual(wfp.tell(), 0)

    def test_seek_whence_2(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            wfp.seek(0, 2)
            self.assertEqual(wfp.tell(), 4096)
            wfp.seek(-4096, 2)
            self.assertEqual(wfp.tell(), 0)

    def test_read_int_blocks(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 33
            while True:
                audio = wfp.read_int(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or
                                    len(audio) == (wfp.num_frames % num_frames))

    def test_iter_int_blocks(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 33
            buffer = wfp.iter_int(num_frames)
            for audio in buffer:
                self.assertTrue(len(audio) == num_frames or
                                len(audio) == (wfp.num_frames % num_frames))

    def test_iter_int_next(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 31
            buffer = wfp.iter_int(num_frames)
            audio = next(buffer)
            self.assertTrue(len(audio) == num_frames)

    def test_remaining(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.tell(), 0)
            wfp.read_int()
            end = wfp.read_int()
            self.assertEqual(len(end), 0)

    def test_read_float_blocks(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 33
            while True:
                audio = wfp.read_float(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or
                                    len(audio) == (wfp.num_frames % num_frames))

    def test_iter_float_blocks(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 29
            buffer = wfp.iter_float(num_frames)
            for audio in buffer:
                self.assertTrue(len(audio) == num_frames or
                                len(audio) == (wfp.num_frames % num_frames))

    def test_iter_float_next(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            num_frames = 27
            buffer = wfp.iter_float(num_frames)
            audio = next(buffer)
            self.assertTrue(len(audio) == num_frames)

    def test_iter_native_blocks(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.format, wavfile.chunk.WavFormat.PCM)
            num_frames = 29
            buffer = wfp.iter(num_frames)
            for audio in buffer:
                self.assertTrue(len(audio) == num_frames or
                                len(audio) == (wfp.num_frames % num_frames))

    def test_iter_samples(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.format, wavfile.chunk.WavFormat.PCM)
            num_frames = 1
            buffer = wfp.iter(num_frames)
            for audio in buffer:
                self.assertTrue(len(audio) == num_frames)

    def test_read_native_type(self):
        with wavfile.open(self.filename) as wfp:
            wfp: wavfile.wavread.WavRead
            self.assertEqual(wfp.format, wavfile.chunk.WavFormat.PCM)
            audio = wfp.read()
            for i in range(0, len(audio)):
                for j in range(0, len(audio[0])):
                    self.assertIsInstance(audio[i][j], int)

    def test_read_short(self):
        with wavfile.open(self.filename_unsigned) as wfp:
            wfp: wavfile.wavread.WavRead
            audio = wfp.read_int()
            for i in range(0, len(audio)):
                for j in range(0, len(audio[0])):
                    self.assertTrue(0 <= audio[i][j] < 2**8)

    def test_seek_error(self):
        with wavfile.open(self.filename) as wfp:
            self.assertRaises(wavfile.Error, wfp.seek, wfp.num_frames + 1)

    def test_whence_error(self):
        with wavfile.open(self.filename) as wfp:
            self.assertRaises(wavfile.Error, wfp.seek, 0, 3)

    def test_shortcut_read(self):
        audio_data, fs, bits_per_sample = wavfile.read(self.filename)
        self.assertEqual(44100, fs)
        self.assertEqual(16, bits_per_sample)
        self.assertEqual(4096, len(audio_data))
        self.assertEqual(1, len(audio_data[0]))

    def test_read_test_file_1(self):
        audio_data, fs, bits_per_sample = wavfile.read(get_file_path('test-file-1.wav'))
        self.assertEqual(44100, fs)
        self.assertEqual(24, bits_per_sample)
        self.assertEqual(44100 * 4, len(audio_data))
        self.assertEqual(2, len(audio_data[0]))

    def test_read_test_file_2(self):
        audio_data, fs, bits_per_sample = wavfile.read(get_file_path('test-file-2.wav'))
        self.assertEqual(96000, fs)
        self.assertEqual(32, bits_per_sample)
        self.assertEqual(96000, len(audio_data))
        self.assertEqual(1, len(audio_data[0]))

    def test_read_test_file_3(self):
        audio_data, fs, bits_per_sample = wavfile.read(get_file_path('test-file-3.wav'))
        self.assertEqual(48000, fs)
        self.assertEqual(24, bits_per_sample)
        self.assertEqual(48000, len(audio_data))
        self.assertEqual(5, len(audio_data[0]))

    def test_read_short_to_float(self):
        with wavfile.open(self.filename_unsigned) as wfp:
            wfp: wavfile.wavread.WavRead
            audio = wfp.read_float()
            for i in range(0, len(audio)):
                for j in range(0, len(audio[0])):
                    self.assertTrue(-1 <= audio[i][j] < 1)


if __name__ == '__main__':
    unittest.main()
