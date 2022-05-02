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

    def __init__(self, fp, sample_rate=44100, num_channels=None, bits_per_sample=16,
                 fmt=chunk.WavFormat.PCM):
        """
        Initialise the WavWrite object.

        :param fp: Either a path to a wave file or a pointer to an open file.
        :type fp: Union[str, os.PathLike, typing.IO]
        :param sample_rate: The sample rate for the new file.
        :type sample_rate: int
        :param num_channels: The number of audio channels for the new file.
        :type num_channels: int
        :param bits_per_sample: The number of bits to encode each audio sample.
        :type bits_per_sample: int
        :param fmt: The audio format (chunk.WavFormat.PCM, chunk.WavFormat.IEEE_FLOAT)
        :type fmt: wavfile.chunk.WavFormat
        """
        base.Wavfile.__init__(self)

        self._is_open = True
        self._init_fp(fp, 'wb')

        # initialise each of the riff chunk
        self._riff_chunk = chunk.RiffChunk(self.fp)
        self._riff_chunk.format = chunk.RiffFormat.WAVE
        fmt_chunk = chunk.WavFmtChunk(self.fp)
        fmt_chunk.audio_fmt = fmt
        self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)
        self._data_chunk.fmt_chunk.sample_rate = int(sample_rate)
        if num_channels is not None:
            self._data_chunk.fmt_chunk.num_channels = int(num_channels)
        self._data_chunk.fmt_chunk.bits_per_sample = int(bits_per_sample)

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
        Write audio data to the file. The data should be a list of lists with dimensions (N,C),
        where N is the number of frames and C is the number of audio channels. The data may be int
        or float. The data may be converted if they do match the format of the destination file.

        :param audio: Audio frames to write.
        :type audio: list[list[Union[int, float]]]
        """
        if self._data_are_floats(audio) and \
                self.format == chunk.WavFormat.PCM:
            # data are floats but we are writing integers
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    if self._data_chunk.fmt_chunk.signed:
                        audio[n][m] = self._convert_float_to_signed_int(audio[n][m])
                    else:
                        audio[n][m] = self._convert_float_to_unsigned_int(audio[n][m])
        elif not self._data_are_floats(audio) and \
                self.format == chunk.WavFormat.IEEE_FLOAT:
            # data are integers but we are writing floats
            gain = 1.0 / ((2 ** (self._data_chunk.fmt_chunk.bits_per_sample - 1)) - 1)
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] *= gain

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
