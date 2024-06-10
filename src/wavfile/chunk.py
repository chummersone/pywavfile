#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chunk-based helper classes for working with RIFF files.
"""

import struct
import sys
from enum import Enum, IntEnum
from types import DynamicClassAttribute
from typing import IO, List, Optional, Union, Dict
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from . import exception


class BytesEnum(Enum):
    """Enum class with bytes values"""

    @DynamicClassAttribute
    def value(self) -> bytes:
        """The value of the Enum member."""
        return self._value_


class RiffFormat(BytesEnum):
    """RIFF file format"""
    WAVE: 'RiffFormat' = b'WAVE'


class ChunkID(BytesEnum):
    """RIFF chunk identifiers"""
    RIFF_CHUNK: 'ChunkID' = b'RIFF'
    FMT_CHUNK: 'ChunkID' = b'fmt '
    DATA_CHUNK: 'ChunkID' = b'data'
    LIST_CHUNK: 'ChunkID' = b'LIST'
    UNKNOWN_CHUNK: 'ChunkID' = b'    '


class WavFormat(IntEnum):
    """Wav audio data format"""
    PCM: 'WavFormat' = 0x0001
    IEEE_FLOAT: 'WavFormat' = 0x0003
    EXTENSIBLE: 'WavFormat' = 0xFFFE


class ListType(BytesEnum):
    """LIST chunk list types"""
    INFO: 'ListType' = b'INFO'


class InfoItem(BytesEnum):
    """Items of the INFO chunk"""
    track: 'InfoItem' = b'INAM'
    album: 'InfoItem' = b'IPRD'
    artist: 'InfoItem' = b'IART'
    date: 'InfoItem' = b'ICRD'
    track_number: 'InfoItem' = b'ITRK'
    comment: 'InfoItem' = b'ICMT'
    genre: 'InfoItem' = b'IGNR'


class Chunk:
    """Chunk read and write"""

    fp: Optional[IO]
    bigendian: bool
    chunk_id: ChunkID
    size: int
    start: int

    align: int = 2
    offset: int = 8
    _min_size: int = 0
    word_size: int = 4

    def __init__(self, fp: IO, bigendian: bool = False) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param bigendian: Is the file bid endian?
        """
        self.fp = fp
        self.bigendian = bigendian
        if not hasattr(self, 'chunk_id'):
            self.chunk_id = ChunkID.UNKNOWN_CHUNK
        self.size = 0
        self.start = self.fp.tell()

        if self.read_only:
            try:
                self.chunk_id = ChunkID(self.read(self.word_size))
            except ValueError:
                self.chunk_id = ChunkID.UNKNOWN_CHUNK
            self.size = self.read_int(self.word_size, signed=True)
        else:
            self.write_header()

    def __del__(self) -> None:
        self.close()

    @staticmethod
    def _file_is_read_only(fp: IO) -> bool:
        """Check whether a file is read-only"""
        return 'r' in fp.mode and '+' not in fp.mode

    @property
    def read_only(self) -> Optional[bool]:
        """Check whether the file is read-only"""
        if self.fp is None:
            return None
        else:
            return self._file_is_read_only(self.fp)

    @property
    def endianness(self) -> Literal['big', 'little']:
        """The endianness in text form."""
        if self.bigendian:
            return 'big'
        else:
            return 'little'

    @property
    def content_start(self) -> int:
        """The start position of the chunk content"""
        return self.start + self.offset

    @property
    def pad(self):
        """Size of any trailing padding required to align the chunk"""
        return self.size % self.align

    def skip(self, include_pad: bool = True) -> None:
        """
        Skip to the end of the chunk.

        :param include_pad: Specify whether the end includes any padding.
        """
        if self.size == 0:
            raise exception.Error('Chunk has no payload to skip')
        if include_pad:
            _pad = self.pad
        else:
            _pad = 0
        self.fp.seek(self.content_start + self.size + _pad)

    def read(self, nbytes: int) -> bytes:
        """
        Read data from the chunk.

        :param nbytes: The number of bytes to read.
        :return: The data.
        """
        data = self.fp.read(nbytes)
        if len(data) < nbytes:
            raise IOError('Could not read enough bytes. Maybe EOF.')
        return data

    def write(self, data: bytes, update_size: bool = True) -> None:
        """
        Write data to the chunk. Adjust the chunk size accordingly.

        :param data: Data to write to the chunk.
        :param update_size: Update the chunk size (not required for padding words).
        """
        data_size = len(data)
        real_size = data_size - (self.size - (self.fp.tell() - self.content_start))
        if update_size:
            self.size += max(real_size, 0)
        self.fp.write(data)

    def write_header(self) -> None:
        """Write the chunk header to the file, esp. the updated chunk size."""
        self.fp.seek(self.start)
        self.fp.write(self.chunk_id.value)
        self.fp.write(self.int_to_bytes(self.size, self.word_size, signed=False))

    def bytes_to_int(self, data: bytes, signed: bool = True) -> int:
        """
        Read a signed integer from the specified number of bytes of the input chunk.

        :param data: Input bytes to interpret as a signed integer.
        :param signed: Is the integer signed?
        :return: The integer value.
        """
        return int.from_bytes(data, byteorder=self.endianness, signed=signed)

    def read_int(self, nbytes: int, signed: bool = True) -> int:
        """
        Read an integer from the chunk.

        :param nbytes: Number of bytes encoding the integer.
        :param signed: Whether the integer is signed.
        :return: The integer value.
        """
        data = self.read(nbytes)
        return self.bytes_to_int(data, signed=signed)

    def int_to_bytes(self, data: int, nbytes: int, signed: bool = True) -> bytes:
        """
        Convert an integer to bytes.

        :param data: The integer to encode.
        :param nbytes: Number of bytes encoding the integer.
        :param signed: Whether the integer is signed.
        :return: The bytes.
        """
        # noinspection PyTypeChecker
        return int(data).to_bytes(nbytes, byteorder=self.endianness, signed=signed)

    def write_int(self, data: int, nbytes: int, signed: bool = True) -> None:
        """
        Write an integer to the chunk.

        :param data: The integer to encode.
        :param nbytes: Number of bytes encoding the integer.
        :param signed: Whether the integer is signed.
        """
        self.write(self.int_to_bytes(data, nbytes, signed=signed))

    def _get_float_struct_fmt(self, nbytes: int) -> str:
        """
        Get the format specifier for packing and unpacking floats

        :param nbytes: Number of bytes per audio sample.
        """

        endianness = '<' if self.endianness == 'little' else '>'
        try:
            return endianness + {
                4: 'f',
                8: 'd',
            }[nbytes]
        except KeyError:
            raise exception.Error('Cannot convert float with the specified bit depth')

    def bytes_to_float(self, data: bytes) -> float:
        """
        Read a float from the specified number of bytes of the input chunk.

        :param data: Input bytes to interpret as a float.
        :return: The float value.
        """
        return struct.unpack(self._get_float_struct_fmt(len(data)), data)[0]

    def read_float(self, nbytes: int) -> float:
        """
        Read a float from the chunk.

        :param nbytes: Number of bytes encoding the float.
        :return: The float value.
        """
        data = self.read(nbytes)
        return self.bytes_to_float(data)

    def float_to_bytes(self, data: float, nbytes: int) -> bytes:
        """
        Convert a float to bytes.

        :param data: The float to encode.
        :param nbytes: Number of bytes encoding the float.
        :return: The bytes.
        """
        return struct.pack(self._get_float_struct_fmt(nbytes), data)

    def write_float(self, data: float, nbytes: int) -> None:
        """
        Write a float to the chunk.

        :param data: The float to encode.
        :param nbytes: Number of bytes encoding the float.
        """
        self.write(self.float_to_bytes(data, nbytes))

    def close(self) -> None:
        """Close the chunk and update the header."""
        if self.size < self._min_size:
            raise exception.WriteError('Required data have not been written to the file')
        if 'w' in self.fp.mode and not self.fp.closed:
            self.write_header()


class RiffChunk(Chunk):
    """Riff container chunk read and write"""

    format: RiffFormat

    _min_size = 4

    def __init__(self, fp: IO) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        """
        self.chunk_id = ChunkID.RIFF_CHUNK
        self.format = RiffFormat.WAVE

        Chunk.__init__(self, fp, bigendian=False)

        if self.read_only:
            if self.chunk_id != ChunkID.RIFF_CHUNK:
                raise exception.ReadError('Chunk is not a RIFF chunk')
            self.format = RiffFormat(self.read(self.word_size))
        else:
            self.write(RiffFormat.WAVE.value)

    def close(self) -> None:
        """Close the chunk and update the header."""
        if self.format is None:
            raise exception.WriteError('RIFF format is not set')
        Chunk.close(self)


class WavFmtChunk(Chunk):
    """Wave format chunk read and write"""

    audio_fmt: WavFormat
    num_channels: int
    sample_rate: int
    byte_rate: int
    block_align: int
    bits_per_sample: int

    _min_size = 16
    audio_fmt_size: int = 2
    _num_channels_size: int = 2
    _sample_rate_size: int = 4
    _byte_rate_size: int = 4
    _block_align_size: int = 2
    _bits_per_sample_size: int = 2

    def __init__(self, fp: IO) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        """
        self.chunk_id = ChunkID.FMT_CHUNK
        if not hasattr(self, 'audio_fmt'):
            self.audio_fmt = WavFormat.PCM
        self.num_channels = 0
        self.sample_rate = 0
        self.byte_rate = 0
        self.block_align = 0
        self.bits_per_sample = 0

        Chunk.__init__(self, fp, bigendian=False)

        if self.read_only:
            self._read()
        else:
            self.write_fmt()

    def _read(self) -> None:
        """Read metadata from the chunk"""
        if self.chunk_id != ChunkID.FMT_CHUNK:
            raise exception.ReadError('Chunk is not a FMT chunk')
        self.audio_fmt = WavFormat(self.read_int(self.audio_fmt_size, signed=False))
        self.num_channels = self.read_int(self._num_channels_size, signed=False)
        self.sample_rate = self.read_int(self._sample_rate_size, signed=False)
        self.byte_rate = self.read_int(self._byte_rate_size, signed=False)
        self.block_align = self.read_int(self._block_align_size, signed=False)
        self.bits_per_sample = self.read_int(self._bits_per_sample_size, signed=False)

    @property
    def bytes_per_sample(self) -> int:
        """Number of bytes per audio sample"""
        return self.bits_per_sample // 8

    @property
    def signed(self) -> bool:
        """Whether the integer representation is signed"""
        return self.bytes_per_sample > 1

    def write_fmt(self) -> None:
        """Write the format data to the file."""
        self.fp.seek(self.content_start)
        self.write_int(self.audio_fmt.value, self.audio_fmt_size, signed=False)
        self.write_int(self.num_channels, self._num_channels_size, signed=False)
        self.write_int(self.sample_rate, self._sample_rate_size, signed=False)
        self.write_int(self.byte_rate, self._byte_rate_size, signed=False)
        self.write_int(self.block_align, self._block_align_size, signed=False)
        self.write_int(self.bits_per_sample, self._bits_per_sample_size, signed=False)

    def close(self) -> None:
        """Close the chunk and update the header and format data."""
        if 'w' in self.fp.mode and not self.fp.closed:
            self.write_fmt()
        Chunk.close(self)


class WavFmtExtensibleChunk(WavFmtChunk):

    extension_size: int
    valid_bits_per_sample: int
    channel_mask: bytes
    sub_format: bytes
    sub_data_format: WavFormat

    _sub_format_pad: bytes = b'\x00\x00\x00\x00\x10\x00\x80\x00\x00\xAA\x00\x38\x9B\x71'

    _min_size = 18
    _extension_size_size: int = 2
    _valid_bits_per_sample_size: int = 2
    _channel_mask_size: int = 4
    _sub_format_size: int = 16
    _sub_data_format_size: int = 2

    def __init__(self, fp: IO) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        """
        self.audio_fmt = WavFormat.EXTENSIBLE
        self.extension_size = 0
        self.valid_bits_per_sample = 0
        self.channel_mask = bytearray(self._channel_mask_size)
        self.sub_format = bytearray(self._sub_format_size)
        self.sub_data_format = WavFormat.PCM
        super().__init__(fp)

    def _read(self) -> None:
        """Read metadata from the chunk"""
        super()._read()
        self.extension_size = self.read_int(self._extension_size_size, signed=False)
        num_remaining_byes = self.extension_size
        if num_remaining_byes >= self._valid_bits_per_sample_size:
            self.valid_bits_per_sample = \
                self.read_int(self._valid_bits_per_sample_size, signed=False)
            num_remaining_byes -= self._valid_bits_per_sample_size
        if num_remaining_byes >= self._channel_mask_size:
            self.channel_mask = self.read(self._channel_mask_size)
            num_remaining_byes -= self._channel_mask_size
        if num_remaining_byes > 0:
            self.sub_format = self.read(num_remaining_byes)
            self.sub_data_format = WavFormat(
                int.from_bytes(
                    self.sub_format[:self._sub_data_format_size],
                    signed=False,
                    byteorder=self.endianness
                )
            )

    def write_fmt(self) -> None:
        """Write the format data to the file."""
        super().write_fmt()
        extension_size = \
            self._extension_size_size + \
            self._valid_bits_per_sample_size + \
            self._channel_mask_size + \
            self._sub_format_size
        self.write_int(extension_size, self._extension_size_size, signed=False)
        self.write_int(self.valid_bits_per_sample, self._valid_bits_per_sample_size, signed=False)
        self.write(self.channel_mask)
        self.write_int(self.sub_data_format.value, self._sub_data_format_size, signed=False)
        self.write(self._sub_format_pad)


class WavDataChunk(Chunk):
    """Wave data chunk read and write"""

    __did_warn: bool
    fmt_chunk: Union[WavFmtChunk, WavFmtExtensibleChunk]

    def __init__(self, fp: IO, fmt_chunk: WavFmtChunk) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param fmt_chunk: The associated format chunk.
        """
        self.chunk_id = ChunkID.DATA_CHUNK
        Chunk.__init__(self, fp, bigendian=False)

        self.__did_warn = False
        self.fmt_chunk = fmt_chunk

        if self.read_only:
            if self.chunk_id != ChunkID.DATA_CHUNK:
                raise exception.ReadError('Chunk is not a DATA chunk')

    @property
    def num_frames(self) -> int:
        """Number of audio frames in the file"""
        try:
            return self.size // self.fmt_chunk.block_align
        except ZeroDivisionError:
            return 0

    def close(self) -> None:
        """Close the chunk and update the header and format data."""
        self.fmt_chunk.close()
        Chunk.close(self)

    @property
    def audio_fmt(self) -> WavFormat:
        """The audio sample format."""
        if type(self.fmt_chunk) == WavFmtChunk:
            return self.fmt_chunk.audio_fmt
        elif type(self.fmt_chunk) == WavFmtExtensibleChunk:
            return self.fmt_chunk.sub_data_format

    def read_sample(self) -> Union[int, float]:
        """Read a sample from the chunk."""
        if self.audio_fmt == WavFormat.PCM:
            return self.read_int(self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
        elif self.audio_fmt == WavFormat.IEEE_FLOAT:
            return self.read_float(self.fmt_chunk.bytes_per_sample)

    def read_frames(self, nframes: Optional[int] = None) -> List[List[Union[int, float]]]:
        """
        Read a number of audio frames from the chunk. A frame is a collection of samples, from each
        audio channel, associated with a single time instant.

        :param nframes: Number of audio frames to read.
        :return: The audio frames as a list of lists.
        """

        if nframes is None or nframes < 0:
            # read all remaining frames
            nframes = self.num_frames

        # do not try to read past the end
        num_frames = min(nframes, self.num_frames - self.tell())

        audio = [
            [
                self.read_sample() for _ in range(self.fmt_chunk.num_channels)
            ]
            for _ in range(num_frames)
        ]

        return audio

    @property
    def _max_val(self) -> Union[float, int]:
        """Maximum value"""
        if self.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                sign_correction = 1
            else:
                sign_correction = 0
            return (2 ** (self.fmt_chunk.bits_per_sample - sign_correction)) - 1
        elif self.audio_fmt == WavFormat.IEEE_FLOAT:
            return 1.0

    @property
    def _min_val(self) -> Union[float, int]:
        """Minimum value"""
        if self.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                return -self._max_val - 1
            else:
                return 0
        elif self.audio_fmt == WavFormat.IEEE_FLOAT:
            return -1.0

    def __saturation_warning(self) -> None:
        """Print a warning to stderr about out-of-range sample values."""
        if not self.__did_warn:
            self.__did_warn = True
            print('Saturating one of more sample values that are out-of-range', file=sys.stderr)

    def _saturate(self, val: Union[int, float]) -> Union[int, float]:
        """Saturate out-of-range sample values."""
        if val > self._max_val:
            val = self._max_val
            self.__saturation_warning()
        elif val < self._min_val:
            val = self._min_val
            self.__saturation_warning()
        return val

    def write_sample(self, sample: Union[int, float]) -> None:
        """
        Write a sample to the chunk.

        :param sample: An audio sample.
        """
        sample = self._saturate(sample)
        if self.audio_fmt == WavFormat.PCM:
            self.write_int(sample, self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
        elif self.audio_fmt == WavFormat.IEEE_FLOAT:
            self.write_float(sample, self.fmt_chunk.bytes_per_sample)

    def write_frames(self, audio: List[List[Union[int, float]]]) -> None:
        """
        Write one or more frames of audio to the chunk.

        :param audio: The audio frames as a list of lists.
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

    def seek(self, frame_number: int, whence: int = 0) -> 'WavDataChunk':
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :param whence: The frame positioning mode.
        :return: The method returns the object.
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

    def tell(self) -> int:
        """Get the current frame number."""
        if self.fmt_chunk.block_align == 0:
            return 0
        else:
            return (self.fp.tell() - self.content_start) // \
                   self.fmt_chunk.block_align


class ListChunk(Chunk):
    """List chunk read and write"""

    info: Optional[Dict[str, Union[int, str]]]

    def __init__(self, fp: IO) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        """
        self.chunk_id = ChunkID.LIST_CHUNK
        Chunk.__init__(self, fp, bigendian=False)
        self.info = None

        if self.read_only:
            if self.chunk_id != ChunkID.LIST_CHUNK:
                raise exception.ReadError('Chunk is not a LIST chunk')
            subchnk = self.read(self.word_size)
            # read the INFO content of the LIST
            if subchnk == ListType.INFO.value:
                self.info = {}
                while self.fp.tell() < self.content_start + self.size:
                    key = self.read(self.word_size)
                    size = self.read_int(self.word_size)
                    pad = size % self.align
                    if key in [e.value for e in InfoItem]:
                        field: str = InfoItem(key).name
                        data = self.read(size).decode('ascii').rstrip('\x00')
                        try:
                            data = int(data)
                        except ValueError:
                            pass
                        self.info[field] = data
                        self.fp.seek(pad, 1)
                    else:
                        self.fp.seek(size + pad, 1)

    def write_info(self):
        """
        Write the INFO to the LIST chunk.
        """
        if self.info is not None:
            self.fp.seek(self.content_start)
            self.write(ListType.INFO.value)
            # write each item
            for key, val in self.info.items():
                if key not in InfoItem.__members__:
                    raise exception.WriteError('Unknown metadata field. Valid fields are: ' +
                                               ', '.join([e.name for e in InfoItem]))
                self.write(InfoItem[key].value)
                # convert to bytes
                data = dict([
                    (int, lambda x: str(x).encode('ascii')),
                    (str, lambda x: x.encode('ascii')),
                ]).get(type(val))(val)
                size = len(data)
                self.write_int(size, self.word_size)
                self.write(data)
                # align next item
                pad = self.fp.tell() % self.align
                if pad > 0:
                    self.write(bytearray(pad), update_size=False)
