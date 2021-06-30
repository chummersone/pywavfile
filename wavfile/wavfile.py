#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main API for reading and writing wav files.

This module provides a builtin-style open() function for reading and writing
audio files.
"""

import wavfile.wavread
import wavfile.wavwrite


class Error(Exception):
    pass


def open(f, mode=None, sample_rate=44100, num_channels=None, bits_per_sample=16):
    """
    Open the wave file.
    :param f: Either a path to a wave file or a pointer to an open file.
    :param mode: Open the file for reading ('r', 'rb') or writing ('w', 'wb').
    Modes 'r' and 'w' are identical to 'rb' and 'wb', respectively.
    :param sample_rate: The sample rate for the new file. Only applicable when
    writing an audio file.
    :param num_channels: The number of audio channels for the new file. If
    unspecified, the parameter will be determined from the first block of
    samples. Only applicable when writing an audio file.
    :param bits_per_sample: The number of bits to encode each audio sample. Only
    applicable when writing an audio file.
    :return: For reading, returns a wavfile.wavread.WavRead object; for writing,
    returns a wavfile.wavwrite.WavWrite object.
    """
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return wavfile.wavread.WavRead(f)
    elif mode in ('w', 'wb'):
        return wavfile.wavwrite.WavWrite(f, sample_rate=sample_rate, num_channels=num_channels,
                                         bits_per_sample=bits_per_sample)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")


def read(path, fmt='int'):
    """
    Shortcut function to read a wave file.
    :param path: Path to the wave audio file.
    :param fmt: Read the file as 'int' or 'float'.
    :return: The audio data, the sample rate, and the bit depth.
    """
    with wavfile.open(path, 'r') as wf:
        fs = wf.sample_rate
        bits_per_sample = wf.bits_per_sample
        fmt_methods = {
            'int': wf.read_int,
            'float': wf.read_float,
        }
        audio_data = None
        try:
            audio_data = fmt_methods.get(fmt)()
        except KeyError:
            Error('Unknown format. Options are: ' + ', '.join(fmt_methods.keys()))

    return audio_data, fs, bits_per_sample


def write(path, audio_data, sample_rate=44100, bits_per_sample=16):
    """
    Shortcut function to write a wave file.
    :param path: Path to the newly created wave file.
    :param audio_data: The data to be written to the file. The data should be
    contained in a list of lists with size (N,C), where C is the number of
    audio channels. If the data are floats then they should be in the range
    [-1, 1). They will be converted automatically. Integers will be written
    directly.
    :param sample_rate: The sample rate for the new file.
    :param bits_per_sample: The number of bits to encode each audio sample. Only
    applicable when writing an audio file.
    """
    with wavfile.open(path, 'w', sample_rate=sample_rate, bits_per_sample=bits_per_sample) as wf:
        wf.write(audio_data)
