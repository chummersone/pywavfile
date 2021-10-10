#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the WavRead class for reading wave files.

The WavRead class is returned by wavfile.open() when opening a file in read
mode.
"""

from . import base
from . import chunk
from . import exception


class WavRead(base.Wavfile):
    """Class for reading a wave file"""

    def __init__(self, f):
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

    def _init_file(self):
        """
        Read the file and initialise the object properties.
        """
        self.fp.seek(0)
        fmt_chunk = None

        # Read the file
        while True:
            chnk = chunk.Chunk(self.fp)

            if len(chnk.chunk_id) == 0:
                break

            # rewind to chunk start
            self.fp.seek(-chunk.Chunk.offset, 1)

            # interpret each chunk
            if chnk.chunk_id == chunk.ChunkID.RIFF_CHUNK.value:
                self._riff_chunk = chunk.RiffChunk(self.fp)
            elif chnk.chunk_id == chunk.ChunkID.FMT_CHUNK.value:
                fmt_chunk = chunk.WavFmtChunk(self.fp)
            elif chnk.chunk_id == chunk.ChunkID.DATA_CHUNK.value:
                if fmt_chunk is None:
                    raise exception.ReadError('DATA chunk read before FMT chunk')
                self._data_chunk = chunk.WavDataChunk(self.fp, fmt_chunk)

            # skip superfluous bytes
            if chnk.chunk_id != chunk.ChunkID.RIFF_CHUNK.value:
                chnk.skip()

        # go to data chunk content start ready to read samples
        self.fp.seek(self._data_chunk.content_start)

    def __copy__(self):
        """
        Create a shallow copy of the WavRead object.
        """
        newobj = type(self)(self.fp.name)
        newobj.__dict__.update({key: value for key, value in self.__dict__.items()
                                if key not in ('fp', '_riff_chunk', '_data_chunk')})
        newobj.fp.seek(self.fp.tell())
        return newobj

    def _block_iterator(self, method, num_frames):
        """
        Read blocks of frames using an iterator.
        """
        while True:
            audio = getattr(self, method)(num_frames=num_frames)
            if len(audio) > 0:
                yield audio
            else:
                break

    def close(self):
        """
        Close the wav file.
        """
        base.Wavfile.close(self)
        if self._should_close_file:
            self.fp.close()
        self._should_close_file = False

    def read_int(self, num_frames=None):
        """
        Read, at most, num_frames frames from the audio stream in integer
        format. The method returns a list of lists with dimensions (N,C), where
        C is the number of audio channels. Choosing N = None or N < 0 will read
        all remaining samples.
        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """

        return self._data_chunk.read_frames(num_frames)

    def iter_int(self, num_frames=None):
        """
        This method is equivalent to read_int(), except that it returns a generator rather than
        a block of sample.
        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read_int', num_frames)

    def read_float(self, num_frames=None):
        """
        Read, at most, num_frames frames from the audio stream in float format
        in the range [-1, 1). The method returns a list of lists with size
        [N][C], where C is the number of audio channels. Choosing N = None or
        N < 0 will read all remaining samples.
        :param num_frames: Maximum number of frames to read.
        :return: The audio samples as a list of lists.
        """
        audio = self.read_int(num_frames)
        if self._bytes_per_sample == 1:
            convert = self._convert_unsigned_int_to_float
        else:
            convert = self._convert_signed_int_to_float
        for i in range(0, len(audio)):
            for j in range(0, len(audio[0])):
                audio[i][j] = convert(audio[i][j])

        return audio

    def iter_float(self, num_frames=None):
        """
        This method is equivalent to read_float(), except that it returns a generator rather than
        a block of samples.
        :param num_frames: Number of frames to read on each iteration.
        :return: A generator to yield the next frame(s) of audio.
        """
        return self._block_iterator('read_float', num_frames)
