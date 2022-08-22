#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavWrite class for writing wave files.

The WavWrite class is returned by wavfile.open() when opening a file in write
mode.
"""
import os
from typing import IO, List, Optional, Union

from . import base
from . import chunk


class WavWrite(base.Wavfile):
    """Class for writing a wave file"""

    _is_open: bool

    def __init__(self, fp: Union[str, os.PathLike, IO], sample_rate: int = 44100,
                 num_channels: Optional[int] = None, bits_per_sample: int = 16,
                 fmt: chunk.WavFormat = chunk.WavFormat.PCM) -> None:
        """
        Initialise the WavWrite object.

        :param fp: Either a path to a wave file or a pointer to an open file.
        :param sample_rate: The sample rate for the new file.
        :param num_channels: The number of audio channels for the new file.
        :param bits_per_sample: The number of bits to encode each audio sample.
        :param fmt: The audio format (chunk.WavFormat.PCM, chunk.WavFormat.IEEE_FLOAT)
        """
        base.Wavfile.__init__(self)

        self._is_open = True
        self._init_fp(fp, 'wb')

        # initialise each of the riff chunk
        self._riff_chunk = chunk.RiffChunk(self.fp)
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
    def _data_are_floats(data: List[List[Union[int, float]]]) -> bool:
        """
        Check for any floats in data.

        data: Audio buffer to analyse for floats.
        """
        return any([any([isinstance(y, float) for y in x]) for x in data]) or \
            base.Wavfile._buffer_max_abs(data) <= 1.0

    def write(self, audio: List[List[Union[int, float]]]) -> None:
        """
        Write audio data to the file. The data should be a list of lists with dimensions (N,C),
        where N is the number of frames and C is the number of audio channels. The data may be int
        or float. The data may be converted if they do match the format of the destination file.

        :param audio: Audio frames to write.
        """
        if self._data_are_floats(audio) and \
                self.format == chunk.WavFormat.PCM:
            # data are floats but we are writing integers
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_float_to_int(audio[n][m])
        elif not self._data_are_floats(audio) and \
                self.format == chunk.WavFormat.IEEE_FLOAT:
            # data are integers but we are writing floats
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_int_to_float(audio[n][m])

        self._data_chunk.write_frames(audio)

    def close(self) -> None:
        """Close the file."""
        num_align_bytes = self._data_chunk.size % chunk.Chunk.align
        if num_align_bytes > 0:
            self._data_chunk.skip()
            self._data_chunk.write(bytearray(num_align_bytes))
        base.Wavfile.close(self)
        if self._should_close_file:
            self.fp.close()
        self._should_close_file = False
