"""
Chunk-based helper classes for working with RIFF files.
"""

import struct
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import Field, dataclass, field, fields
from enum import Enum
from typing import Any, BinaryIO, ClassVar, Literal, TypeVar
from warnings import warn

try:
    from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    from typing_extensions import Self

from . import exception

T = TypeVar("T", int, float)


class WavEnum(Enum):
    """Enum class for wave file chunks."""

    @classmethod
    def _missing_(cls, value):
        raise exception.ReadError(
            f"{value} is not a valid {cls.__name__}.  Valid types: "
            f"{', '.join([repr(m.value) for m in cls])}"
        )


class RiffFormat(WavEnum):
    """RIFF file format."""

    WAVE = b"WAVE"


class ChunkID(WavEnum):
    """RIFF chunk identifiers."""

    RIFF_CHUNK = b"RIFF"
    FMT_CHUNK = b"fmt "
    DATA_CHUNK = b"data"
    LIST_CHUNK = b"LIST"
    UNKNOWN_CHUNK = b"    "


class WavFormat(WavEnum):
    """Wav audio data format."""

    PCM = 0x0001
    IEEE_FLOAT = 0x0003
    EXTENSIBLE = 0xFFFE


class WavFormatExSubformat(WavEnum):
    """Extensible WAVE sub-format."""

    PCM = uuid.UUID("00000001-0000-0010-8000-00AA00389B71")
    IEEE = uuid.UUID("00000003-0000-0010-8000-00AA00389B71")


class ListType(WavEnum):
    """LIST chunk list types."""

    INFO = b"INFO"


class InfoItem(WavEnum):
    """Items of the INFO chunk."""

    track = b"INAM"
    album = b"IPRD"
    artist = b"IART"
    date = b"ICRD"
    track_number = b"ITRK"
    comment = b"ICMT"
    genre = b"IGNR"


@dataclass
class SchemaMixin:
    """Mixin class to provide chunk data parsing based on a schema."""

    @classmethod
    def _binfmt(cls) -> str:
        """The binary format for the chunk data."""
        return "<" + "".join(fld.metadata["binary"] for fld in cls._schema())

    @classmethod
    def _schema_size(cls) -> int:
        """The binary size of the schema."""
        return struct.calcsize(cls._binfmt())

    @property
    def _min_size(self) -> int:
        """The minimum size of the chunk."""
        return self._schema_size()

    @classmethod
    def _schema(cls) -> tuple[Field[Any], ...]:
        """The chunk schema."""
        return fields(cls)

    def _deserialize(self, data: bytes) -> None:
        """Deserialize the chunk data to class attributes."""
        values = struct.unpack(self._binfmt(), data)

        for f, value in zip(self._schema(), values, strict=True):
            if "decode" in f.metadata:
                value = f.metadata["decode"](value)
            setattr(self, f.name, value)

    def _serialize(self) -> bytes:
        """Serialize the class attributes to chunk data bytes."""
        values = []
        for f in self._schema():
            value = getattr(self, f.name)
            if "encode" in f.metadata:
                value = f.metadata["encode"](value)
            values.append(value)

        return struct.pack(self._binfmt(), *values)

    @classmethod
    def _field_size(cls, name: str) -> int:
        """Get the size of the field with the given name."""
        f = next(f for f in cls._schema() if f.name == name)
        return struct.calcsize(f.metadata["binary"])


def enum_value(e: Enum) -> Any:
    """Get the value of an enum item."""
    return e.value


@dataclass
class Chunk:
    """Chunk read and write."""

    align: ClassVar[int] = 2
    offset: ClassVar[int] = 8
    word_size: ClassVar[int] = 4
    endianness: ClassVar[Literal["little"]] = "little"

    def __init__(self, fp: BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the chunk from a file pointer. Chunks are little endian.

        :param fp: Open file pointer.
        :param mode: File read/write mode.
        """
        self.fp: BinaryIO = fp
        if mode not in ("r", "w"):
            raise ValueError(f"Invalid mode: {mode}")
        self.mode: Literal["r", "w"] = mode
        if not hasattr(self, "chunk_id"):
            self.chunk_id: ChunkID = ChunkID.UNKNOWN_CHUNK
        self.size: int = 0
        self.start: int = self.fp.tell()

        if self.read_only:
            try:
                self.chunk_id = ChunkID(self.read(self.word_size))
            except exception.ReadError:
                self.chunk_id = ChunkID.UNKNOWN_CHUNK
            self.size = self.read_int(self.word_size, signed=False)
        else:
            self.write_header()

    @property
    def _min_size(self) -> int:
        """The minimum size of the chunk."""
        return 0

    @property
    def read_only(self) -> bool:
        """Check whether the file is read-only."""
        return "r" == self.mode

    @property
    def content_start(self) -> int:
        """The start position of the chunk content."""
        return self.start + self.offset

    @property
    def pad(self) -> int:
        """Size of any trailing padding required to align the chunk."""
        return self.size % self.align

    @property
    def end(self) -> int:
        """The end position of the chunk content after any padding."""
        return self.content_start + self.size + self.pad

    def skip(self, include_pad: bool = True) -> None:
        """
        Skip to the end of the chunk.

        :param include_pad: Specify whether the end includes any padding.
        """
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
            raise exception.ReadError("Could not read enough bytes. Maybe EOF.")
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

        endianness = "<" if self.endianness == "little" else ">"
        try:
            return (
                endianness
                + {
                    4: "f",
                    8: "d",
                }[nbytes]
            )
        except KeyError:
            raise exception.Error("Cannot convert float with the specified bit depth") from None

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

    def finalise(self) -> None:
        """Finalise the chunk and update the header."""
        if (not self.read_only) and (not self.fp.closed):
            if self.size < self._min_size:
                raise exception.WriteError("Required data have not been written to the file")
            self.write_header()


class RiffChunk(Chunk):
    """Riff container chunk read and write."""

    def __init__(self, fp: BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param mode: File read/write mode.
        """
        self.chunk_id = ChunkID.RIFF_CHUNK
        self.format: RiffFormat = RiffFormat.WAVE

        Chunk.__init__(self, fp, mode=mode)

        if self.read_only:
            if self.chunk_id != ChunkID.RIFF_CHUNK:
                raise exception.ReadError("Chunk is not a RIFF chunk")
            self.format = RiffFormat(self.read(self.word_size))
        else:
            self.write(RiffFormat.WAVE.value)

    @property
    def _min_size(self) -> int:
        """Minimum chunk size."""
        return 4

    def finalise(self) -> None:
        """Finalise the chunk and update the header."""
        if self.format is None:
            raise exception.WriteError("RIFF format is not set")
        Chunk.finalise(self)


@dataclass
class WavFmtChunk(SchemaMixin, Chunk):
    """Wave format chunk read and write."""

    _audio_fmt: WavFormat = field(
        default=WavFormat.PCM,
        metadata={"binary": "H", "decode": WavFormat, "encode": enum_value},
        init=False,
    )
    num_channels: int = field(default=0, metadata={"binary": "H"})
    sample_rate: int = field(default=0, metadata={"binary": "I"})
    byte_rate: int = field(default=0, metadata={"binary": "I"})
    block_align: int = field(default=0, metadata={"binary": "H"})
    bits_per_sample: int = field(default=0, metadata={"binary": "H"})

    def __init__(self, fp: BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param mode: File read/write mode.
        """
        self.chunk_id = ChunkID.FMT_CHUNK

        Chunk.__init__(self, fp, mode=mode)

        if self.read_only:
            self._read()
        else:
            self.write_fmt()

    @classmethod
    def read_audio_format(cls, fp: BinaryIO) -> WavFormat:
        """
        Find the audio data format for the file. Assumes that the audio format word is the next word
        in the input stream. Calling the method will advance the stream position.

        :param fp: Stream from which to read the audio data format.
        :return: The audio data format.
        """
        f = next(f for f in fields(cls) if f.name == "_audio_fmt")
        binfmt = "<" + f.metadata["binary"]
        size = struct.calcsize(binfmt)
        data = fp.read(size)
        if len(data) != size:
            raise exception.ReadError("Could not read audio format")
        return WavFormat(struct.unpack(binfmt, data)[0])

    def _read(self) -> None:
        """Read metadata from the chunk."""
        if self.chunk_id != ChunkID.FMT_CHUNK:
            raise exception.ReadError("Chunk is not a FMT chunk")
        if self.size < self._schema_size():
            raise exception.ReadError("FMT chunk is too small")

        self._deserialize(self.read(self._schema_size()))

        if self.num_channels == 0:
            raise exception.ReadError("Number of channels is 0")
        if self.sample_rate == 0:
            raise exception.ReadError("Sample rate is 0")
        if self.bits_per_sample == 0:
            raise exception.ReadError("bits_per_sample is 0")
        if self.bits_per_sample % 8 != 0:
            raise exception.ReadError("bits_per_sample should be a multiple of 8")
        expected_block_align = self.num_channels * self.bits_per_sample // 8
        if self.block_align != expected_block_align:
            raise exception.ReadError("block_align set incorrectly")
        expected_byte_rate = self.sample_rate * self.block_align
        if self.byte_rate != expected_byte_rate:
            raise exception.ReadError("byte_rate set incorrectly")
        if self.audio_fmt == WavFormat.IEEE_FLOAT and self.bits_per_sample not in (32, 64):
            raise exception.ReadError("bits_per_sample should be 32 or 64 for IEEE_FLOAT")

    @property
    def audio_fmt(self) -> WavFormat:
        """Get the audio sample format."""
        return self._audio_fmt

    @audio_fmt.setter
    def audio_fmt(self, audio_fmt: WavFormat) -> None:
        """Set the audio sample format."""
        self._audio_fmt = audio_fmt

    @property
    def bytes_per_sample(self) -> int:
        """Number of bytes per audio sample."""
        return self.bits_per_sample // 8

    @property
    def signed(self) -> bool:
        """Whether the integer representation is signed."""
        return self.bytes_per_sample > 1

    def write_fmt(self) -> None:
        """Write the format data to the file."""
        self.fp.seek(self.content_start)
        self.write(self._serialize())

    def finalise(self) -> None:
        """Finalise the chunk and update the header and format data."""
        if (not self.read_only) and (not self.fp.closed):
            self.write_fmt()
        Chunk.finalise(self)


@dataclass
class WavFmtExtensibleChunk(WavFmtChunk):
    """Wave extensible format chunk read and write."""

    extension_size: int = field(default=0, metadata={"binary": "H"})
    valid_bits_per_sample: int = field(default=0, metadata={"binary": "H"})
    channel_mask: int = field(default=0, metadata={"binary": "I"})
    sub_data_format: WavFormatExSubformat = field(
        default=WavFormatExSubformat.PCM,
        metadata={
            "binary": "16s",
            "decode": lambda x: WavFormatExSubformat(uuid.UUID(bytes_le=x)),
            "encode": lambda x: enum_value(x).bytes_le,
        },
    )

    def __init__(self, fp: BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param mode: File read/write mode.
        """
        self._audio_fmt = WavFormat.EXTENSIBLE
        super().__init__(fp, mode=mode)

    @classmethod
    def _min_extension_size(cls) -> int:
        """Minimum chunk extension size."""
        return (
            cls._field_size("valid_bits_per_sample")
            + cls._field_size("channel_mask")
            + cls._field_size("sub_data_format")
        )

    def _read(self) -> None:
        """Read metadata from the chunk."""
        super()._read()

        # verify metadata
        if self.extension_size < self._min_extension_size():
            raise exception.ReadError("Extension size is too small")
        fmt_ext_offset = WavFmtChunk._schema_size() + self._field_size("extension_size")
        if fmt_ext_offset + self.extension_size > self.size:
            raise exception.ReadError("Extension size exceeds chunk size")
        if self.valid_bits_per_sample == 0:
            raise exception.ReadError("Valid bits per sample is 0.")
        if self.valid_bits_per_sample > self.bits_per_sample:
            raise exception.ReadError("Valid bits per sample exceeds container bits per sample")
        if self.audio_fmt == WavFormat.IEEE_FLOAT:
            if self.valid_bits_per_sample not in (32, 64):
                raise exception.ReadError("valid_bits_per_sample should be 32 or 64 for IEEE_FLOAT")
            if self.valid_bits_per_sample != self.bits_per_sample:
                raise exception.ReadError("Valid bits must equal container width for IEEE_FLOAT")
        if self.channel_mask != 0:
            # the channel count mask must have a number of bits set equal to the number of channels
            channel_count = self.channel_mask.bit_count()
            if channel_count != self.num_channels:
                raise exception.ReadError("Invalid channel mask")

    def write_fmt(self) -> None:
        """Write the format data to the file."""
        self.extension_size = self._min_extension_size()

        if self.valid_bits_per_sample == 0:
            warn(
                "valid_bits_per_sample is 0. Interpreting this as full container precision.",
                stacklevel=2,
            )
            self.valid_bits_per_sample = self.bits_per_sample

        super().write_fmt()

    @property
    def audio_fmt(self) -> WavFormat:
        """Get the audio sample format."""
        return WavFormat(
            int.from_bytes(self.sub_data_format.value.bytes_le[0:2], byteorder="little")
        )

    @audio_fmt.setter
    def audio_fmt(self, audio_fmt: WavFormat) -> None:
        """Set the audio sample format."""
        self.sub_data_format = {
            WavFormat.PCM: WavFormatExSubformat.PCM,
            WavFormat.IEEE_FLOAT: WavFormatExSubformat.IEEE,
        }[audio_fmt]


class WavDataChunk(Chunk):
    """Wave data chunk read and write."""

    def __init__(
        self,
        fp: BinaryIO,
        fmt_chunk: WavFmtChunk | WavFmtExtensibleChunk,
        mode: Literal["r", "w"] = "r",
    ) -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param fmt_chunk: The associated format chunk.
        :param mode: File read/write mode.
        """
        self.chunk_id = ChunkID.DATA_CHUNK
        Chunk.__init__(self, fp, mode=mode)

        self.__did_warn = False
        self.fmt_chunk = fmt_chunk

        if self.read_only and self.chunk_id != ChunkID.DATA_CHUNK:
            raise exception.ReadError("Chunk is not a DATA chunk")

    @property
    def num_frames(self) -> int:
        """Number of audio frames in the file."""
        try:
            return self.size // self.fmt_chunk.block_align
        except ZeroDivisionError:
            return 0

    def finalise(self) -> None:
        """Finalise the chunk and update the header and format data."""
        self.fmt_chunk.finalise()
        if not self.read_only:
            num_align_bytes = self.size % Chunk.align
            if num_align_bytes > 0:
                self.skip(include_pad=False)
                self.write(bytes(bytearray(num_align_bytes)), update_size=False)

        Chunk.finalise(self)

    def read_sample(self) -> int | float:
        """Read a sample from the chunk."""
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            sample = self.read_int(self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
            return sample >> self._padding_bits
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return self.read_float(self.fmt_chunk.bytes_per_sample)
        raise exception.ReadError("File is invalid")  # pragma: no cover

    def read_frames(self, nframes: int | None = None) -> list[list[int | float]]:
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
            [self.read_sample() for _ in range(self.fmt_chunk.num_channels)]
            for _ in range(num_frames)
        ]

        return audio

    @property
    def _max_val(self) -> float | int:
        """Maximum value."""
        bits_per_sample = self.fmt_chunk.bits_per_sample
        if isinstance(self.fmt_chunk, WavFmtExtensibleChunk):
            bits_per_sample = self.fmt_chunk.valid_bits_per_sample
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                sign_correction = 1
            else:
                sign_correction = 0
            return (2 ** (bits_per_sample - sign_correction)) - 1
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return 1.0
        raise exception.ReadError("File is invalid")  # pragma: no cover

    @property
    def _min_val(self) -> float | int:
        """Minimum value."""
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            if self.fmt_chunk.signed:
                return -self._max_val - 1
            else:
                return 0
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            return -1.0
        raise exception.ReadError("File is invalid")  # pragma: no cover

    def __saturation_warning(self) -> None:
        """Print a warning to stderr about out-of-range sample values."""
        if not self.__did_warn:
            self.__did_warn = True
            print("Saturating one of more sample values that are out-of-range", file=sys.stderr)

    def _saturate(self, val: float) -> int | float:
        """Saturate out-of-range sample values."""
        if val > self._max_val:
            val = self._max_val
            self.__saturation_warning()
        elif val < self._min_val:
            val = self._min_val
            self.__saturation_warning()
        return val

    @property
    def _padding_bits(self) -> int:
        """Sample padding bits for extensible format."""
        padding_bits = 0
        if isinstance(self.fmt_chunk, WavFmtExtensibleChunk):
            padding_bits = self.fmt_chunk.bits_per_sample - self.fmt_chunk.valid_bits_per_sample
        return padding_bits

    def write_sample(self, sample: float) -> None:
        """
        Write a sample to the chunk.

        :param sample: An audio sample.
        """
        sample = self._saturate(sample)
        if self.fmt_chunk.audio_fmt == WavFormat.PCM:
            sample = int(sample) << self._padding_bits
            self.write_int(sample, self.fmt_chunk.bytes_per_sample, signed=self.fmt_chunk.signed)
        elif self.fmt_chunk.audio_fmt == WavFormat.IEEE_FLOAT:
            self.write_float(sample, self.fmt_chunk.bytes_per_sample)
        else:
            raise exception.ReadError("File is invalid")

    def write_frames(
        self, audio: Sequence[Sequence[T]], sample_transform: Callable[[T], int | float] | None
    ) -> None:
        """
        Write one or more frames of audio to the chunk. Assumes that the audio buffer is
        well-formed. Use Wavfile.check_audio_buffer to validate a buffer.

        :param audio: The audio frames as a list of lists.
        :param sample_transform: An optional transform function to apply to the audio samples.
        """
        num_channels = len(audio[0])
        if num_channels != self.fmt_chunk.num_channels:
            if self.fmt_chunk.num_channels == 0:
                self.fmt_chunk.num_channels = num_channels
            else:
                raise exception.WriteError("Number of channels does not match the format chunk")

        if self.fmt_chunk.block_align == 0:
            self.fmt_chunk.block_align = (
                self.fmt_chunk.num_channels * self.fmt_chunk.bytes_per_sample
            )
            self.fmt_chunk.byte_rate = self.fmt_chunk.block_align * self.fmt_chunk.sample_rate

        for frame in audio:
            for sample in frame:
                if sample_transform is not None:
                    sample = sample_transform(sample)
                self.write_sample(sample)

    def seek(self, frame_number: int, whence: int = 0) -> Self:
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :param whence: The frame positioning mode.
        :return: The method returns the object.
        """
        if self.fmt_chunk.block_align == 0:
            raise exception.Error("No frames written yet")
        if whence == 0:
            relative_pos = self.content_start
        elif whence == 1:
            relative_pos = self.fp.tell()
        elif whence == 2:
            relative_pos = self.content_start + self.size
        else:
            raise exception.Error("Invalid whence parameter")

        new_pos = relative_pos + (frame_number * self.fmt_chunk.block_align)
        if not self.content_start <= new_pos <= self.content_start + self.size:
            raise exception.Error("Requested frame exceeds data chunk")

        self.fp.seek(new_pos)
        return self

    def tell(self) -> int:
        """Get the current frame number."""
        if self.fmt_chunk.block_align == 0:
            return 0
        else:
            return (self.fp.tell() - self.content_start) // self.fmt_chunk.block_align


class ListChunk(Chunk):
    """List chunk read and write."""

    def __init__(self, fp: BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the chunk from a file pointer.

        :param fp: Open file pointer.
        :param mode: File read/write mode.
        """
        self.chunk_id = ChunkID.LIST_CHUNK
        Chunk.__init__(self, fp, mode=mode)
        self.info: dict[str, int | str] | None = None

        if self.read_only:
            if self.chunk_id != ChunkID.LIST_CHUNK:
                raise exception.ReadError("Chunk is not a LIST chunk")

            # get end
            file_pos = fp.tell()
            self.fp.seek(0, 2)
            file_size = self.fp.tell()
            if (self.content_start + self.size) > file_size:
                raise exception.ReadError("Chunk exceeds file size")
            self.fp.seek(file_pos)

            # check there are words to read
            if self.size < self.word_size:
                warn("LIST chunk content is too small, skipping", stacklevel=2)
                return

            # read the INFO content of the LIST
            subchnk = self.read(self.word_size)
            if subchnk == ListType.INFO.value:
                self.info = {}
                list_end = self.content_start + self.size
                while self.fp.tell() < list_end:
                    if list_end - self.fp.tell() < 2 * self.word_size:
                        raise exception.ReadError("Incomplete LIST subchunk header")

                    key = self.read(self.word_size)
                    size = self.read_int(self.word_size, signed=False)
                    pad = size % self.align

                    if size + pad > list_end - self.fp.tell():
                        raise exception.ReadError("LIST subchunk exceeds LIST chunk")

                    if key in {e.value for e in InfoItem}:
                        _field: str = InfoItem(key).name
                        data = self.read(size).decode("ascii").rstrip("\x00")
                        try:
                            data = int(data)
                        except ValueError:
                            pass
                        self.info[_field] = data
                        self.fp.seek(pad, 1)
                    else:
                        warn(f"Unknown LIST subchunk {key}", stacklevel=2)
                        self.fp.seek(size + pad, 1)

    def write_info(self):
        """Write the INFO to the LIST chunk."""
        if self.info is not None:
            self.fp.seek(self.content_start)
            self.write(ListType.INFO.value)
            # write each item
            for key, val in self.info.items():
                if key not in InfoItem.__members__:
                    raise exception.WriteError(
                        "Unknown metadata field. Valid fields are: "
                        + ", ".join([e.name for e in InfoItem])
                    )
                self.write(InfoItem[key].value)
                # convert to bytes
                decoder = {
                    int: lambda x: str(x).encode("ascii"),
                    str: lambda x: x.encode("ascii"),
                }.get(type(val))
                if decoder is not None:
                    data = decoder(val)
                else:
                    raise exception.WriteError("Unknown metadata type")
                size = len(data)
                self.write_int(size, self.word_size, signed=False)
                self.write(data)
                # align next item
                pad = size % self.align
                self.write(bytes(pad))
