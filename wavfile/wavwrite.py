#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavWrite class for writing wave files.

The WavWrite class is returned by wavfile.open() when opening a file in write
mode.
"""

from . import base
from . import chunk


class WavWrite(base.Wavfile):
    """Class for writing a wave file"""

    def __init__(self, fp, sample_rate=44100, num_channels=None, bits_per_sample=16):
        """
        Initialise the WavWrite object.
        :param fp: Either a path to a wave file or a pointer to an open file.
        :param sample_rate: The sample rate for the new file.
        :param num_channels: The number of audio channels for the new file. If
        unspecified, the parameter will be determined from the first block of
        samples.
        :param bits_per_sample: The number of bits to encode each audio sample.
        """
        base.Wavfile.__init__(self)

        self._is_open = True
        self._init_fp(fp, 'wb')

        # initialise each of the riff chunk
        self._riff_chunk = chunk.RiffChunk(self.fp)
        self._riff_chunk.format = chunk.RiffFormat.WAVE.value
        fmt_chunk = chunk.WavFmtChunk(self.fp)
        self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)
        self._data_chunk.fmt_chunk.sample_rate = sample_rate
        if num_channels is not None:
            self._data_chunk.fmt_chunk.num_channels = num_channels
        self._data_chunk.fmt_chunk.bits_per_sample = bits_per_sample

        # go to data chunk content start ready to write samples
        self.fp.seek(self._data_chunk.content_start)

    @staticmethod
    def _data_are_floats(data):
        """
        Check for any floats in data.
        """
        return any([any([isinstance(y, float) for y in x]) for x in data]) or \
            base.Wavfile._buffer_max_abs(data) <= 1.0

    def write(self, audio):
        """
        Write audio data to the file. The data should be a list of lists with
        dimensions (N,C), where N is the number of frames and C is the number of
        audio channels. The data maybe int or float. Integer data are written
        directly. Float data should be in the range [-1,1) and are converted
        automatically.
        :param audio: Audio frames to write.
        """

        if self._data_are_floats(audio):
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    if self._data_chunk.fmt_chunk.signed:
                        audio[n][m] = self._convert_float_to_signed_int(audio[n][m])
                    else:
                        audio[n][m] = self._convert_float_to_unsigned_int(audio[n][m])

        self._data_chunk.write_frames(audio)

    def close(self):
        """
        Close the file.
        """
        num_align_bytes = self._data_chunk.size % chunk.Chunk.align
        if num_align_bytes > 0:
            self._data_chunk.skip()
            self._data_chunk.write(bytearray(num_align_bytes))
        base.Wavfile.close(self)
        if self._should_close_file:
            self.fp.close()
        self._should_close_file = False
