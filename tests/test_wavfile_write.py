import unittest

import wavfile


class TestWavfileWrite(unittest.TestCase):

    def run_test(self, audio_data_in, read_callback, sample_rate,
                 bits_per_sample, num_channels, reference=None):
        filename = "tmp.wav"
        with wavfile.open(filename, 'w',
                          sample_rate=sample_rate,
                          bits_per_sample=bits_per_sample,
                          num_channels=num_channels) as wfp:
            wfp.write(audio_data_in)

        with wavfile.open(filename, 'r') as wfp:
            audio_out = getattr(wfp, read_callback)()

        if reference is None:
            reference = audio_data_in

        self.assertEqual(len(reference), len(audio_out))
        self.assertEqual(len(reference[0]), len(audio_out[0]))
        for i in range(0, len(audio_out)):
            for j in range(0, len(audio_out[0])):
                self.assertAlmostEqual(audio_out[i][j], reference[i][j],
                                       delta=(2.0 ** (-bits_per_sample + 1)))

        self.assertEqual(wfp.sample_rate, sample_rate)
        self.assertEqual(wfp.bits_per_sample, bits_per_sample)
        self.assertEqual(wfp.num_channels, num_channels)
        self.assertEqual(wfp.num_frames, len(reference))

    def test_read_write_audio_short_int_1(self):
        audio_data_in = [
            [0, 0],
            [255, 255],
            [127, 127],
            [63, 63],
            [255, 255],
        ]
        read_callback = "read_int"
        sample_rate = 44100
        bits_per_sample = 8
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_short_float_1(self):
        audio_data_in = [
            [0, 0],
            [255, 255],
            [127, 127],
            [63, 63],
            [255, 255],
        ]
        reference = [
            [-1.0, -1.0],
            [1.0, 1.0],
            [0.0, 0.0],
            [-0.5, -0.5],
            [1.0, 1.0],
        ]
        read_callback = "read_float"
        sample_rate = 44100
        bits_per_sample = 8
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]), reference)

    def test_read_write_audio_int16(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 16
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_int24(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 24
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_int32(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 24
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_int64(self):
        audio_data_in = [
            [0, 0],
            [256, 512],
            [512, 256],
            [-256, -512],
            [-512, -256],
        ]
        read_callback = "read_int"
        sample_rate = 48000
        bits_per_sample = 64
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_int24_mono(self):
        audio_data_in = [
            [0],
            [256],
            [512],
            [-256],
            [-512],
        ]
        read_callback = "read_int"
        sample_rate = 32000
        bits_per_sample = 24
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))

    def test_read_write_audio_int24_6channel(self):
        audio_data_in = [
            [0, 1, 2, 3, 4, 5],
            [256, 255, 254, 253, 252, 251],
            [512, 513, 514, 515, 516, 517],
            [0x7FFFFF, -1, -2**23, 0x3A3A3A, 0x0, 0x00DEAD],
            [5, 4, 3, 2, 1, 0],
            [0, 1, 2, 3, 4, 5],
            [256, 255, 254, 253, 252, 251],
            [512, 513, 514, 515, 516, 517],
            [0x7FFFFF, -1, -2**23, 0x3A3A3A, 0x0, 0x00DEAD],
            [5, 4, 3, 2, 1, 0],
        ]
        read_callback = "read_int"
        sample_rate = 96000
        bits_per_sample = 24
        self.run_test(audio_data_in, read_callback, sample_rate,
                      bits_per_sample, len(audio_data_in[0]))


if __name__ == '__main__':
    unittest.main()
