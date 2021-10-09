#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read/write wave audio files to/from lists of native Python types.

The library is currently limited to PCM (integer) formats but supports arbitrary
precision, including 16-, 24-, 32-, and 64-bit samples.

Usage: reading wave files

    f = wavfile.open(file, 'r')

where file is either a path to a wave file or a pointer to an open file. This
returns a wavfile.wavread.WavRead object with the following properties:
    num_channels    -- The number of audio channels in the stream.
    sample_rate     -- The sampling rate/frequency of the audio stream.
    bits_per_sample -- The number of bits per audio sample.
    num_frames      -- The total number of audio frames in the audio stream. A
                       frame is a block of samples, one for each channel,
                       corresponding to a single sampling point.

The object also has the following methods:
    read_int(N)      -- Read, at most, N frames from the audio stream in their
                        unmodified integer format. The method returns a list of
                        lists with size (N,C), where C is the number of audio
                        channels. Choosing N = None or N < 0 will read all
                        remaining samples.
    read_float(N)    -- This method is identical to read_int() except that it
                        returns the samples as floats in the range [-1, 1).
    iter_int(N)      -- Similar to read_int() but used in iterator contexts to
                        read successive groups of audio frames.
    iter_float(N)    -- Similar to read_float() but used in iterator contexts
                        to read successive groups of audio frames.
    seek(N, [W])     -- Move to the Nth frame in the audio stream. The
                        position mode can be changed by setting W: 0 (default)
                        = absolute positioning, 1 = relative to current
                        position, 2 = relative to end of last frame.
    tell()           -- Return the current frame in the audio stream.
    close()          -- Close the instance.

Alternatively, the following shortcut function is provided:

    audio, sample_rate, bits_per_sample = wavfile.read(file, fmt='int')

where fmt is 'int' or 'float', and audio is the audio data. The function reads
all audio data in the file.

Usage: writing wave files.

    f = wavfile.open(file, 'w', sample_rate=44100, num_channels=None,
                     bits_per_sample=16)

where sample_rate is the sampling rate for the new file, num_channels is the
number of audio channels, and bits_per_sample is the number of bits used to
encode each sample. If num_channels is unspecified it will be determined
automatically from the first block of samples that are written (see below).
This returns a wavfile.wavread.WavWrite object. The object shares its properties
with the wavfile.wavread.WavRead class. The object also offers the same seek(),
tell(), and close() methods. In addition, the following methods are provided for
writing audio data:
    write(N)         -- Write N frames of integers or floats to the audio file.
                        The data should be contained in a list of lists with
                        size (N,C), where C is the number of audio channels. If
                        the data are floats then they should be in the range
                        [-1, 1). They will be converted automatically. Integers
                        will be written directly.

Alternatively, the following shortcut function is provided:

    wavfile.write(file, audio, sample_rate=44100, bits_per_sample=16)

where audio is the audio data to write to the file.

"""

from . import chunk
from . import wavread
from . import wavwrite
from .exception import Error
from .version import __VERSION__


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
        return wavread.WavRead(f)
    elif mode in ('w', 'wb'):
        return wavwrite.WavWrite(f, sample_rate=sample_rate, num_channels=num_channels,
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
    with open(path, 'r') as wf:
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
    with open(path, 'w', sample_rate=sample_rate, bits_per_sample=bits_per_sample) as wf:
        wf.write(audio_data)
