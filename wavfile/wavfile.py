import wavfile.wavread
import wavfile.wavwrite


class Error(Exception):
    pass


def open(f, mode=None, sample_rate=44100, num_channels=None, bits_per_sample=16):
    """
    Open the wave file.
    :param f: Either a path to a wave file or a pointer to an open file.
    :param mode: Open the file for reading ('r', 'rb') or writing ('w', 'wb').
    Modes 'r' and 'w' are identical to 'rb' and 'wb', respectively.
    :param sample_rate: The sample rate for the new file. Only applicable when
    writing an audio file.
    :param num_channels: The number of audio channels for the new file. If
    unspecified, the parameter will be determined from the first block of
    samples. Only applicable when writing an audio file.
    :param bits_per_sample: The number of bits to encode each audio sample. Only
    applicable when writing an audio file.
    :return: For reading, returns a wavfile.wavread.WavRead object; for writing,
    returns a wavfile.wavwrite.WavWrite object.
    """
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return wavfile.wavread.WavRead(f)
    elif mode in ('w', 'wb'):
        return wavfile.wavwrite.WavWrite(f, sample_rate=sample_rate, num_channels=num_channels,
                                         bits_per_sample=bits_per_sample)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")
