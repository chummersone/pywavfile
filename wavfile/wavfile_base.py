#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavFile abstract class for working with wave files.

The WavFile class is the abstract base class for WavWrite and WavRead. It
provides the main API for those classes, implements common methods, and
defines a number of constants.
"""

import builtins
from abc import ABC

import wavfile


class WavFile(ABC):
    """Abstract base class for wave file read/write"""

    chunksize = 4
    endianness = 'little'

    # audio sample format
    WAVE_FORMAT_PCM = 0x0001
    valid_formats = (WAVE_FORMAT_PCM,)

    # chunk IDs
    WAVE_CHUNK_ID_RIFF = b'RIFF'
    WAVE_CHUNK_ID_WAVE = b'WAVE'
    WAVE_CHUNK_ID_FMT = b'fmt '
    WAVE_CHUNK_ID_DATA = b'data'

    def __init__(self):
        """Initialise the base class"""
        self._filesize = 0
        self._audio_fmt = 0
        self._num_channels = 0
        self._sample_rate = 0
        self._byte_rate = 0
        self._block_align = 0
        self._bits_per_sample = 0
        self._data_size = 0
        self._data_start = 0
        self._fmt_size = 0
        self._num_frames = 0
        self._fp = None
        self._should_close_file = False

    def _init_fp(self, f, mode):
        """Initialise the file pointer"""
        # open the file
        if isinstance(f, str):
            self._fp = builtins.open(f, mode)
            self._should_close_file = True
        else:
            self._fp = f

    @property
    def _bytes_per_sample(self):
        """Number of bytes per audio sample"""
        return self._block_align // self._num_channels

    @property
    def num_channels(self):
        """Number of audio channels in the file"""
        return self._num_channels

    @property
    def sample_rate(self):
        """Sampling rate of the audio data"""
        return self._sample_rate

    @property
    def bits_per_sample(self):
        """Number of bits per audio sample"""
        return self._bits_per_sample

    @property
    def num_frames(self):
        """Number of audio frames in the file"""
        return self._num_frames

    @staticmethod
    def _buffer_max_abs(data):
        """Max(Abs(X)) for an audio buffer"""
        return max([max([abs(y) for y in x]) for x in data])

    def seek(self, frame_number, whence=0):
        """
        Move to the specified frame number.
        :param frame_number: The frame number.
        :param whence: The frame positioning mode; 0 (default) = absolute positioning, 1 = relative
        to current position, 2 = relative to end of last frame.
        :return: The method returns the object.
        """
        if frame_number > self._num_frames:
            raise wavfile.Error('Frame number exceeds number of frames in file')
        relative_pos = self._data_start
        if whence == 0:
            pass
        elif whence == 1:
            relative_pos = self._fp.tell()
        elif whence == 2:
            relative_pos = self._data_start + self._data_size
        else:
            raise wavfile.Error('Invalid whence parameter')
        self._fp.seek(relative_pos + (frame_number * self._block_align))
        return self

    def tell(self):
        """Get the current frame number."""
        return (self._fp.tell() - self._data_start) // self._block_align

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
