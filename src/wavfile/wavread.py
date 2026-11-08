"""
Provides the WavRead class for reading wave files.

The WavRead class is returned by wavfile.open() when opening a file in read
mode.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from typing import BinaryIO, cast

from . import base, chunk, exception


class WavRead(base.Wavfile):
    """Class for reading a wave file"""

    def __init__(self, f: str | os.PathLike[str] | BinaryIO) -> None:
        """
        Initialise the WavRead object.

        :param f: Either a path to a wave file or a pointer to an open file.
        """
        base.Wavfile.__init__(self)
        self._f = f
        self._init_fp(f)

        self._riff_chunk: chunk.RiffChunk | None = None
        self._data_chunk: chunk.WavDataChunk | None = None
        self._fmt_chunk: chunk.WavFmtChunk | None = None
        self._list_chunk: chunk.ListChunk | None = None
        self._data_offset_for_deferred: int = 0

        # read the file header
        try:
            self._init_file()
            if self.fp is None:
                raise exception.ReadError('Audio file pointer must be initialized')
            if self._data_chunk is None:
                raise exception.ReadError('Audio data chunk not initialised')
            self.fp.seek(self._data_chunk.content_start)
        except Exception:
            if self._should_close_file:
                if self.fp is not None:
                    self.fp.close()
            raise

    def __repr__(self) -> str:
        """
        Return the object representation in string format.
        """
        return f'{self.__class__.__name__}("{self.fp!r}")'

    def __parse_chunk(self, chnk: chunk.Chunk) -> None:
        """Parse the chunk."""
        if self.fp is None:
            raise exception.ReadError('Audio file pointer must be initialized')

        if chnk.chunk_id == chunk.ChunkID.RIFF_CHUNK:
            self._riff_chunk = chunk.RiffChunk(self.fp)
        elif chnk.chunk_id == chunk.ChunkID.FMT_CHUNK:
            if self._fmt_chunk is not None:
                raise exception.ReadError('Second format chunk found')
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
                self._fmt_chunk = chunk.WavFmtExtensibleChunk(self.fp)
            else:
                self._fmt_chunk = chunk.WavFmtChunk(self.fp)
        elif chnk.chunk_id == chunk.ChunkID.DATA_CHUNK:
            if self._data_chunk is not None:
                raise exception.ReadError('Second data chunk found')
            if self._fmt_chunk is None:
                self._data_offset_for_deferred = self.fp.tell()
                return
            self._data_chunk = chunk.WavDataChunk(self.fp, self._fmt_chunk)
        elif chnk.chunk_id == chunk.ChunkID.LIST_CHUNK:
            self._list_chunk = chunk.ListChunk(self.fp)

    def _init_file(self) -> None:
        """
        Read the file and initialise the object properties.
        """
        if self.fp is None:
            raise exception.ReadError('Audio file pointer must be initialized')

        self.fp.seek(0, 2)
        file_size = self.fp.tell()
        self.fp.seek(0)

        read_end = file_size

        # Read the file
        while read_end - self.fp.tell() > 0:
            chnk = chunk.Chunk(self.fp)

            # rewind to chunk start
            self.fp.seek(-chunk.Chunk.offset, 1)

            # parse the chunk
            self.__parse_chunk(chnk)

            # RIFF chunk should be the first
            if self._riff_chunk is None:
                raise exception.ReadError('RIFF chunk not found')

            # check RIFF boundary
            if self._riff_chunk is not None:
                if self._riff_chunk.size > file_size - self._riff_chunk.offset:
                    raise exception.ReadError('RIFF chunk size exceeds file size')
                if self.fp.tell() > self._riff_chunk.end:
                    raise exception.ReadError('Reading beyond the end of the RIFF chunk')

            # do not read past the end of the RIFF chunk
            read_end = self._riff_chunk.end

            # check this chunk's boundary
            if chnk.end > self._riff_chunk.end:
                raise exception.ReadError('Chunk end exceeds RIFF chunk boundary')

            # skip superfluous bytes
            if chnk.chunk_id != chunk.ChunkID.RIFF_CHUNK:
                chnk.skip()

        if self._data_offset_for_deferred != 0:
            # Data chunk parsing was deferred because it landed before the format chunk
            self.fp.seek(self._data_offset_for_deferred)
            chnk = chunk.Chunk(self.fp)
            self.fp.seek(-chunk.Chunk.offset, 1)
            self.__parse_chunk(chnk)

        if self._fmt_chunk is None:
            raise exception.ReadError('FMT chunk not found')
        if self._data_chunk is None:
            raise exception.ReadError('DATA chunk not found')

        # go to data chunk content start ready to read samples
        self.fp.seek(self._data_chunk.content_start)

    def __copy__(self) -> WavRead:
        """
        Create a shallow copy of the WavRead object.
        """
        newobj = type(self)(self._f)
        for key, value in self.__dict__.items():
            if key not in ('fp', '_riff_chunk', '_data_chunk'):
                setattr(newobj, key, value)
        if self.fp is not None and newobj.fp is not None:
            newobj.fp.seek(self.fp.tell())
        return newobj

    def _block_iterator(self, method: str, num_frames: int | None = None) -> \
            Generator[list[list[float | int]], None, None]:
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

    @base.requires_open
    def read_int(self, num_frames: int | None = None) -> list[list[int]]:
        """
        Read, at most, num_frames frames from the audio stream in integer format. The method returns
        a list of lists with dimensions `(N,C)`, where `C` is the number of audio channels. Choosing
        `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        if self._data_chunk is None:
            raise exception.ReadError('Audio data chunk must be initialised')
        audio = self._data_chunk.read_frames(num_frames)
        if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT:
            for n in range(len(audio)):
                for m in range(len(audio[n])):
                    audio[n][m] = self._convert_float_to_int(audio[n][m])
        return cast(list[list[int]], audio)

    @base.requires_open
    def iter_int(self, num_frames: int | None = None) -> Generator[list[list[int]], None, None]:
        """
        This method is equivalent to :meth:`read_int`, except that it returns a generator rather
        than a block of sample.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return cast(Generator[list[list[int]], None, None],
                    self._block_iterator('read_int', num_frames))

    @base.requires_open
    def read_float(self, num_frames: int | None = None) -> list[list[float]]:
        """
        Read, at most, num_frames frames from the audio stream in float format in the range [-1, 1).
        The method returns a list of lists with size `[N][C]`, where `C` is the number of audio
        channels. Choosing `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        if self._data_chunk is None:
            raise exception.ReadError('Audio data chunk must be initialised')
        audio = []
        if self.audio_fmt == chunk.WavFormat.IEEE_FLOAT:
            audio = self._data_chunk.read_frames(num_frames)
        elif self.audio_fmt == chunk.WavFormat.PCM:
            audio = self.read_int(num_frames)
            audio = [[self._convert_int_to_float(int(sample)) for sample in frame] for frame in audio]

        return audio

    @base.requires_open
    def iter_float(self, num_frames: int | None = None) -> \
            Generator[list[list[float]], None, None]:
        """
        This method is equivalent to :meth:`read_float`, except that it returns a generator rather
        than a block of samples.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read_float', num_frames)

    @base.requires_open
    def read(self, num_frames: int | None = None) -> list[list[int | float]]:
        """
        Read, at most, `num_frames` frames from the audio stream in its native format. The method
        returns a list of lists with dimensions `(N,C)`, where `C` is the number of audio channels.
        Choosing `N = None` or `N < 0` will read all remaining samples.

        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        if self._data_chunk is None:
            raise exception.ReadError('Audio data chunk must be initialised')
        return self._data_chunk.read_frames(num_frames)

    @base.requires_open
    def iter(self, num_frames=None) -> Generator[list[list[int | float]], None, None]:
        """
        This method is equivalent to :meth:`read`, except that it returns a generator rather than
        a block of samples.

        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read', num_frames)
