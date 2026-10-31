#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavWrite class for writing wave files.

The WavWrite class is returned by wavfile.open() when opening a file in write
mode.
"""
import os
import sys
from typing import cast, IO, Sequence

from . import base
from . import chunk
from . import exception


class WavWrite(base.Wavfile):
    """Class for writing a wave file"""

    _is_open: bool

    def __init__(self, fp: str | os.PathLike | IO, sample_rate: int = 44100,
                 num_channels: int | None = None, bits_per_sample: int = 16,
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
        if self.fp is None:
            raise exception.WriteError('Failed to open audio file')

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

    def __check_metadata(self) -> None:
        """
        Prevent new audio data from overwriting the metadata chunk.
        """
        if self._list_chunk is not None:
            if self._list_chunk.start > self._data_chunk.start:
                raise exception.WriteError('Audio may overwrite metadata chunk')

    @staticmethod
    def _check_audio_buffer(audio: Sequence[Sequence[float]]) -> \
            type[int] | type[float] | None:
        """
        Validate the audio buffer layout and type.
        """
        if len(audio) == 0:
            return None

        channels = len(audio[0])

        if channels == 0:
            raise ValueError("Audio frames must contain at least one channel")

        if any(len(frame) != channels for frame in audio):
            raise ValueError("All frames must have the same number of channels")

        first = audio[0][0]
        sample_type = type(first)

        if sample_type not in (int, float):
            raise TypeError("Audio samples must be integers or floats")

        if not all(
            type(sample) is sample_type
            for frame in audio
            for sample in frame
        ):
            raise TypeError("Audio samples must be of the same type")

        return sample_type

    def __write_float(self, audio: Sequence[Sequence[float]]) -> None:
        """
        Write float data to the file.
        """
        convert = (
            self._convert_float_to_int
            if self.audio_fmt == chunk.WavFormat.PCM
            else None
        )
        self._data_chunk.write_frames(audio, convert)

    def write_float(self, audio: Sequence[Sequence[float]]) -> None:
        """
        Write float data to the file. If the file format is `PCM` then the data will be converted to
        floats, otherwise there will be no conversion.

        :param audio: Audio frames to write.
        """
        self.__check_metadata()
        sample_type = self._check_audio_buffer(audio)
        if sample_type is None:
            return
        elif sample_type is int:
            raise TypeError("Audio samples must be floats")
        self.__write_float(audio)

    def __write_int(self, audio: Sequence[Sequence[int]]) -> None:
        """
        Write integer data to the file.
        """
        convert = (
            self._convert_int_to_float
            if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT
            else None
        )
        self._data_chunk.write_frames(audio, convert)

    def write_int(self, audio: Sequence[Sequence[int]]) -> None:
        """
        Write integer data to the file. If the file format is `IEEE_FLOAT` then the data will be
        converted to floats, otherwise there will be no conversion.

        :param audio: Audio frames to write.
        """
        self.__check_metadata()
        sample_type = self._check_audio_buffer(audio)
        if sample_type is None:
            return
        elif sample_type is float:
            raise TypeError("Audio samples must be integers")
        self.__write_int(audio)

    def write(self, audio: Sequence[Sequence[int | float]]) -> None:
        """
        Write audio data to the file. The data should be a list of lists with dimensions `(N,C)`,
        where `N` is the number of frames and `C` is the number of audio channels. The data may be
        ``int`` or ``float``; the method will attempt to determine the format of the data, and
        choose the appropriate scaling and conversion when writing the file.

        :param audio: Audio frames to write.
        """
        self.__check_metadata()
        sample_type = self._check_audio_buffer(audio)
        if sample_type is None:
            return

        if sample_type is float:
            self.__write_float(audio)
        else:
            self.__write_int(cast(Sequence[Sequence[int]], audio))

    def add_metadata(self, **kwargs: str | int) -> None:
        """
        Add metadata to the wav file. Note that this method can only be called once, and the
        metadata cannot be updated once it is written. The metadata chunk will be written before or
        after the data chunk, depending on when this method is called. Note that if the method is
        called after writing audio data, then it will not be possible to write additional audio
        data (since this may overwrite the trailing metadata chunk).

        See :class:`wavfile.chunk.InfoItem` for a list of supported tags.

        :param kwargs: The metadata to write, provided as keyword arguments.
        """
        if self.fp is None:
            raise exception.WriteError('Audio file pointer must be initialized')

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
