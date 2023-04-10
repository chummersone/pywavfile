#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavRead class for reading wave files.

The WavRead class is returned by wavfile.open() when opening a file in read
mode.
"""

import os
from typing import Generator, IO, List, Optional, Union

from . import base
from . import chunk
from . import exception


class WavRead(base.Wavfile):
    """Class for reading a wave file"""

    def __init__(self, f: Union[str, os.PathLike, IO]) -> None:
        """
        Initialise the WavRead object.

        :param f: Either a path to a wave file or a pointer to an open file.
        """
        base.Wavfile.__init__(self)
        self._init_fp(f, 'rb')

        # read the file header
        try:
            self._init_file()
        except BaseException:
            self.close()
            raise

        self.fp.seek(self._data_chunk.content_start)

    def __repr__(self) -> str:
        """
        Return the object representation in string format.
        """
        return f'{self.__class__.__name__}("{self.fp.name}")'

    def _init_file(self) -> None:
        """
        Read the file and initialise the object properties.
        """
        self.fp.seek(0, 2)
        file_size = self.fp.tell()
        self.fp.seek(0)
        fmt_chunk = None

        # Read the file
        while file_size - self.fp.tell() > 0:
            chnk = chunk.Chunk(self.fp)

            # rewind to chunk start
            self.fp.seek(-chunk.Chunk.offset, 1)

            # interpret each chunk
            if chnk.chunk_id == chunk.ChunkID.RIFF_CHUNK:
                self._riff_chunk = chunk.RiffChunk(self.fp)
            elif chnk.chunk_id == chunk.ChunkID.FMT_CHUNK:
                # get audio format
                self.fp.seek(chunk.Chunk.offset, 1)
                audio_fmt_int = int.from_bytes(
                    self.fp.read(chunk.WavFmtChunk.audio_fmt_size),
                    signed=False,
                    byteorder='little'
                )
                audio_fmt = chunk.WavFormat(audio_fmt_int)
                self.fp.seek(-chunk.Chunk.offset - chunk.WavFmtChunk.audio_fmt_size, 1)
                if audio_fmt == chunk.WavFormat.EXTENSIBLE:
                    fmt_chunk = chunk.WavFmtExtensibleChunk(self.fp)
                else:
                    fmt_chunk = chunk.WavFmtChunk(self.fp)
            elif chnk.chunk_id == chunk.ChunkID.DATA_CHUNK:
                if fmt_chunk is None:
                    raise exception.ReadError('DATA chunk read before FMT chunk')
                self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)
            elif chnk.chunk_id == chunk.ChunkID.LIST_CHUNK:
                self._list_chunk = chunk.ListChunk(self.fp)

            # skip superfluous bytes
            if chnk.chunk_id != chunk.ChunkID.RIFF_CHUNK:
                chnk.skip()

        # go to data chunk content start ready to read samples
        self.fp.seek(self._data_chunk.content_start)

    def __copy__(self) -> 'WavRead':
        """
        Create a shallow copy of the WavRead object.
        """
        newobj = type(self)(self.fp.name)
        newobj.__dict__.update({key: value for key, value in self.__dict__.items()
                                if key not in ('fp', '_riff_chunk', '_data_chunk')})
        newobj.fp.seek(self.fp.tell())
        return newobj

    def _block_iterator(self, method: str, num_frames: int) -> \
            Generator[List[List[Union[float, int]]], None, None]:
        """
        Read blocks of frames using an iterator.

        :param method: The underlying read method.
        :param num_frames: The number of frames to read.
        """
        while True:
            audio = getattr(self, method)(num_frames=num_frames)
            if len(audio) > 0:
                yield audio
            else:
                return

    def close(self) -> None:
        """Close the wav file."""
        try:
            base.Wavfile.close(self)
        except AttributeError:
            pass
        if self._should_close_file:
            self.fp.close()
        self._should_close_file = False

    def read_int(self, num_frames: Optional[int] = None) -> List[List[int]]:
        """
        Read, at most, num_frames frames from the audio stream in integer format. The method returns
        a list of lists with dimensions `(N,C)`, where `C` is the number of audio channels. Choosing
        `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        audio = self._data_chunk.read_frames(num_frames)
        if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT:
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_float_to_int(audio[n][m])
        return audio

    def iter_int(self, num_frames: Optional[int] = None) -> Generator[List[List[int]], None, None]:
        """
        This method is equivalent to :meth:`read_int`, except that it returns a generator rather
        than a block of sample.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read_int', num_frames)

    def read_float(self, num_frames: Optional[int] = None) -> List[List[float]]:
        """
        Read, at most, num_frames frames from the audio stream in float format in the range [-1, 1).
        The method returns a list of lists with size `[N][C]`, where `C` is the number of audio
        channels. Choosing `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        audio: List[List[Union[int, float]]] = []
        if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT:
            audio = self._data_chunk.read_frames(num_frames)
        elif self.audio_fmt == chunk.WavFormat.PCM:
            audio = self.read_int(num_frames)
            audio = [[self._convert_int_to_float(sample) for sample in frame] for frame in audio]

        return audio

    def iter_float(self, num_frames: Optional[int] = None) -> \
            Generator[List[List[float]], None, None]:
        """
        This method is equivalent to :meth:`read_float`, except that it returns a generator rather
        than a block of samples.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read_float', num_frames)

    def read(self, num_frames: Optional[int] = None) -> List[List[Union[int, float]]]:
        """
        Read, at most, `num_frames` frames from the audio stream in its native format. The method
        returns a list of lists with dimensions `(N,C)`, where `C` is the number of audio channels.
        Choosing `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        return self._data_chunk.read_frames(num_frames)

    def iter(self, num_frames=None) -> Generator[List[List[Union[int, float]]], None, None]:
        """
        This method is equivalent to :meth:`read`, except that it returns a generator rather than
        a block of samples.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read', num_frames)
