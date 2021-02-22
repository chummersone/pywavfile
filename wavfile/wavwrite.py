from wavfile.wavfile_base import WavFile
import wavfile


class WavWrite(WavFile):
    """Class for writing a wave file"""

    def __init__(self, f, sample_rate=44100, num_channels=None, bits_per_sample=16):
        """
        Initialise the WavWrite object.
        :param f: Either a path to a wave file or a pointer to an open file.
        :param sample_rate: The sample rate for the new file.
        :param num_channels: The number of audio channels for the new file. If
        unspecified, the parameter will be determined from the first block of
        samples.
        :param bits_per_sample: The number of bits to encode each audio sample.
        """

        WavFile.__init__(self)
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._bits_per_sample = bits_per_sample
        if (bits_per_sample % 8) != 0:
            wavfile.Error("Invalid bits per sample")

        self._data_end = 0
        self._fmt_chunk_ptr = 0
        self._data_chunk_ptr = 0
        self._is_open = True

        self._init_fp(f, 'wb')
        try:
            self._init_file()
        except:
            self.close()
            raise

    def _write_chunk(self, data):
        """Write a chunk of data to the file"""
        return self._fp.write(data)

    def _max_signed_int(self, nbytes=None):
        """Maximum signed integer"""
        if nbytes is None:
            nbytes = self.chunksize
        return (2 ** ((nbytes * 8) - 1)) - 1

    def _min_signed_int(self, nbytes=None):
        """Minimum signed integer"""
        return -self._max_signed_int(nbytes) - 1

    def _max_unsigned_int(self, nbytes=None):
        """Maximum unsigned integer"""
        if nbytes is None:
            nbytes = self.chunksize
        return (2 ** (nbytes * 8)) - 1

    def _write_unsigned_int(self, data, nbytes=None):
        """Write an unsigned integer to the file"""
        if nbytes is None:
            nbytes = self.chunksize
        max_unsigned_int = self._max_unsigned_int(nbytes)
        min_unsigned_int = 0
        if data > max_unsigned_int:
            data = max_unsigned_int
        if data < min_unsigned_int:
            data = min_unsigned_int
        byte_data = data.to_bytes(nbytes, byteorder='little', signed=False)
        self._write_chunk(byte_data)

    def _write_signed_int(self, data, nbytes=None):
        """Write a signed integer to the file"""
        if nbytes is None:
            nbytes = self.chunksize
        max_signed_int = self._max_signed_int(nbytes)
        min_signed_int = self._min_signed_int(nbytes)
        if data > max_signed_int:
            data = max_signed_int
        if data < min_signed_int:
            data = min_signed_int
        byte_data = data.to_bytes(nbytes, byteorder='little', signed=True)
        self._write_chunk(byte_data)

    def _init_file(self):
        """Write the header"""
        self._fp.seek(0)

        # write RIFF header
        self._write_chunk(self.WAVE_CHUNK_ID_RIFF)
        self._write_signed_int(0)
        self._write_chunk(self.WAVE_CHUNK_ID_WAVE)

        # write fmt header
        _num_fmt_bytes = 16
        self._fmt_chunk_ptr = self._fp.tell()
        self._write_chunk(self.WAVE_CHUNK_ID_FMT)
        self._write_signed_int(_num_fmt_bytes)
        self._write_signed_int(self.WAVE_FORMAT_PCM, self.chunksize // 2)
        self._write_signed_int(self._num_channels or 0, self.chunksize // 2)
        self._write_signed_int(self._sample_rate)
        self._write_signed_int(0)  # byte rate
        self._write_signed_int(0, self.chunksize // 2)  # block align
        self._write_signed_int(self._bits_per_sample, self.chunksize // 2)

        # write data header
        self._data_chunk_ptr = self._fp.tell()
        self._write_chunk(self.WAVE_CHUNK_ID_DATA)
        self._write_signed_int(0)  # data size
        self._data_start = self._fp.tell()

    def write(self, audio):
        """
        Write audio data to the file. The data should be a list of lists with
        dimensions (N,C), where N is the number of frames and C is the number of
        audio channels. The data maybe int or float. Integer data are written
        directly. Float data should be in the range [-1,1) and are converted
        automatically.
        :param audio:
        :return:
        """

        if not self._is_open:
            raise wavfile.Error("Wave file is closed")

        # set number of audio channels if not set
        if self._num_channels is None:
            self._num_channels = len(audio[0])

        # if number of audio channels is set, update the block alignment, etc.
        if self._block_align == 0:
            self._block_align = (self._bits_per_sample // 8) * self._num_channels
            self._byte_rate = self._block_align * self._sample_rate

        # set up format converters
        if self._bits_per_sample == 8:
            write = self._write_unsigned_int
        else:
            write = self._write_signed_int
        if isinstance(audio[0][0], float):
            if self._bits_per_sample == 8:
                def convert(x):
                    return int(round(((x + 1.0) / 2.0) * (2.0 ** self._bits_per_sample)))
            else:
                def convert(x):
                    return int(round(x * (2.0 ** (self._bits_per_sample - 1.0))))
        else:
            def convert(x):
                return int(x)

        # write the audio data
        for i in range(0, len(audio)):
            for j in range(0, self._num_channels):
                sample = convert(audio[i][j])
                write(sample, self._bytes_per_sample)

        self._data_end = max(self._data_end, self._fp.tell())
        self._data_size = self._data_end - self._data_start
        self._num_frames = self._data_size // self._block_align

    def close(self):
        """Close the file."""

        if self._is_open:
            # write data chunk size
            self._fp.seek(self._data_chunk_ptr + self.chunksize)
            self._write_signed_int(self._data_size)

            # write fmt data
            self._fp.seek(self._fmt_chunk_ptr + (2 * self.chunksize) + (self.chunksize // 2))
            self._write_signed_int(self._num_channels, self.chunksize // 2)
            self._fp.seek(self.chunksize, 1)  # skip sample rate
            self._write_signed_int(self._byte_rate)
            self._write_signed_int(self._block_align, self.chunksize // 2)

            self._is_open = False

        # close the file
        if self._should_close_file:
            self._fp.close()
        self._should_close_file = False
