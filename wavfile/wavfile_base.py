import builtins
from abc import ABC

import wavfile


class WavFile(ABC):
    """Abstract base class for wave file read/write"""

    chunksize = 4

    # audio sample format
    WAVE_FORMAT_PCM = 0x0001
    valid_formats = (WAVE_FORMAT_PCM,)

    # chunk IDs
    WAVE_CHUNK_ID_RIFF = b'RIFF'
    WAVE_CHUNK_ID_WAVE = b'WAVE'
    WAVE_CHUNK_ID_FMT = b'fmt '
    WAVE_CHUNK_ID_DATA = b'data'

    def __init__(self):
        """Initialise the base class"""
        self._filesize = 0
        self._audio_fmt = 0
        self._num_channels = 0
        self._sample_rate = 0
        self._byte_rate = 0
        self._block_align = 0
        self._bits_per_sample = 0
        self._data_size = 0
        self._data_start = 0
        self._fmt_size = 0
        self._num_frames = 0
        self._fp = None
        self._should_close_file = False

    def _init_fp(self, f, mode):
        """Initialise the file pointer"""
        # open the file
        if isinstance(f, str):
            self._fp = builtins.open(f, mode)
            self._should_close_file = True
        else:
            self._fp = f

    @property
    def _bytes_per_sample(self):
        """Number of bytes per audio sample"""
        return self._block_align // self._num_channels

    @property
    def num_channels(self):
        """Number of audio channels in the file"""
        return self._num_channels

    @property
    def sample_rate(self):
        """Sampling rate of the audio data"""
        return self._sample_rate

    @property
    def bits_per_sample(self):
        """Number of bits per audio sample"""
        return self._bits_per_sample

    @property
    def num_frames(self):
        """Number of audio frames in the file"""
        return self._num_frames

    def seek(self, frame_number):
        """
        Move to the specified frame number.
        :param frame_number: The frame number.
        :return: The method returns the object.
        """
        if frame_number > self._num_frames:
            raise wavfile.Error('Frame number exceeds number of frames in file')
        self._fp.seek(self._data_start + (frame_number * self._block_align))
        return self

    def tell(self):
        """Get the current frame number."""
        return (self._fp.tell() - self._data_start) // self._block_align

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
