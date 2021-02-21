"""
Read/write wave audio files to/from lists of native Python types.

The library is currently limited to PCM (integer) formats but supports arbitrary
precision, including 16-, 24-, 32-, and 64-bit samples.

Usage: reading wave files

    f = wavfile.open(file, 'r')

where file is either a path to a wave file or a pointer to an open file. This
returns a wavfile.wavread.WavRead object with the following properties:
    num_channels    -- The number of audio channels in the stream.
    sample_rate     -- The sampling rate/frequency of the audio stream.
    bits_per_sample -- The number of bits per audio sample.
    num_frames      -- The total number of audio frames in the audio stream. A
                       frame is a block of samples, one for each channel,
                       corresponding to a single sampling point.

The object also has the following methods:
    read_int(N)      -- Read, at most, N frames from the audio stream in their
                        unmodified integer format. The method returns a list of
                        lists with size (N,C), where C is the number of audio
                        channels. Choosing N = None or N < 0 will read all
                        remaining samples.
    read_float(N)    -- This method is identical to read_int() except that it
                        returns the samples as floats in the range [-1, 1).
    seek(N)          -- Move to the Nth frame in the audio stream.
    tell()           -- Return the current frame in the audio stream.
    close()          -- Close the instance.

Usage: writing wave files.

    f = wavfile.open(file, 'w', sample_rate=44100, num_channels=None,
                     bits_per_sample=16)

where sample_rate is the sampling rate for the new file, num_channels is the
number of audio channels, and bits_per_sample is the number of bits used to
encode each sample. If num_channels is unspecified it will be determined
automatically from the first block of samples that are written (see below).
This returns a wavfile.wavread.WavWrite object. The object shares its properties
with the wavfile.wavread.WavRead class. The object also offers the same seek(),
tell(), and close() methods. In addition, the following methods are provided for
writing audio data:
    write(N)         -- Write N frames of integers or floats to the audio file.
                        The data should be contained in a list of lists with
                        size (N,C), where C is the number of audio channels. If
                        the data are floats then they should be in the range
                        [-1, 1). They will be converted automatically. Integers
                        will be written directly.

"""

from wavfile.wavfile import Error, open
from wavfile.version import __VERSION__
