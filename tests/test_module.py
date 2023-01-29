#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for the main module.
"""

import os
import pathlib
import unittest

import wavfile


def test_file_path(*args):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


class TestCaseWithFile(unittest.TestCase):

    def assertIsFile(self, path):
        if not pathlib.Path(path).resolve().is_file():
            raise AssertionError("File does not exist: {}".format(str(path)))


class TestModule(TestCaseWithFile):

    def test_write_error(self):
        self.assertRaises(wavfile.WriteError, wavfile.open, test_file_path('junk.wav'), 'w', fmt=b'junk')

    def test_mode_error(self):
        self.assertRaises(wavfile.Error, wavfile.open, test_file_path('junk.wav'), 'j')

    def test_read_error(self):
        self.assertRaises(wavfile.Error, wavfile.read, test_file_path('osc_tri.wav'), fmt='junk')

    def test_split(self):
        wavfile.split(test_file_path('test-file-3.wav'))
        filenames = [
            'test-file-3_00.wav',
            'test-file-3_01.wav',
            'test-file-3_02.wav',
            'test-file-3_03.wav',
            'test-file-3_04.wav'
        ]
        for f in filenames:
            self.assertIsFile(test_file_path(f))
            os.remove(test_file_path(f))

    def test_metadata(self):
        metadata = {
            'artist': 'Testy McTestface',
            'track': 'test_metadata',
            'album': 'test suite',
            'date': 'today',
            'track_number': 99,
            'comment': 'Test',
            'genre': 'testing'
        }
        filename = 'tmp.wav'
        wavfile.write(
            filename,
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [-2, -2, -2, -2],
                [3, 3, 3, 3],
            ],
            48000,
            24,
            metadata=metadata
        )
        with wavfile.open(filename) as wf:
            self.assertDictEqual(metadata, wf.metadata)

    def test_repr(self):
        with wavfile.open(test_file_path('osc_tri.wav'), 'r') as wfp:
            self.assertEqual(repr(wfp), f'WavRead("{test_file_path("osc_tri.wav")}")')
        with wavfile.open(test_file_path('tmp.wav'), 'w') as wfp:
            self.assertEqual(repr(wfp), f'WavWrite("{test_file_path("tmp.wav")}", ' +
                             'sample_rate=44100, num_channels=0, bits_per_sample=16, ' +
                             'fmt=WavFormat.PCM)')

    def test_join(self):
        files = (
            test_file_path('test-file-1.wav'),
            test_file_path('osc_tri.wav')
        )
        filename = 'join-tmp.wav'
        wavfile.join(test_file_path(filename), *files)
        self.assertIsFile(test_file_path(filename))
        with wavfile.open(test_file_path(filename), 'r') as wfp:
            self.assertEqual(wfp.num_channels, 3)

    def test_join_mismatch_fs(self):
        files = (
            test_file_path('test-file-2.wav'),
            test_file_path('osc_tri.wav')
        )
        filename = 'join-tmp.wav'
        self.assertRaises(wavfile.exception.ReadError, wavfile.join, filename, *files)
