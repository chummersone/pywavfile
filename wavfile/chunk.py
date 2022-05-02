#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chunk-based helper classes for working with RIFF files.
"""

import struct
import sys
from enum import Enum

from . import exception


class RiffFormat(Enum):
    """RIFF file format"""
    WAVE = b'WAVE'


class ChunkID(Enum):
    """RIFF chunk identifiers"""
    RIFF_CHUNK = b'RIFF'
    FMT_CHUNK = b'fmt '
    DATA_CHUNK = b'data'
    UNKNOWN_CHUNK = b'    '


class WavFormat(Enum):
    """Wav audio data format"""
    PCM = 0x0001
    IEEE_FLOAT = 0x0003


class Chunk:
    """Chunk read and write"""

    align = 2
    offset = 8
    _min_size = 0

    def __init__(self, fp, bigendian=False):
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :type fp: typing.IO
        :param bigendian: Is the file bid endian?
        :type bigendian: bool
        """
        self.fp = fp
        self.bigendian = bigendian
        if not hasattr(self, 'chunk_id'):
            self.chunk_id = None
        self.size = 0
        self.start = self.fp.tell()
        self._header_is_written = False

        if 'r' in self.fp.mode:
            chunk_id = self.fp.read(4)
            try:
                self.chunk_id = ChunkID(chunk_id)
            except ValueError:
                self.chunk_id = ChunkID.UNKNOWN_CHUNK
            if len(self.chunk_id.value) > 0:
                self.size = self.read_int(4, signed=True)
        else:
            self.write_header()

    @property
    def endianness(self):
        """The endianness in text form."""
        if self.bigendian:
            return 'big'
        else:
            return 'little'

    @property
    def content_start(self):
        """The start position of the chunk content"""
        return self.start + self.offset

    def skip(self):
        """
        Skip to the end of the chunk.
        """
        if self.size == 0:
            raise exception.Error('Chunk has no payload to skip')
        self.fp.seek(self.content_start + self.size)

    def read(self, nbytes):
        """
        Read data from the chunk.

        :param nbytes: The number of bytes to read.
        :type nbytes: int
        """
        data = self.fp.read(nbytes)
        return data

    def write(self, data):
        """
        Write data to the chunk. Adjust the chunk size accordingly.
        """
        data_size = len(data)
        real_size = data_size - (self.size - (self.fp.tell() - self.content_start))
        self.size += max(real_size, 0)
        if not self._header_is_written and 'w' in self.fp.mode and not self.fp.closed:
            pos = self.fp.tell()
            self.write_header()
            self.fp.seek(pos)
        self.fp.write(data)

    def write_header(self):
        """
        Write the chunk header to the file, esp. the updated chunk size.
        """
        self.fp.seek(self.start)
        self.fp.write(self.chunk_id.value)
        self.fp.write(self.int_to_bytes(self.size, 4, signed=False))
        self._header_is_written = True

    def bytes_to_int(self, data, signed=True):
        """
        Read a signed integer from the specified number of bytes of the input
        chunk.

        :param data: Input bytes to interpret as a signed integer.
        :type data: bytes
        :param signed: Is the integer signed?
        :type signed: bool
        :return: The integer value.
        :rtype: int
        """
        # noinspection PyTypeChecker
        return int.from_bytes(data, byteorder=self.endianness, signed=signed)

    def read_int(self, nbytes, signed=True):
        """
        Read an integer from the chunk.

        :param nbytes: Number of bytes encoding the integer.
        :type nbytes: int
        :param signed: Whether the integer is signed.
        :type signed: bool
        :return: The integer value.
        :rtype: int
        """
        data = self.read(nbytes)
        if len(data) < nbytes:
            raise IOError('Could not read enough bytes. Maybe EOF.')
        return self.bytes_to_int(data, signed=signed)

    def int_to_bytes(self, data, nbytes, signed=True):
        """
        Convert an integer to bytes.

        :param data: The integer to encode.
        :type data: int
        :param nbytes: Number of bytes encoding the integer.
        :type nbytes: int
        :param signed: Whether the integer is signed.
        :type signed: bool
        :return: The bytes.
        :rtype: bytes
        """
        # noinspection PyTypeChecker
        return data.to_bytes(nbytes, byteorder=self.endianness, signed=signed)

    def write_int(self, data, nbytes, signed=True):
        """
        Write an integer to the chunk.

        :param data: The integer to encode.
        :type data: int
        :param nbytes: Number of bytes encoding the integer.
        :type nbytes: int
        :param signed: Whether the integer is signed.
        :type signed: bool
        """
        self.write(self.int_to_bytes(data, nbytes, signed=signed))

    def _get_float_struct_fmt(self, nbytes):
        """Get the format specifier for packing and unpacking floats"""

        endianness = '<' if self.endianness == 'little' else '>'
        try:
            return endianness + {
                4: 'f',
                8: 'd',
            }[nbytes]
        except KeyError:
            raise exception.Error('Cannot convert float with the specified bit depth')

    def bytes_to_float(self, data):
        """
        Read a float from the specified number of bytes of the input chunk.

        :param data: Input bytes to interpret as a float.
        :type data: bytes
        :return: The float value.
        :rtype: float
        """
        return struct.unpack(self._get_float_struct_fmt(len(data)), data)[0]

    def read_float(self, nbytes):
        """
        Read a float from the chunk.

        :param nbytes: Number of bytes encoding the float.
        :type nbytes: int
        :return: The float value.
        :rtype: float
        """
        data = self.read(nbytes)

        if len(data) < nbytes:
            raise IOError('Could not read enough bytes. Maybe EOF.')
        return self.bytes_to_float(data)

    def float_to_bytes(self, data, nbytes):
        """
        Convert a float to bytes.

        :param data: The float to encode.
        :type data: float
        :param nbytes: Number of bytes encoding the float.
        :type nbytes: int
        :return: The bytes.
        :rtype: bytes
        """
        return struct.pack(self._get_float_struct_fmt(nbytes), data)

    def write_float(self, data, nbytes):
        """
        Write a float to the chunk.

        :param data: The float to encode.
        :type data: float
        :param nbytes: Number of bytes encoding the float.
        :type nbytes: int
        """
        self.write(self.float_to_bytes(data, nbytes))

    def close(self):
        """
        Close the chunk and update the header.
        """
        if self.size < self._min_size:
            raise exception.WriteError('Required data have not been written to the file')
        if 'w' in self.fp.mode and not self.fp.closed:
            self._header_is_written = False
            self.write_header()


class RiffChunk(Chunk):
    """Riff container chunk read and write"""

    _min_size = 4

    def __init__(self, fp):
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :type fp: typing.IO
        """
        self.chunk_id = ChunkID.RIFF_CHUNK
        self.format = RiffFormat.WAVE

        Chunk.__init__(self, fp, bigendian=False)

        if 'r' in self.fp.mode:
            if self.chunk_id != ChunkID.RIFF_CHUNK:
                raise exception.ReadError('Chunk is not a RIFF chunk')
            self.format = RiffFormat(self.read(4))
        else:
            self.write(RiffFormat.WAVE.value)

    def close(self):
        """
        Close the chunk and update the header.
        """
        if self.format is None:
            raise exception.WriteError('RIFF format is not set')
        Chunk.close(self)


class WavFmtChunk(Chunk):
    """Wave format chunk read and write"""

    _min_size = 16
    _audio_fmt_size = 2
    _num_channels_size = 2
    _sample_rate_size = 4
    _byte_rate_size = 4
    _block_align_size = 2
    _bits_per_sample_size = 2

    def __init__(self, fp):
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :type fp: typing.IO
        """
        self.chunk_id = ChunkID.FMT_CHUNK
        self.audio_fmt = WavFormat.PCM
        self.num_channels = 0
        self.sample_rate = 0
        self.byte_rate = 0
        self.block_align = 0
        self.bits_per_sample = 0

        Chunk.__init__(self, fp, bigendian=False)

        if 'r' in self.fp.mode:
            if self.chunk_id != ChunkID.FMT_CHUNK:
                raise exception.ReadError('Chunk is not a FMT chunk')
            self.audio_fmt = WavFormat(self.read_int(self._audio_fmt_size, signed=False))
            self.num_channels = self.read_int(self._num_channels_size, signed=False)
            self.sample_rate = self.read_int(self._sample_rate_size, signed=False)
            self.byte_rate = self.read_int(self._byte_rate_size, signed=False)
            self.block_align = self.read_int(self._block_align_size, signed=False)
            self.bits_per_sample = self.read_int(self._bits_per_sample_size, signed=False)
        else:
            self.write_fmt()

    @property
    def bytes_per_sample(self):
        """Number of bytes per audio sample"""
        return self.bits_per_sample // 8

    @property
    def signed(self):
        """Whether the integer representation is signed"""
        return self.bytes_per_sample > 1

    def write_fmt(self):
        """
        Write the format data to the file.
        """
        self.fp.seek(self.content_start)
        self.write_int(self.audio_fmt.value, self._audio_fmt_size, signed=False)
        self.write_int(self.num_channels, self._num_channels_size, signed=False)
        self.write_int(self.sample_rate, self._sample_rate_size, signed=False)
        self.write_int(self.byte_rate, self._byte_rate_size, signed=False)
        self.write_int(self.block_align, self._block_align_size, signed=False)
        self.write_int(self.bits_per_sample, self._bits_per_sample_size, signed=False)

    def close(self):
        """
        Close the chunk and update the header and format data.
        """
        if 'w' in self.fp.mode and not self.fp.closed:
            self.write_fmt()
        Chunk.close(self)


class WavDataChunk(Chunk):
    """Wave data chunk read and write"""

    def __init__(self, fp, fmt_chunk):
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :type fp: typing.IO
        :param fmt_chunk: The associated format chunk.
        :type fmt_chunk: WavFmtChunk
        """
        self.chunk_id = ChunkID.DATA_CHUNK
        Chunk.__init__(self, fp, bigendian=False)

        self.__did_warn = False
        self.fmt_chunk = fmt_chunk

        if 'r' in self.fp.mode:
            if self.chunk_id != ChunkID.DATA_CHUNK:
                raise exception.ReadError('Chunk is not a DATA chunk')

    @property
    def num_frames(self):
        """Number of audio frames in the file"""
        try:
            return self.size // self.fmt_chunk.block_align
        except ZeroDivisionError:
            return 0

    def close(self):
        """
        Close the chunk and update the header and format data.
        """
        self.fmt_chunk.close()
        Chunk.close(self)

    def read_sample(self):
        """
        Read a sample from the chunk.
        """
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            return self.read_int(self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return self.read_float(self.fmt_chunk.bytes_per_sample)

    def read_frames(self, nframes=None):
        """
        Read a number of audio frames from the chunk. A frame is a collection of samples, from each
        audio channel, associated with a single time instant.

        :param nframes: Number of audio frames to read.
        :type nframes: int
        :return: The audio frames as a list of lists.
        :rtype: list[list[Union[int, float]]]
        """

        if nframes is None or nframes < 0:
            # read all remaining frames
            nframes = self.num_frames

        # do not try to read past the end
        num_frames = min(nframes, self.num_frames - self.tell())

        audio = []
        for n in range(num_frames):
            frame = []
            for m in range(self.fmt_chunk.num_channels):
                frame.append(self.read_sample())
            audio.append(frame)

        return audio

    @property
    def _max_val(self):
        """Maximum value"""
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                sign_correction = 1
            else:
                sign_correction = 0
            return (2 ** (self.fmt_chunk.bits_per_sample - sign_correction)) - 1
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return 1.0

    @property
    def _min_val(self):
        """Minimum value"""
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                return -self._max_val - 1
            else:
                return 0
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return -1.0

    def __saturation_warning(self):
        """
        Print a warning to stderr about out-of-range sample values.
        """
        if not self.__did_warn:
            self.__did_warn = True
            print('Saturating one of more sample values that are out-of-range', file=sys.stderr)

    def _saturate(self, val):
        """
        Saturate out-of-range sample values.
        """
        if val > self._max_val:
            val = self._max_val
            self.__saturation_warning()
        elif val < self._min_val:
            val = self._min_val
            self.__saturation_warning()
        return val

    def write_sample(self, sample):
        """
        Write a sample to the chunk.

        :param sample: An audio sample.
        :type sample: Union[int, float]
        """
        sample = self._saturate(sample)
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            self.write_int(sample, self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            self.write_float(sample, self.fmt_chunk.bytes_per_sample)

    def write_frames(self, audio):
        """
        Write one or more frames of audio to the chunk.

        :param audio: The audio frames as a list of lists.
        :type audio: list[list[Union[int, float]]]
        """

        num_channels = len(audio[0])
        if num_channels != self.fmt_chunk.num_channels:
            if self.fmt_chunk.num_channels == 0:
                self.fmt_chunk.num_channels = num_channels
            else:
                raise exception.WriteError('Number of channels does not match the format chunk')

        if self.fmt_chunk.block_align == 0:
            self.fmt_chunk.block_align = \
                self.fmt_chunk.num_channels * self.fmt_chunk.bytes_per_sample
            self.fmt_chunk.byte_rate = self.fmt_chunk.block_align * self.fmt_chunk.sample_rate

        for n in range(len(audio)):
            for m in range(len(audio[n])):
                self.write_sample(audio[n][m])

    def seek(self, frame_number, whence=0):
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :type frame_number: int
        :param whence: The frame positioning mode.
        :type whence: int
        :return: The method returns the object.
        :rtype: WavDataChunk
        """
        if frame_number > self.num_frames:
            raise exception.Error('Frame number exceeds number of frames in file')
        relative_pos = self.content_start
        if whence == 0:
            pass
        elif whence == 1:
            relative_pos = self.fp.tell()
        elif whence == 2:
            relative_pos = self.content_start + self.size
        else:
            raise exception.Error('Invalid whence parameter')
        self.fp.seek(relative_pos + (frame_number * self.fmt_chunk.block_align))
        return self

    def tell(self):
        """
        Get the current frame number.
        """
        if self.fmt_chunk.block_align == 0:
            return 0
        else:
            return (self.fp.tell() - self.content_start) // \
                   self.fmt_chunk.block_align
