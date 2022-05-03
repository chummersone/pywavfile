![python-package](https://github.com/chummersone/pywavfile/actions/workflows/python-package.yml/badge.svg)
![python-publish](https://github.com/chummersone/pywavfile/actions/workflows/python-publish.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/wavfile.svg)](https://pypi.org/project/wavfile/)

# wavfile

A lightweight library to read/write wave audio files to/from lists of native Python types.

The library currently supports PCM (integer) and IEEE float formats, and supports arbitrary integer
precision, including: 16-, 24-, 32-, and 64-bit samples.

## Usage: reading wave files

```
f = wavfile.open(file, 'r')
```

where `file` is either a path to a wave file or a pointer to an open file. This returns a
`wavfile.wavread.WavRead` object with the following properties:
* `num_channels`  
The number of audio channels in the stream.
* `sample_rate`  
The sampling rate/frequency of the audio stream.
* `bits_per_sample`  
The number of bits per audio sample.
* `num_frames`  
The total number of audio frames in the audio stream. A frame is a block of samples, one for each
channel, corresponding to a single sampling point.
* `format`  
The file audio sample format.

The object also has the following methods:
* `read([N])`  
Read, at most, `N` frames from the audio stream in their unmodified native format. The method
returns a list of lists with size `(N,C)`, where `C` is the number of audio channels. Excluding `N`,
choosing `N = None` or `N < 0` will read all remaining samples.
* `read_int([N])`  
This method is identical to `read()` except that it returns the samples as integers using the
specified bit depth.
* `read_float([N])`  
This method is identical to `read()` except that it returns the samples as floats in the range
[-1, 1).
* `iter([N])`  
Similar to `read()` but used in iterator contexts to read successive groups of audio frames.
* `iter_int([N])`  
Similar to `read_int()` but used in iterator contexts to read successive groups of audio frames.
* `iter_float([N])`  
Similar to `read_float()` but used in iterator contexts to read successive groups of audio frames.
* `seek(N [, whence])`  
Move to the `N`<sup>th</sup> frame in the audio stream; `whence` sets the positioning: 0 (default) =
absolute positioning, 1 = relative to current position, 2 = relative to end of last frame.
* `tell()`  
Return the current frame in the audio stream.
* `close()`  
Close the instance.

Alternatively, the following shortcut function is provided:

    audio, sample_rate, bits_per_sample = wavfile.read(file, fmt='int')

where `fmt` is `'int'`, `'float'`, or `'native'`; and `audio` is the audio data. The function reads
all audio data in the file.

## Usage: writing wave files

```
f = wavfile.open(file, 'w',
                 sample_rate=44100,
                 num_channels=None,
                 bits_per_sample=16,
                 fmt=wavfile.chunk.WavFormat.PCM)
```

where `sample_rate` is the sampling rate for the new file, `num_channels` is the number of audio
channels, `bits_per_sample` is the number of bits used to encode each sample, and `fmt` is the audio
sample format. If `num_channels` is unspecified it will be determined automatically from the first
block of samples that are written (see below). This returns a `wavfile.wavwrite.WavWrite` object.
The object shares its properties with the `wavfile.wavread.WavRead` class. The object also offers
the same `seek()`, `tell()`, and `close()` methods. In addition, the following methods are provided
for writing audio data:
* `write(audio)`  
Write frames of audio data to the audio file. The data should be contained in a list of lists with
size `(N,C)`, where `N` is the number of frames and `C` is the number of audio channels. The data
may be `int` or `float`. The data may be converted if they do match the format of the destination
file.
  
Alternatively, the following shortcut function is provided:

    wavfile.write(file,
                  audio,
                  sample_rate=44100,
                  bits_per_sample=16,
                  fmt=wavfile.chunk.WavFormat.PCM)

where `audio` is the audio data to write to the file.

## Installation

From source:
```
python -m pip install -e --user .
```

From PyPI:
```
python -m pip install --user wavfile
```

## License

`wavfile` is available under the MIT license. See LICENSE.txt for more information.
