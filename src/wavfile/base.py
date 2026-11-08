"""
The main API for reading and writing wav files.
"""

from __future__ import annotations

import builtins
import os
from abc import ABC
from collections.abc import Sequence
from functools import wraps
from typing import BinaryIO, Literal

try:
    from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    from typing_extensions import Self

from . import chunk, exception


def requires_open(func):
    """Throw an exception on IO operations if the file is not open."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.closed:
            raise ValueError("I/O operation on closed WAV file")
        return func(self, *args, **kwargs)

    return wrapper


class Wavfile(ABC):  # noqa: B024
    """Abstract base class for wave file read/write"""

    def __init__(self) -> None:
        """
        Initialise the base class.
        """
        self.fp: BinaryIO | None = None
        self._should_close_file: bool = False
        self._closed: bool = False
        self._riff_chunk: chunk.RiffChunk | None = None
        self._data_chunk: chunk.WavDataChunk | None = None
        self._list_chunk: chunk.ListChunk | None = None

    def _init_fp(self, f: str | os.PathLike[str] | BinaryIO, mode: Literal["r", "w"] = "r") -> None:
        """
        Initialise the file pointer.

        :param f: A path to a file or an open file object.
        """
        # open the file
        if isinstance(f, (str, os.PathLike)):
            self.fp = builtins.open(f, mode + "b")  # noqa: SIM115
            self._should_close_file = True
        else:
            self.fp = f
            self._should_close_file = False

    @classmethod
    def check_audio_buffer(cls, audio: Sequence[Sequence[float]]) -> type[int | float] | None:
        """
        Validate the audio buffer layout and type. The buffer must have a consistent audio sample
        type and channel count.

        Raises TypeError when the audio sample type is invalid or inconsistent.

        Raises ValueError when channel count is zero or inconsistent.

        :return: None when there are no audio frames, otherwise the audio sample type.
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

        if not all(type(sample) is sample_type for frame in audio for sample in frame):
            raise TypeError("Audio samples must be of the same type")

        return sample_type

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
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
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
        return round(((x + 1.0) / 2.0) * (2.0**self.bits_per_sample))

    def _convert_float_to_signed_int(self, x: float) -> int:
        """
        Convert float [-1, 1) to signed int.

        :param x: The float value to convert.
        :return: The integer equivalent in the current range.
        """
        return round(x * (2.0 ** (self.bits_per_sample - 1.0)))

    def _convert_float_to_int(self, x: float) -> int:
        """
        Convert float [-1, 1) to int.

        :param x: The float value to convert.
        :return: The integer equivalent in the current range.
        """
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        if self._data_chunk.fmt_chunk.signed:
            return self._convert_float_to_signed_int(x)
        else:
            return self._convert_float_to_unsigned_int(x)

    @property
    def _bytes_per_sample(self) -> int:
        """Number of bytes per audio sample"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.bytes_per_sample

    @property
    def closed(self) -> bool:
        """Whether the file is closed"""
        return self._closed

    @property
    def num_channels(self) -> int:
        """Number of audio channels in the file"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.num_channels

    @property
    def sample_rate(self) -> int:
        """Sampling rate of the audio data"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.sample_rate

    @property
    def bits_per_sample(self) -> int:
        """Number of bits per audio sample"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.bits_per_sample

    @property
    def format(self) -> chunk.WavFormat:
        """Wave file format code"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk._audio_fmt

    @property
    def audio_fmt(self) -> chunk.WavFormat:
        """Audio sample format"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.audio_fmt

    @property
    def num_frames(self) -> int:
        """Number of audio frames in the file"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
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
        return f"{h}:{m:02d}:{s:05.2f}"

    @property
    def _block_align(self) -> int:
        """Number of audio frames in the file"""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.fmt_chunk.block_align

    @property
    def metadata(self) -> dict[str, str | int] | None:
        """Metadata from the .wav file"""
        if self._list_chunk is not None:
            return self._list_chunk.info
        return None

    @staticmethod
    def _buffer_max_abs(data: Sequence[Sequence[float | int]]) -> float | int:
        """
        Max(Abs(X)) for an audio buffer.

        :param data: The buffer to analyse.
        :return: The maximum absolute value.
        """
        return max([max([abs(y) for y in x]) for x in data])

    @requires_open
    def seek(self, frame_number: int, whence: int = 0) -> Wavfile:
        """
        Move to the specified frame number. The frame positioning mode ``whence`` are: 0 (default) =
        absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.

        :param frame_number: The frame number.
        :param whence: The frame positioning mode.
        :return: The method returns the object.
        """
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        self._data_chunk.seek(frame_number, whence)
        return self

    @requires_open
    def tell(self) -> int:
        """Get the current frame number."""
        if self._data_chunk is None:
            raise exception.Error("Audio data chunk is not initialised.")
        return self._data_chunk.tell()

    def _get_total_size(self) -> int:
        """Get the total size of the file"""
        if self._data_chunk is None:
            return 0
        total_size = (
            self._data_chunk.size
            + self._data_chunk.pad
            + chunk.Chunk.offset
            + self._data_chunk.fmt_chunk.size
            + self._data_chunk.fmt_chunk.pad
            + chunk.Chunk.offset
            + chunk.Chunk.word_size
        )
        if self._list_chunk is not None:
            total_size += self._list_chunk.size + self._list_chunk.pad + chunk.Chunk.offset
        return total_size

    def _finalise(self) -> None:
        """
        Finalise the file.
        """
        if self._riff_chunk is not None:
            self._riff_chunk.size = self._get_total_size()
        if self._data_chunk:
            self._data_chunk.finalise()
        if self._list_chunk is not None:
            self._list_chunk.finalise()
        if self._riff_chunk is not None:
            self._riff_chunk.finalise()

    def close(self) -> None:
        """
        Close the wav file.
        """
        if self._closed:
            return
        self._closed = True
        try:
            self._finalise()
        finally:
            if self._should_close_file and self.fp is not None:
                self.fp.close()

    @requires_open
    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.close()
        return False
