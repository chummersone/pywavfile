#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides test cases for the main module.
"""

import os
import pathlib
import unittest

import wavfile


def get_file_path(*args):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


def get_fixture(*args):
    return get_file_path("fixtures", *args)


class TestCaseWithFile(unittest.TestCase):

    def assertIsFile(self, path):
        if not pathlib.Path(path).resolve().is_file():
            raise AssertionError("File does not exist: {}".format(str(path)))


class TestModule(TestCaseWithFile):

    def test_write_error(self):
        self.assertRaises(wavfile.WriteError, wavfile.open, get_fixture('junk.wav'), 'w', fmt=b'junk')

    def test_mode_error(self):
        self.assertRaises(wavfile.Error, wavfile.open, get_fixture('junk.wav'), 'j')

    def test_read_error(self):
        self.assertRaises(wavfile.Error, wavfile.read, get_fixture('osc_tri.wav'), fmt='junk')

    def test_split(self):
        wavfile.split(get_fixture('test-file-3.wav'))
        filenames = [
            'test-file-3_00.wav',
            'test-file-3_01.wav',
            'test-file-3_02.wav',
            'test-file-3_03.wav',
            'test-file-3_04.wav'
        ]
        for f in filenames:
            self.assertIsFile(get_fixture(f))
            os.remove(get_fixture(f))

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
        filename = get_fixture("tmp.wav")
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
        with wavfile.open(get_fixture('osc_tri.wav'), 'r') as wfp:
            self.assertEqual(repr(wfp), f'WavRead("{get_fixture("osc_tri.wav")}")')
        with wavfile.open(get_fixture('tmp.wav'), 'w') as wfp:
            self.assertEqual(repr(wfp), f'WavWrite("{get_fixture("tmp.wav")}", ' +
                             'sample_rate=44100, num_channels=0, bits_per_sample=16, ' +
                             'fmt=WavFormat.PCM)')

    def test_join(self):
        files = (
            get_fixture('test-file-1.wav'),
            get_fixture('osc_tri.wav')
        )
        filename = 'join-tmp.wav'
        wavfile.join(get_fixture(filename), *files)
        self.assertIsFile(get_fixture(filename))
        with wavfile.open(get_fixture(filename), 'r') as wfp:
            self.assertEqual(wfp.num_channels, 3)

    def test_join_mismatch_fs(self):
        files = (
            get_fixture('test-file-2.wav'),
            get_fixture('osc_tri.wav')
        )
        filename = 'join-tmp.wav'
        self.assertRaises(wavfile.exception.ReadError, wavfile.join, filename, *files)
