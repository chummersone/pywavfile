|GitHub| |GitHub Workflow Status (event)| |rtd| |Coveralls| |GitHub release
(latest by date)| |PyPI| |PyPI - Python Version|

.. |GitHub| image:: https://img.shields.io/github/license/chummersone/pywavfile
.. |GitHub Workflow Status (event)| image:: https://img.shields.io/github/workflow/status/chummersone/pywavfile/wavfile%20CI?event=push&logo=github&logoColor=white
.. |rtd| image:: https://img.shields.io/readthedocs/pywavfile/latest?logo=readthedocs&logoColor=white
   :alt: Read the Docs (version)
   :target: https://pywavfile.readthedocs.io
.. |Coveralls| image:: https://img.shields.io/coveralls/github/chummersone/pywavfile?logo=coveralls&logoColor=white
   :target: https://coveralls.io/github/chummersone/pywavfile
.. |GitHub release (latest by date)| image:: https://img.shields.io/github/v/release/chummersone/pywavfile?logo=github&logoColor=white
.. |PyPI| image:: https://img.shields.io/pypi/v/wavfile?logo=pypi&logoColor=white
   :target: https://pypi.org/project/wavfile/
.. |PyPI - Python Version| image:: https://img.shields.io/pypi/pyversions/wavfile?logo=python&logoColor=white

.. |wavfile.open| replace:: ``wavfile.open``
.. |WavRead| replace:: ``wavfile.wavread.WavRead``
.. |num_channels| replace:: ``num_channels``
.. |sample_rate| replace:: ``sample_rate``
.. |bits_per_sample| replace:: ``bits_per_sample``
.. |num_frames| replace:: ``num_frames``
.. |duration| replace:: ``duration``
.. |hms| replace:: ``hms``
.. |format| replace:: ``format``
.. |metadata| replace:: ``metadata``
.. |read| replace:: ``read()``
.. |readN| replace:: ``read([N])``
.. |read_int| replace:: ``read_int()``
.. |read_intN| replace:: ``read_int([N])``
.. |read_float| replace:: ``read_float()``
.. |read_floatN| replace:: ``read_float([N])``
.. |iter| replace:: ``iter()``
.. |iterN| replace:: ``iter([N])``
.. |iter_intN| replace:: ``iter_int([N])``
.. |iter_floatN| replace:: ``iter_float([N])``
.. |seek| replace:: ``seek()``
.. |seekN| replace:: ``seek(N [, whence])``
.. |tell| replace:: ``tell()``
.. |close| replace:: ``close()``
.. |wavfile.read| replace:: ``wavfile.read``
.. |WavWrite| replace:: ``wavfile.wavwrite.WavWrite``
.. |write| replace:: ``write(audio)``
.. |write_int| replace:: ``write_int(audio)``
.. |write_float| replace:: ``write_float(audio)``
.. |add_metadata| replace:: ``add_metadata(**kwargs)``
.. |wavfile.write| replace:: ``wavfile.write``

.. github-only-above-here

wavfile
=======

A lightweight package to read/write wave audio files to/from lists of
native Python types.

The package currently supports PCM (integer) and IEEE float formats, and
supports arbitrary integer precision, including: 16-, 24-, 32-, and
64-bit samples.

View online documentation at https://pywavfile.readthedocs.io/.

Usage: reading wave files
-------------------------

The package provides |wavfile.open| to open audio files for reading and
writing. For reading::

   f = wavfile.open(file, 'r')

where ``file`` is either a path to a wave file or a pointer to an open
file. This returns a |WavRead| object with the following properties:

|num_channels|
  The number of audio channels in the stream.

|sample_rate|
  The sampling rate/frequency of the audio stream.

|bits_per_sample|
  The number of bits per audio sample.

|num_frames|
  The total number of audio frames in the audio stream. A frame is a
  block of samples, one for each channel, corresponding to a single
  sampling point.

|duration|
  The duration of the audio file in seconds.

|hms|
  The duration of the audio file formatted as hh:mm:ss.tt.

|format|
  The file audio sample format.

|metadata|
  A dictionary containing metadata encoded in the file.

The object also has the following methods:

|readN|
  Read, at most, ``N`` frames from the audio stream in their unmodified
  native format. The method returns a list of lists with size
  ``(N,C)``, where ``C`` is the number of audio channels. Excluding
  ``N``, choosing ``N = None`` or ``N < 0`` will read all remaining
  samples.

|read_intN|
  This method is identical to |read| except that it returns the samples
  as integers using the specified bit depth.

|read_floatN|
  This method is identical to |read| except that it returns the samples
  as floats in the range [-1, 1).

|iterN|
  Similar to |read| but used in iterator contexts to read successive
  groups of audio frames.

|iter_intN|
  Similar to |read_int| but used in iterator contexts to read successive
  groups of audio frames.


|iter_floatN|
  Similar to |read_float| but used in iterator contexts to read
  successive groups of audio frames.

|seekN|
  Move to the ``N``\ th frame in the audio stream; ``whence`` sets the
  positioning: 0 (default) = absolute positioning, 1 = relative to
  current position, 2 = relative to end of last frame.

|tell|
  Return the current frame in the audio stream.

|close|
  Close the instance.

Alternatively, the |wavfile.read| shortcut function is provided::

   audio, sample_rate, bits_per_sample = wavfile.read(file, fmt='int')

where ``fmt`` is ``'int'``, ``'float'``, or ``'native'``; and ``audio``
is the audio data. The function reads all audio data in the file.

Usage: writing wave files
-------------------------

::

   f = wavfile.open(file, 'w',
                    sample_rate=44100,
                    num_channels=None,
                    bits_per_sample=16,
                    fmt=wavfile.chunk.WavFormat.PCM)

where ``sample_rate`` is the sampling rate for the new file,
``num_channels`` is the number of audio channels, ``bits_per_sample`` is
the number of bits used to encode each sample, and ``fmt`` is the audio
sample format. If ``num_channels`` is unspecified it will be determined
automatically from the first block of samples that are written (see
below). This returns a |WavWrite| object. The object shares its
properties with the |WavRead| class. The object also offers the same
|seek|, |tell|, and |close| methods. In addition, the following methods
are provided for writing audio data:

|write|
  Write frames of audio data to the audio file. The data should be
  contained in a list of lists with size ``(N,C)``, where ``N`` is the
  number of frames and ``C`` is the number of audio channels. The data
  may be ``int`` or ``float``. The data may be converted if they do
  match the format of the destination file.

|write_int|
  Write frames of integer audio data to the audio file. The data may be
  converted if they do match the format of the destination file.

|write_float|
  Write frames of float audio data to the audio file. The data may be
  converted if they do match the format of the destination file.

|add_metadata|
  Add metadata to the .wav file.

Alternatively, the |wavfile.write| shortcut function is provided::

   wavfile.write(file,
                 audio,
                 sample_rate=44100,
                 bits_per_sample=16,
                 fmt=wavfile.chunk.WavFormat.PCM,
                 metadata=None)

where ``audio`` is the audio data to write to the file.

Installation
------------

From source::

   python -m pip install -e --user .

From PyPI::

   python -m pip install --user wavfile

License
-------

``wavfile`` is available under the MIT license. See LICENSE.txt for more
information.
