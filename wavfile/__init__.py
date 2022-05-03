#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read/write wave audio files to/from lists of native Python types.

The library currently supports PCM (integer) and IEEE float formats, and supports arbitrary integer
precision, including: 16-, 24-, 32-, and 64-bit samples.

Usage: reading wave files

    f = wavfile.open(file, 'r')

where file is either a path to a wave file or a pointer to an open file. This returns a
wavfile.wavread.WavRead object with the following properties:
    num_channels    -- The number of audio channels in the stream.
    sample_rate     -- The sampling rate/frequency of the audio stream.
    bits_per_sample -- The number of bits per audio sample.
    num_frames      -- The total number of audio frames in the audio stream. A frame is a block of
                       samples, one for each channel, corresponding to a single sampling point.
    format          -- Audio sample format.

The object also has the following methods:
    read([N])        -- Read, at most, N frames from the audio stream in their unmodified native
                        format. The method returns a list of lists with size (N,C), where C is the
                        number of audio channels. Excluding N, choosing N = None or N < 0 will read
                        all remaining samples.
    read_int([N])    -- This method is identical to read() except that it returns the samples as
                        integers using the specified bit depth.
    read_float(N)    -- This method is identical to read() except that it returns the samples as
                        floats in the range [-1, 1).
    iter([N])        -- Similar to read() but used in iterator contexts to read successive groups of
                        audio frames.
    iter_int(N)      -- Similar to read_int() but used in iterator contexts to read successive
                        groups of audio frames.
    iter_float(N)    -- Similar to read_float() but used in iterator contexts to read successive
                        groups of audio frames.
    seek(N, [W])     -- Move to the Nth frame in the audio stream. The position mode can be changed
                        by setting W: 0 (default) = absolute positioning, 1 = relative to current
                        position, 2 = relative to end of last frame.
    tell()           -- Return the current frame in the audio stream.
    close()          -- Close the instance.

Alternatively, the following shortcut function is provided:

    audio, sample_rate, bits_per_sample = wavfile.read(file, fmt='int')

where fmt is 'int', 'float', or 'native'; and audio is the audio data. The function reads all audio
data in the file.

Usage: writing wave files.

    f = wavfile.open(file, 'w', sample_rate=44100, num_channels=None, bits_per_sample=16)

where sample_rate is the sampling rate for the new file, num_channels is the number of audio
channels, and bits_per_sample is the number of bits used to encode each sample. If num_channels is
unspecified it will be determined automatically from the first block of samples that are written
(see below). This returns a wavfile.wavread.WavWrite object. The object shares its properties with
the wavfile.wavread.WavRead class. The object also offers the same seek(), tell(), and close()
methods. In addition, the following methods are provided for writing audio data:
    write(N)         -- Write N frames of integers or floats to the audio file. The data should be
                        contained in a list of lists with size (N,C), where C is the number of audio
                        channels. The data may be int or float. The data may be converted if they do
                        match the format of the destination file.

Alternatively, the following shortcut function is provided:

    wavfile.write(file, audio, sample_rate=44100, bits_per_sample=16, fmt=chunk.WavFormat.PCM)

where audio is the audio data to write to the file.
"""

from . import chunk
from . import wavread
from . import wavwrite
from .exception import Error, WriteError
from .version import __VERSION__


def open(f, mode=None, sample_rate=44100, num_channels=None, bits_per_sample=16,
         fmt=chunk.WavFormat.PCM):
    """
    Open the wave file.

    If writing and ``num_channels`` is unspecified, it is determined automatically from the first
    block of samples.

    :param f: Either a path to a wave file or a pointer to an open file.
    :param mode: Open the file for reading ('r', 'rb') or writing ('w', 'wb').
    :param sample_rate: The sample rate for the new file (write only).
    :param num_channels: The number of audio channels for the new file (write only).
    :param bits_per_sample: The number of bits to encode each audio sample (write only).
    :param fmt: The audio format (write only) (chunk.WavFormat.PCM, chunk.WavFormat.IEEE_FLOAT)
    :return: Returns a wavfile.wavread.WavRead object or wavfile.wavwrite.WavWrite object.
    """
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return wavread.WavRead(f)
    elif mode in ('w', 'wb'):
        if not isinstance(fmt, chunk.WavFormat):
            raise WriteError('Invalid format')
        return wavwrite.WavWrite(f, sample_rate=sample_rate, num_channels=num_channels,
                                 bits_per_sample=bits_per_sample, fmt=fmt)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")


def read(path, fmt='int'):
    """
    Shortcut function to read a wave file. The audio can be read directly (``fmt='native'``),
    converted to integers (``fmt='int'``), or converted to floating point (``fmt='float'``).

    :param path: Path to the wave audio file.
    :param fmt: Read the file as 'int', 'float', or 'native'.
    :return: The audio data, the sample rate, and the bit depth.
    """
    with open(path, 'r') as wf:
        fs = wf.sample_rate
        bits_per_sample = wf.bits_per_sample
        fmt_methods = {
            'int': wf.read_int,
            'float': wf.read_float,
            'native': wf.read,
        }
        audio_data = None
        try:
            audio_data = fmt_methods.get(fmt)()
        except KeyError:
            Error('Unknown format. Options are: ' + ', '.join(fmt_methods.keys()))

    return audio_data, fs, bits_per_sample


def write(path, audio_data, sample_rate=44100, bits_per_sample=16, fmt=chunk.WavFormat.PCM):
    """
    Shortcut function to write a wave file. The data should be contained in a list of lists with
    size (N,C), where C is the number of audio channels. The data may be int or float. The data may
    be converted if they do match the format of the destination file.

    :param path: Path to the newly created wave file.
    :param audio_data: The data to be written to the file.
    :param sample_rate: The sample rate for the new file.
    :param bits_per_sample: The number of bits to encode each audio sample (write only).
    :param fmt: The audio format (chunk.WavFormat.PCM, chunk.WavFormat.IEEE_FLOAT)
    """
    with open(path, 'w', sample_rate=sample_rate, bits_per_sample=bits_per_sample, fmt=fmt) as wf:
        wf.write(audio_data)
