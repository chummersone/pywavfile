#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for metadata read/write.
"""

import unittest

import wavfile

from test_module import test_file_path
from test_wavfile_write import WavfileWriteTestRunner


class TestReadMetadata(unittest.TestCase):

    def test_read(self):

        filename = test_file_path('noise_44100_24bit_w_metadata.wav')
        with wavfile.open(filename, 'r') as wfp:
            self.assertEqual('Joe Bloggs', wfp.metadata['artist'])
            self.assertEqual('Noise', wfp.metadata['track'])
            self.assertEqual('pywavfile', wfp.metadata['album'])
            self.assertEqual('This is a comment', wfp.metadata['comment'])
            self.assertEqual('postmodern', wfp.metadata['genre'])
            self.assertEqual(1, wfp.metadata['track_number'])


class TestWavfileWriteMetadata(WavfileWriteTestRunner):

    def test_metadata_pre(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 16
        metadata = {
            'artist': 'Joey',
            'track': 'test_metadata_pre',
            'album': 'test suite',
            'date': 'today',
            'track_number': 1,
            'comment': 'Short comment',
            'genre': 'chillout'
        }
        self.run_test(audio_data_in, read_callback, sample_rate, bits_per_sample,
                      len(audio_data_in[0]), metadata=metadata, metadata_mode='pre')

    def test_metadata_post(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 16
        metadata = {
            'artist': 'Wavey McWaveface',
            'track': 'test_metadata_post',
            'album': 'test suite',
            'date': 'yesterday',
            'track_number': 'one',
            'comment': 'this is a slightly longer comment',
            'genre': 'postmodern'
        }
        self.run_test(audio_data_in, read_callback, sample_rate, bits_per_sample,
                      len(audio_data_in[0]), metadata=metadata, metadata_mode='post')

    def test_metadata_rewrite(self):
        filename = test_file_path("tmp.wav")
        with wavfile.open(filename, 'w') as wfp:
            wfp: wavfile.wavwrite.WavWrite
            wfp.add_metadata(comment='test')
            self.assertRaises(wavfile.exception.WriteError, wfp.add_metadata, comment='more')

    def test_metadata_write_invalid(self):
        filename = test_file_path("tmp.wav")
        with wavfile.open(filename, 'w') as wfp:
            wfp: wavfile.wavwrite.WavWrite
            self.assertRaises(wavfile.exception.WriteError, wfp.add_metadata, invalid='test')

    def test_metadata_write_order(self):
        filename = test_file_path("tmp.wav")
        with wavfile.open(filename, 'w') as wfp:
            wfp: wavfile.wavwrite.WavWrite
            wfp.write([[0]])
            wfp.add_metadata(
                comment='Write metadata after audio',
            )
            self.assertRaises(wavfile.exception.WriteError, wfp.write, [[0]])
