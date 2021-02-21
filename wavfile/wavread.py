from wavfile.wavfile_base import WavFile
import wavfile


class WavRead(WavFile):
    """Class for reading a wave file"""

    def __init__(self, f):
        """
        Initialise the WavRead object.
        :param f: Either a path to a wave file or a pointer to an open file.
        """
        WavFile.__init__(self)

        self._init_fp(f, 'rb')

        # read the file header
        try:
            self._init_file()
        except:
            self.close()
            raise

    def _read_chunk(self, chunksize):
        """Read a chunk of data from the file"""
        return self._fp.read(chunksize)

    def _read_chunk_header(self, chunksize):
        """Read the chunk header"""
        chk_id = self._read_chunk(chunksize)
        chk_size = self._read_signed_int(chunksize)
        return chk_id, chk_size

    def _read_required_chunk(self, chunksize, requirement):
        """
        Read a chunk and check that its content meets a requirement.
        :param chunksize: Number of bytes to read.
        :param requirement: The expected value.
        :return: The read data.
        """
        data = self._read_chunk(chunksize)
        if data != requirement:
            raise wavfile.Error('Invalid wave file')
        return data

    def _read_signed_int(self, nbytes):
        """
        Read a signed integer from the specified number of bytes of the input
        file.
        :param nbytes: Number of bytes from the input to interpret as a signed
        integer.
        :return: The integer value.
        """
        return int.from_bytes(self._read_chunk(nbytes), byteorder='little', signed=True)

    def _init_file(self):
        """Read the file and initialise the object properties."""
        self._fp.seek(0)

        # Read the file
        while True:
            chk_id, chk_size = self._read_chunk_header(self.chunksize)

            # Check for EOF
            if len(chk_id) == 0:
                break

            # Interpret chunks
            if chk_id == self.WAVE_CHUNK_ID_RIFF:
                # Read RIFF chunk
                self._filesize = chk_size
                self._read_required_chunk(self.chunksize, self.WAVE_CHUNK_ID_WAVE)

            elif chk_id == self.WAVE_CHUNK_ID_FMT:
                # Read fmt chunk
                _num_fmt_bytes = 16
                self._fmt_size = chk_size
                if chk_id != self.WAVE_CHUNK_ID_FMT:
                    raise wavfile.Error('Invalid wave file')
                self._audio_fmt = self._read_signed_int(self.chunksize // 2)
                if self._audio_fmt not in self.valid_formats:
                    raise wavfile.Error('Invalid audio format.')
                self._num_channels = self._read_signed_int(self.chunksize // 2)
                self._sample_rate = self._read_signed_int(self.chunksize)
                self._byte_rate = self._read_signed_int(self.chunksize)
                self._block_align = self._read_signed_int(self.chunksize // 2)
                self._bits_per_sample = self._read_signed_int(self.chunksize // 2)
                if (self._bits_per_sample % 8) != 0:
                    raise wavfile.Error('Invalid bits per sample.')
                remaining = self._fmt_size - _num_fmt_bytes
                if remaining > 0:
                    self._read_chunk(remaining)

            elif chk_id == self.WAVE_CHUNK_ID_DATA:
                # Start to read data chunk
                self._data_size = chk_size
                self._num_frames = self._data_size // self._block_align
                self._data_start = self._fp.tell()
                break

            else:
                # Throw chunk away
                self._read_chunk(chk_size)

        if self._data_start == 0:
            raise wavfile.Error('Cannot find any audio data')

    def close(self):
        """Close the file."""
        if self._should_close_file:
            self._fp.close()
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
        if self._bytes_per_sample == 1:
            signed = False
        else:
            signed = True

        def read_sample():
            return int.from_bytes(self._read_chunk(self._bytes_per_sample), byteorder='little', signed=signed)

        if num_frames is None or num_frames < 0:
            # read all remaining frames
            num_frames = self._num_frames

        # do not try to read past the end
        num_frames = min(num_frames, self._num_frames - self.tell())
        audio = [[0] * self._num_channels for _ in range(num_frames)]

        if num_frames > 0:
            # read the audio
            for i in range(0, num_frames):
                for j in range(0, self._num_channels):
                    audio[i][j] = read_sample()

        return audio

    def _convert_unsigned_int_to_float(self, x):
        """Convert unsigned int to float [-1, 1)"""
        adjust = 2.0 ** (self._bits_per_sample - 1.0)
        return (x - adjust) / adjust

    def _convert_signed_int_to_float(self, x):
        """Convert signed int to float [-1, 1)"""
        return x / (2.0 ** (self._bits_per_sample - 1.0))

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
