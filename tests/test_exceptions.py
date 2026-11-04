"""
Provides test cases for writing and reading floating-point wave audio files.
"""

import unittest

import wavfile
import wavfile.base
import wavfile.chunk
import wavfile.exception

from test_module import get_file_path


class TestExceptions(unittest.TestCase):

    def test_empty_file(self):
        filename = get_file_path("corpus/empty.wav")
        self.assertRaises(wavfile.exception.Error, wavfile.open, filename, 'r')

    def test_wrong_size(self):
        filename = get_file_path("corpus/osc_tri_wrong_size.wav")
        self.assertRaises(wavfile.exception.ReadError, wavfile.open, filename)

    def test_riff_wrong_file_type(self):
        with open(__file__, 'rb') as fp:
            self.assertRaises(wavfile.exception.ReadError,
                              wavfile.chunk.RiffChunk, fp)

    def test_fmt_wrong_type(self):
        with open(__file__, 'rb') as fp:
            self.assertRaises(wavfile.exception.ReadError,
                              wavfile.chunk.WavFmtChunk, fp)

    def test_data_wrong_type(self):
        with open(get_file_path("corpus/osc_tri.wav"), 'rb') as fp1:
            wav = wavfile.wavread.WavRead(fp1)
        with open(__file__, 'rb') as fp2:
            self.assertRaises(wavfile.exception.ReadError,
                              wavfile.chunk.WavDataChunk,
                              fp2,
                              wav._data_chunk.fmt_chunk)

    def test_list_wrong_type(self):
        with open(__file__, 'rb') as fp:
            self.assertRaises(wavfile.exception.ReadError,
                              wavfile.chunk.ListChunk, fp)

    def test_check_audio_buffer_empty_frame(self):
        buffer = [[]]
        self.assertRaises(ValueError, wavfile.base.Wavfile.check_audio_buffer, buffer)

    def test_check_audio_buffer_inconsistent_channel_count(self):
        buffer = [[0, 0], [0], [0, 0]]
        self.assertRaises(ValueError, wavfile.base.Wavfile.check_audio_buffer, buffer)

    def test_check_audio_buffer_type(self):
        buffer = [['0', '0']]
        self.assertRaises(TypeError, wavfile.base.Wavfile.check_audio_buffer, buffer)

    def test_check_audio_buffer_inconsistent_type(self):
        buffer = [[0, 0], [0.5, 0.5]]
        self.assertRaises(TypeError, wavfile.base.Wavfile.check_audio_buffer, buffer)

    def test_check_audio_buffer_no_frames(self):
        buffer = []
        self.assertIsNone(wavfile.base.Wavfile.check_audio_buffer(buffer))

    def test_check_audio_buffer_float_frames(self):
        buffer = [[0.0, 0.0], [0.5, 0.5]]
        self.assertIs(wavfile.base.Wavfile.check_audio_buffer(buffer), float)

    def test_check_audio_buffer_int_frames(self):
        buffer = [[0, 0], [5, 5]]
        self.assertIs(wavfile.base.Wavfile.check_audio_buffer(buffer), int)
