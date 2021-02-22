import unittest

import wavfile


class TestWavfileWrite(unittest.TestCase):

    sample_rate = 48000
    bits_per_sample = 24
    unsigned_bits_per_sample = 8
    num_channels = 2
    audio_data_int = [
        [0, 0],
        [256, 256],
        [512, 512],
        [-256, -256],
        [-512, -512],
    ]
    audio_data_float = [
        [0.0, 0.0],
        [-1.0, -1.0],
        [0.0, 0.0],
        [1.0, 1.0],
        [0.0, 0.0],
    ]
    audio_data_short = [
        [0, 0],
        [255, 255],
        [127, 127],
        [63, 63],
        [255, 255],
    ]
    audio_data_short_as_float = [
        [-1.0, -1.0],
        [1.0, 1.0],
        [0.0, 0.0],
        [-0.5, -0.5],
        [1.0, 1.0],
    ]
    filename = "tmp.wav"

    def test_write_audio_data(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_int)
        wfp.close()
        self.assertEqual(wfp.sample_rate, self.sample_rate)
        self.assertEqual(wfp.bits_per_sample, self.bits_per_sample)
        self.assertEqual(wfp.num_channels, self.num_channels)
        self.assertEqual(wfp.num_frames, len(self.audio_data_int))

    def test_write_read_fmt(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_int)
        wfp.close()
        wfp = wavfile.open(self.filename, 'r')
        self.assertEqual(wfp.sample_rate, self.sample_rate)
        self.assertEqual(wfp.bits_per_sample, self.bits_per_sample)
        self.assertEqual(wfp.num_channels, self.num_channels)
        self.assertEqual(wfp.num_frames, len(self.audio_data_int))
        wfp.close()

    def test_write_read_data_int(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_int)
        wfp.close()
        wfp = wavfile.open(self.filename, 'r')
        audio = wfp.read_int()
        self.assertEqual(len(audio), len(self.audio_data_int))
        self.assertEqual(len(audio[0]), len(self.audio_data_int[0]))
        for i in range(0, len(audio)):
            for j in range(0, len(audio[0])):
                self.assertEqual(audio[i][j], self.audio_data_int[i][j])
        wfp.close()

    def test_write_read_data_float(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_float)
        wfp.close()
        wfp = wavfile.open(self.filename, 'r')
        audio = wfp.read_float()
        self.assertEqual(len(audio), len(self.audio_data_int))
        self.assertEqual(len(audio[0]), len(self.audio_data_int[0]))
        for i in range(0, len(audio)):
            for j in range(0, len(audio[0])):
                self.assertAlmostEqual(audio[i][j], self.audio_data_float[i][j],
                                       delta=(2.0 ** (-self.bits_per_sample + 1)))
        wfp.close()

    def test_write_read_data_unsigned(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.unsigned_bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_short)
        wfp.close()
        wfp = wavfile.open(self.filename, 'r')
        audio = wfp.read_int()
        self.assertEqual(len(audio), len(self.audio_data_short))
        self.assertEqual(len(audio[0]), len(self.audio_data_short[0]))
        for i in range(0, len(audio)):
            for j in range(0, len(audio[0])):
                self.assertEqual(audio[i][j], self.audio_data_short[i][j])
        wfp.close()

    def test_write_read_data_unsigned_to_float(self):
        wfp = wavfile.open(self.filename, 'w',
                           sample_rate=self.sample_rate,
                           bits_per_sample=self.unsigned_bits_per_sample,
                           num_channels=self.num_channels)
        wfp.write(self.audio_data_short)
        wfp.close()
        wfp = wavfile.open(self.filename, 'r')
        audio = wfp.read_float()
        self.assertEqual(len(audio), len(self.audio_data_short))
        self.assertEqual(len(audio[0]), len(self.audio_data_short[0]))
        for i in range(0, len(audio)):
            for j in range(0, len(audio[0])):
                self.assertAlmostEqual(audio[i][j], self.audio_data_short_as_float[i][j],
                                       delta=(2.0 ** (-self.unsigned_bits_per_sample + 1)))
        wfp.close()


if __name__ == '__main__':
    unittest.main()
