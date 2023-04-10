#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavWrite class for writing wave files.

The WavWrite class is returned by wavfile.open() when opening a file in write
mode.
"""
import os
import sys
from typing import IO, List, Optional, Union

from . import base
from . import chunk
from . import exception


class WavWrite(base.Wavfile):
    """Class for writing a wave file"""

    _is_open: bool

    def __init__(self, fp: Union[str, os.PathLike, IO], sample_rate: int = 44100,
                 num_channels: Optional[int] = None, bits_per_sample: int = 16,
                 fmt: chunk.WavFormat = chunk.WavFormat.PCM) -> None:
        """
        Initialise the WavWrite object. The `fmt` argument may be any of the enumerations of
        `wavfile.chunk.WavFormat`. If `wavfile.chunk.WavFormat.EXTENSIBLE` is specified, then the
        audio data are PCM-encoded.

        :param fp: Either a path to a wave file or a pointer to an open file.
        :param sample_rate: The sample rate for the new file.
        :param num_channels: The number of audio channels for the new file.
        :param bits_per_sample: The number of bits to encode each audio sample.
        :param fmt: The audio format (:class:`wavfile.chunk.WavFormat`)
        """
        base.Wavfile.__init__(self)

        self._is_open = True
        self._init_fp(fp, 'wb')

        # initialise each of the riff chunks
        self._riff_chunk = chunk.RiffChunk(self.fp)
        if bits_per_sample > 16 or (num_channels is not None and num_channels > 2) or \
                fmt == chunk.WavFormat.EXTENSIBLE:
            fmt_chunk = chunk.WavFmtExtensibleChunk(self.fp)
            if fmt != chunk.WavFormat.EXTENSIBLE:
                fmt_chunk.sub_data_format = fmt
        else:
            fmt_chunk = chunk.WavFmtChunk(self.fp)
            fmt_chunk.audio_fmt = fmt
        self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)
        self._data_chunk.fmt_chunk.sample_rate = int(sample_rate)
        if num_channels is not None:
            self._data_chunk.fmt_chunk.num_channels = int(num_channels)
        self._data_chunk.fmt_chunk.bits_per_sample = int(bits_per_sample)
        self._list_chunk = None

        # go to data chunk content start ready to write samples
        self.fp.seek(self._data_chunk.content_start)

    def __repr__(self) -> str:
        """
        Return the object representation in string format.
        """
        return f'{self.__class__.__name__}("{self.fp.name}", sample_rate={self.sample_rate}, ' + \
               f'num_channels={self.num_channels}, bits_per_sample={self.bits_per_sample}, ' + \
               f'fmt={self.format.__class__.__name__}.{self.format.name})'

    @staticmethod
    def _data_are_floats(data: List[List[Union[int, float]]]) -> bool:
        """
        Check for any floats in data.

        data: Audio buffer to analyse for floats.
        """
        return any([any([isinstance(y, float) for y in x]) for x in data]) or \
            base.Wavfile._buffer_max_abs(data) <= 1.0

    def __check_metadata(self) -> None:
        """
        Prevent new audio data from overwriting the metadata chunk.
        """
        if self._list_chunk is not None:
            if self._list_chunk.start > self._data_chunk.start:
                raise exception.WriteError('Audio may overwrite metadata chunk')

    def write_float(self, audio: List[List[float]]) -> None:
        """
        Write float data to the file. If the file format is `PCM` then the data will be converted to
        floats, otherwise there will be no conversion.

        :param audio: Audio frames to write.
        """
        self.__check_metadata()
        if self.audio_fmt == chunk.WavFormat.PCM:
            # data are floats but we are writing integers
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_float_to_int(audio[n][m])

        self._data_chunk.write_frames(audio)

    def write_int(self, audio: List[List[int]]) -> None:
        """
        Write integer data to the file. If the file format is `IEEE_FLOAT` then the data will be
        converted to floats, otherwise there will be no conversion.

        :param audio: Audio frames to write.
        """
        self.__check_metadata()
        if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT:
            # data are integers but we are writing floats
            audio: List[List[Union[int, float]]]
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_int_to_float(audio[n][m])

        self._data_chunk.write_frames(audio)

    def write(self, audio: List[List[Union[int, float]]]) -> None:
        """
        Write audio data to the file. The data should be a list of lists with dimensions `(N,C)`,
        where `N` is the number of frames and `C` is the number of audio channels. The data may be
        ``int`` or ``float``; the method will attempt to determine the format of the data, and
        choose the appropriate scaling and conversion when writing the file.

        :param audio: Audio frames to write.
        """
        if self._data_are_floats(audio):
            self.write_float(audio)
        else:
            self.write_int(audio)

    def add_metadata(self, **kwargs: Union[str, int]) -> None:
        """
        Add metadata to the wav file. Note that this method can only be called once, and the
        metadata cannot be updated once it is written. The metadata chunk will be written before or
        after the data chunk, depending on when this method is called. Note that if the method is
        called after writing audio data, then it will not be possible to write additional audio
        data (since this may overwrite the trailing metadata chunk).

        See :class:`wavfile.chunk.InfoItem` for a list of supported tags.

        :param kwargs: The metadata to write, provided as keyword arguments.
        """

        if self._list_chunk is not None:
            raise exception.WriteError('Metadata already written to file. '
                                       'Editing is not currently supported.')

        # if the data chunk is empty, then overwrite it and recreate it after the metadata
        recreate_data_chunk = False
        if self._data_chunk.size == 0:
            # overwrite data chunk
            self.fp.seek(self._data_chunk.start)
            recreate_data_chunk = True
        else:
            # write after data
            self.fp.seek(
                self._data_chunk.content_start +
                self._data_chunk.size +
                self._data_chunk.pad
            )
        self._list_chunk = chunk.ListChunk(self.fp)
        self._list_chunk.info = kwargs
        self._list_chunk.write_info()
        if recreate_data_chunk:
            # recreate data chunk
            fmt_chunk = self._data_chunk.fmt_chunk
            self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)
        self._riff_chunk.size = self._get_total_size()
        self.fp.seek(self._data_chunk.content_start)

    def close(self) -> None:
        """Close the file."""
        num_align_bytes = self._data_chunk.size % chunk.Chunk.align
        if num_align_bytes > 0:
            self._data_chunk.skip(include_pad=False)
            self._data_chunk.write(bytearray(num_align_bytes), update_size=False)
        base.Wavfile.close(self)
        if self._should_close_file:
            self.fp.close()
        self._should_close_file = False
        if self.format != chunk.WavFormat.EXTENSIBLE and \
                self.num_channels > 2:
            print('More than two audio channels are present, but the file does not use the '
                  'EXTENSIBLE format. The file may not be readable in some software.',
                  file=sys.stderr
                  )
