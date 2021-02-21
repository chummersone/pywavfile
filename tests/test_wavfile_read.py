import unittest

import wavfile


class TestWavfileRead(unittest.TestCase):

    filename = "osc_tri.wav"

    def test_file_open_filename(self):
        wfp = wavfile.open(self.filename)
        self.assertEqual(wfp.sample_rate, 44100)
        wfp.close()
        self.assertTrue(wfp._fp.closed)

    def test_file_open_filename_with(self):
        with wavfile.open(self.filename) as wfp:
            fp = wfp
            self.assertEqual(wfp.sample_rate, 44100)
        self.assertTrue(fp._fp.closed)

    def test_file_open_file(self):
        with open(self.filename, "rb") as fp:
            wfp = wavfile.open(fp)
            self.assertEqual(wfp.sample_rate, 44100)
            wfp.close()

    def test_file_open_file_with(self):
        with open(self.filename, "rb") as fp:
            with wavfile.open(fp) as wfp:
                self.assertEqual(wfp.sample_rate, 44100)

    def test_file_num_channels(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.num_channels, 1)

    def test_file_read_num_channels(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(len(wfp.read_int()[0]), 1)

    def test_file_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.num_frames, 4096)

    def test_file_read_num_frames(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(len(wfp.read_int()), 4096)

    def test_file_bits_per_sample(self):
        with wavfile.open(self.filename) as wfp:
            self.assertEqual(wfp.bits_per_sample, 16)

    def test_float_range(self):
        with wavfile.open(self.filename) as wfp:
            audio = wfp.read_float()
            max_abs = max([max([abs(y) for y in x]) for x in audio])
            self.assertTrue(max_abs < 0.7)

    def test_tell(self):
        with wavfile.open(self.filename) as wfp:
            wfp.read_int()
            self.assertEqual(wfp.tell(), 4096)

    def test_seek(self):
        with wavfile.open(self.filename) as wfp:
            wfp.read_int()
            wfp.seek(0)
            self.assertEqual(wfp.tell(), 0)

    def test_read_int_blocks(self):
        with wavfile.open(self.filename) as wfp:
            num_frames = 33
            while True:
                audio = wfp.read_int(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or len(audio) == (wfp.num_frames % num_frames))

    def test_read_float_blocks(self):
        with wavfile.open(self.filename) as wfp:
            num_frames = 33
            while True:
                audio = wfp.read_float(num_frames)
                if len(audio) == 0:
                    break
                else:
                    self.assertTrue(len(audio) == num_frames or len(audio) == (wfp.num_frames % num_frames))


if __name__ == '__main__':
    unittest.main()
