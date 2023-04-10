#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main API for reading and writing wav files.
"""

import builtins
import os
from abc import ABC
from typing import Any, Dict, IO, List, Optional, Tuple, Union

from . import chunk


class Wavfile(ABC):
    """Abstract base class for wave file read/write"""

    fp: Optional[IO]
    _should_close_file: bool
    _riff_chunk: Optional[chunk.RiffChunk]
    _data_chunk: Optional[chunk.WavDataChunk]

    def __init__(self) -> None:
        """
        Initialise the base class.
        """
        self.fp = None
        self._should_close_file = False
        self._riff_chunk = None
        self._data_chunk = None
        self._list_chunk = None

    def _init_fp(self, f: Union[str, os.PathLike, IO], mode: str) -> None:
        """
        Initialise the file pointer.

        :param f: A path to a file or an open file object.
        """
        # open the file
        if isinstance(f, (str, os.PathLike)):
            self.fp = builtins.open(f, mode)
            self._should_close_file = True
        else:
            self.fp = f

    def _convert_unsigned_int_to_float(self, x: int) -> float:
        """
        Convert unsigned int to float [-1, 1).

        :param x: The unsigned integer value to convert.
        :return: The float equivalent in the current range.
        """
        adjust = 2.0 ** (self.bits_per_sample - 1.0)
        return (x - adjust) / adjust

    def _convert_signed_int_to_float(self, x: int) -> float:
        """
        Convert signed int to float [-1, 1).

        :param x: The integer value to convert.
        :return: The float equivalent in the current range.
        """
        return x / (2.0 ** (self.bits_per_sample - 1.0))

    def _convert_int_to_float(self, x: int) -> float:
        """
        Convert int to float [-1, 1).

        :param x: The integer value to convert.
        :return: The float equivalent in the current range.
        """
        if self._data_chunk.fmt_chunk.signed:
            return self._convert_signed_int_to_float(x)
        else:
            return self._convert_unsigned_int_to_float(x)

    def _convert_float_to_unsigned_int(self, x: float) -> int:
        """
        Convert float [-1, 1) to unsigned int.

        :param x: The float value to convert.
        :return: The integer equivalent in the current range.
        """
        return int(round(((x + 1.0) / 2.0) * (2.0 ** self.bits_per_sample)))

    def _convert_float_to_signed_int(self, x: float) -> int:
        """
        Convert float [-1, 1) to signed int.

        :param x: The float value to convert.
        :return: The integer equivalent in the current range.
        """
        return int(round(x * (2.0 ** (self.bits_per_sample - 1.0))))

    def _convert_float_to_int(self, x: float) -> int:
        """
        Convert float [-1, 1) to int.

        :param x: The float value to convert.
        :return: The integer equivalent in the current range.
        """
        if self._data_chunk.fmt_chunk.signed:
            return self._convert_float_to_signed_int(x)
        else:
            return self._convert_float_to_unsigned_int(x)

    @property
    def _bytes_per_sample(self) -> int:
        """Number of bytes per audio sample"""
        return self._data_chunk.fmt_chunk.bytes_per_sample

    @property
    def num_channels(self) -> int:
        """Number of audio channels in the file"""
        return self._data_chunk.fmt_chunk.num_channels

    @property
    def sample_rate(self) -> int:
        """Sampling rate of the audio data"""
        return self._data_chunk.fmt_chunk.sample_rate

    @property
    def bits_per_sample(self) -> int:
        """Number of bits per audio sample"""
        return self._data_chunk.fmt_chunk.bits_per_sample

    @property
    def format(self) -> chunk.WavFormat:
        """Wave file format code"""
        return self._data_chunk.fmt_chunk.audio_fmt

    @property
    def audio_fmt(self) -> chunk.WavFormat:
        """Audio sample format"""
        return self._data_chunk.audio_fmt

    @property
    def num_frames(self) -> int:
        """Number of audio frames in the file"""
        try:
            return self._data_chunk.size // self._block_align
        except ZeroDivisionError:
            return 0

    @property
    def duration(self) -> float:
        """Duration of the file in seconds"""
        return self.num_frames / self.sample_rate

    @property
    def hms(self) -> str:
        """Duration of the file formatted as hh:mm:ss.tt"""
        m, s = divmod(self.duration, 60)
        h, m = divmod(int(m), 60)
        return '{}:{:02d}:{:05.2f}'.format(h, m, s)

    @property
    def _block_align(self) -> int:
        """Number of audio frames in the file"""
        return self._data_chunk.fmt_chunk.block_align

    @property
    def metadata(self) -> Optional[Dict[str, Union[str, int]]]:
        """Metadata from the .wav file"""
        if self._list_chunk is not None:
            return self._list_chunk.info
        return None

    @staticmethod
    def _buffer_max_abs(data: List[List[Union[float, int]]]) -> Union[float, int]:
        """
        Max(Abs(X)) for an audio buffer.

        :param data: The buffer to analyse.
        :return: The maximum absolute value.
        """
        return max([max([abs(y) for y in x]) for x in data])

    def seek(self, frame_number: int, whence: int = 0) -> 'Wavfile':
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :param whence: The frame positioning mode.
        :return: The method returns the object.
        """
        self._data_chunk.seek(frame_number, whence)
        return self

    def tell(self) -> int:
        """Get the current frame number."""
        return self._data_chunk.tell()

    def _get_total_size(self) -> int:
        """Get the total size of the file"""
        total_size = self._data_chunk.size + self._data_chunk.pad + chunk.Chunk.offset + \
            self._data_chunk.fmt_chunk.size + self._data_chunk.fmt_chunk.pad + chunk.Chunk.offset + \
            chunk.Chunk.word_size  # riff chunk contains four bytes indicating the format
        if self._list_chunk is not None:
            total_size += self._list_chunk.size + self._list_chunk.pad + chunk.Chunk.offset
        return total_size

    def close(self) -> None:
        """
        Close the wav file.
        """
        self._riff_chunk.size = self._get_total_size()
        self._data_chunk.close()
        if self._list_chunk is not None:
            self._list_chunk.close()
        self._riff_chunk.close()

    def __del__(self) -> None:
        if self._should_close_file:
            self.close()

    def __enter__(self) -> 'Wavfile':
        return self

    def __exit__(self, *args: Tuple[Any, ...]) -> None:
        self.close()
