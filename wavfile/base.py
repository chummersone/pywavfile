#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main API for reading and writing wav files.
"""

import builtins
import os
from abc import ABC

from . import chunk


class Wavfile(ABC):
    """Abstract base class for wave file read/write"""

    def __init__(self):
        """
        Initialise the base class.
        """
        self.fp = None
        self._should_close_file = False
        self._riff_chunk = None
        self._data_chunk = None

    def _init_fp(self, f, mode):
        """
        Initialise the file pointer.
        """
        # open the file
        if isinstance(f, (str, os.PathLike)):
            self.fp = builtins.open(f, mode)
            self._should_close_file = True
        else:
            self.fp = f

    def _convert_unsigned_int_to_float(self, x):
        """
        Convert unsigned int to float [-1, 1).
        """
        adjust = 2.0 ** (self.bits_per_sample - 1.0)
        return (x - adjust) / adjust

    def _convert_signed_int_to_float(self, x):
        """
        Convert signed int to float [-1, 1).
        """
        return x / (2.0 ** (self.bits_per_sample - 1.0))

    def _convert_float_to_unsigned_int(self, x):
        """
        Convert float [-1, 1) to unsigned int.
        """
        return int(round(((x + 1.0) / 2.0) * (2.0 ** self.bits_per_sample)))

    def _convert_float_to_signed_int(self, x):
        """
        Convert float [-1, 1) to signed int.
        """
        return int(round(x * (2.0 ** (self.bits_per_sample - 1.0))))

    @property
    def _bytes_per_sample(self):
        """Number of bytes per audio sample"""
        return self._data_chunk.fmt_chunk.bytes_per_sample

    @property
    def num_channels(self):
        """Number of audio channels in the file"""
        return self._data_chunk.fmt_chunk.num_channels

    @property
    def sample_rate(self):
        """Sampling rate of the audio data"""
        return self._data_chunk.fmt_chunk.sample_rate

    @property
    def bits_per_sample(self):
        """Number of bits per audio sample"""
        return self._data_chunk.fmt_chunk.bits_per_sample

    @property
    def format(self):
        """Audio sample format"""
        return self._data_chunk.fmt_chunk.audio_fmt

    @property
    def num_frames(self):
        """Number of audio frames in the file"""
        try:
            return self._data_chunk.size // self._block_align
        except ZeroDivisionError:
            return 0

    @property
    def _block_align(self):
        """Number of audio frames in the file"""
        return self._data_chunk.fmt_chunk.block_align

    @staticmethod
    def _buffer_max_abs(data):
        """Max(Abs(X)) for an audio buffer"""
        return max([max([abs(y) for y in x]) for x in data])

    def seek(self, frame_number, whence=0):
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :type frame_number: int
        :param whence: The frame positioning mode.
        :type whence: int
        :return: The method returns the object.
        :rtype: Wavfile
        """
        self._data_chunk.seek(frame_number, whence)
        return self

    def tell(self):
        """Get the current frame number."""
        return self._data_chunk.tell()

    def close(self):
        """
        Close the wav file.
        """
        total_size = \
            self._data_chunk.size + chunk.Chunk.offset + \
            self._data_chunk.fmt_chunk.size + chunk.Chunk.offset + \
            4  # riff chunk contains four bytes indicating the format
        self._riff_chunk.size = total_size
        self._data_chunk.close()
        self._riff_chunk.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
