#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read/write wave audio files to/from lists of native Python types.

The library currently supports PCM (integer) and IEEE float formats, and supports arbitrary integer
precision, including: 16-, 24-, 32-, and 64-bit samples.
"""
import os.path
from typing import Dict, IO, List, Optional, Tuple, Union

from . import chunk
from . import wavread
from . import wavwrite
from .exception import Error, ReadError, WriteError
from .version import __VERSION__


def open(f: Union[str, os.PathLike, IO], mode: Optional[str] = None, sample_rate: int = 44100,
         num_channels: Optional[int] = None, bits_per_sample: int = 16,
         fmt: chunk.WavFormat = chunk.WavFormat.PCM) -> Union[wavread.WavRead, wavwrite.WavWrite]:
    """
    Open the wave file.

    If writing and ``num_channels`` is unspecified, it is determined automatically from the first
    block of samples.

    The format code is either ``wavfile.chunk.WavFormat.PCM``,
    ``wavfile.chunk.WavFormat.IEEE_FLOAT``, or ``wavfile.chunk.WavFormat.EXTENSIBLE``. The
    extensible code corresponds to a variation of the wave file format intended for audio with: a
    bit depth of greater than 16 bits, or more than two channels. The file will be updated
    automatically to use the extensible format as appropriate. If the extensible format is specified
    explicitly, then the audio data will be PCM encoded.

    :param f: Either a path to a wave file or a pointer to an open file.
    :param mode: Open the file for reading ('r', 'rb') or writing ('w', 'wb').
    :param sample_rate: The sample rate for the new file (write only).
    :param num_channels: The number of audio channels for the new file (write only).
    :param bits_per_sample: The number of bits to encode each audio sample (write only).
    :param fmt: The format code (write only) (:class:`chunk.WavFormat`)
    :return: Returns a :class:`wavread.WavRead` object or :class:`wavwrite.WavWrite` object.
    """
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return wavread.WavRead(f)
    elif mode in ('w', 'wb'):
        if not isinstance(fmt, chunk.WavFormat):
            raise WriteError('Invalid format')
        return wavwrite.WavWrite(f, sample_rate=sample_rate, num_channels=num_channels,
                                 bits_per_sample=bits_per_sample, fmt=fmt)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")


def read(path: Union[str, os.PathLike], fmt: str = 'int') -> \
        Tuple[List[List[Union[int, float]]], int, int]:
    """
    Shortcut function to read a wave file. The audio can be read directly (``fmt='native'``),
    converted to integers (``fmt='int'``), or converted to floating point (``fmt='float'``).

    :param path: Path to the wave audio file.
    :param fmt: Read the file as 'int', 'float', or 'native'.
    :return: The audio data, the sample rate, and the bit depth.
    """
    with open(path, 'r') as wf:
        wf: wavread.WavRead
        fs = wf.sample_rate
        bits_per_sample = wf.bits_per_sample
        fmt_methods = {
            'int': wf.read_int,
            'float': wf.read_float,
            'native': wf.read,
        }
        audio_data = None
        try:
            audio_data = fmt_methods[fmt]()
        except KeyError:
            raise Error('Unknown format. Options are: ' + ', '.join(fmt_methods.keys()))

    return audio_data, fs, bits_per_sample


def write(path: Union[str, os.PathLike], audio_data: List[List[Union[int, float]]],
          sample_rate: int = 44100, bits_per_sample: int = 16,
          fmt: chunk.WavFormat = chunk.WavFormat.PCM,
          metadata: Optional[Dict[str, Union[int, str]]] = None) -> None:
    """
    Shortcut function to write a wave file. The data should be contained in a list of lists with
    size (N,C), where C is the number of audio channels. The data may be int or float. The data may
    be converted if they do match the format of the destination file.

    Metadata can be added to the wav file by providing an appropriate dict. See chunk.InfoItem for a
    list of valid metadata fields.

    :param path: Path to the newly created wave file.
    :param audio_data: The data to be written to the file.
    :param sample_rate: The sample rate for the new file.
    :param bits_per_sample: The number of bits to encode each audio sample (write only).
    :param fmt: The audio format (:class:`chunk.WavFormat`)
    :param metadata: The metadata to write, provided as a dictionary.
    """
    with open(path, 'w', sample_rate=sample_rate, bits_per_sample=bits_per_sample, fmt=fmt) as wf:
        wf: wavwrite.WavWrite
        if metadata is not None:
            wf.add_metadata(**metadata)
        wf.write(audio_data)


def split(path: Union[str, os.PathLike]) -> None:
    """
    Split a multichannel wave file in to multiple mono wave files.

    :param path: Path to the multichannel wave file.
    """

    with open(path, 'r') as wfp:
        wfp: wavread.WavRead
        num_channels = wfp.num_channels

        # filenames for new files
        filenames = []
        base, ext = os.path.splitext(path)
        for i in range(num_channels):
            filenames.append('{:s}_{:02d}{:s}'.format(base, i, ext))

        # open the wave files for writing
        outs = []
        for i in range(num_channels):
            outs.append(
                wavwrite.WavWrite(
                    filenames[i],
                    sample_rate=wfp.sample_rate,
                    num_channels=1,
                    bits_per_sample=wfp.bits_per_sample,
                    fmt=wfp.format
                )
            )

        # read the input file and write to the output files
        for audio in wfp.iter(1):
            for i in range(num_channels):
                outs[i].write([[audio[0][i]]])

        # close the output files
        for i in range(num_channels):
            outs[i].close()


def join(filename: Union[str, os.PathLike], *paths: Union[str, os.PathLike]) -> None:
    """
    Join several wave files in to a single multichannel wave file.

    The resulting wave file's duration will be equal to the longest wave file, with other shorter
    channels being appended with zeros. The order of the channels will match the order of the
    specified files.

    :param filename: Name of the output file.
    :param paths: Paths to the wave files.
    """
    # determine file properties
    sample_rate = None
    num_frames = []
    bits_per_sample = 0
    num_channels = 0
    for file in paths:
        with open(file, 'r') as fp:
            # check matching sample rates
            if sample_rate is None:
                sample_rate = fp.sample_rate
            else:
                if fp.sample_rate != sample_rate:
                    raise ReadError('Sample rates of input files do not match')
            num_frames.append(fp.num_frames)
            bits_per_sample = max(bits_per_sample, fp.bits_per_sample)
            num_channels += fp.num_channels

    # join files
    with open(filename, 'w', bits_per_sample=bits_per_sample, sample_rate=sample_rate,
              num_channels=num_channels) as wfp:
        wfp: wavwrite.WavWrite

        # open files
        file_pointers = []
        for file in paths:
            file_pointers.append(open(file, 'r'))

        # write each frame
        for frame_num in range(max(num_frames)):
            new_frame: List[float] = [0.0] * num_channels
            channel = 0
            for file_index, rfp in enumerate(file_pointers):
                rfp: wavread.WavRead
                # get samples if there are any
                if frame_num < num_frames[file_index]:
                    frame = rfp.read_float(1)[0]
                    for ch in range(rfp.num_channels):
                        new_frame[channel] = frame[ch]
                        channel += 1
                else:
                    # keep zeros
                    channel += rfp.num_channels
            wfp.write_float([new_frame])

        # close files
        for rfp in file_pointers:
            rfp.close()
