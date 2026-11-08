"""
Provides test cases for file lifecycle.
"""

import io

import pytest

import wavfile
import wavfile.base
import wavfile.chunk
import wavfile.exception

valid_wav_file = (b'\x52\x49\x46\x46\x2C\x00\x00\x00\x57\x41\x56\x45\x66\x6D\x74\x20\x10\x00\x00'
                  b'\x00\x01\x00\x02\x00\x80\xBB\x00\x00\x00\xEE\x02\x00\x04\x00\x10\x00\x64\x61'
                  b'\x74\x61\x08\x00\x00\x00\x64\x00\x9C\xFF\xC8\x00\x38\xFF')


def test_reader_does_not_close_borrowed_stream():

    fp = io.BytesIO(valid_wav_file)

    with wavfile.open(fp, "r") as wav:
        wav.read()

    assert not fp.closed


def test_writer_does_not_close_borrowed_stream():
    fp = io.BytesIO()

    with wavfile.open(fp, mode="w", num_channels=2) as wav:
        wav.write([[100, 200], [300, 400]])

    assert not fp.closed

    # The WAV should still be readable.
    fp.seek(0)
    with wavfile.open(fp, mode="r") as wav:
        assert wav.num_channels == 2


def test_reader_closes_owned_file(tmp_path):
    path = tmp_path / "test.wav"
    path.write_bytes(valid_wav_file)

    wav = wavfile.open(path, "r")
    fp = wav.fp
    assert fp is not None
    assert not fp.closed

    wav.close()

    assert fp.closed


def test_writer_closes_owned_file(tmp_path):
    path = tmp_path / "test.wav"

    wav = wavfile.open(path, "w", num_channels=2)
    fp = wav.fp

    wav.write([[100, 200], [300, 400]])
    wav.close()

    assert fp is not None
    assert fp.closed
    assert path.stat().st_size > 0


def test_close_is_idempotent(tmp_path):
    path = tmp_path / "test.wav"

    wav = wavfile.open(path, "w", num_channels=2)
    wav.write([[100, 200]])

    wav.close()
    wav.close()

    assert wav.fp is not None
    assert wav.fp.closed


def test_context_manager_closes_on_exception(tmp_path):
    path = tmp_path / "test.wav"
    fp = None
    with pytest.raises(RuntimeError), \
            wavfile.open(path, "w", num_channels=2) as wav:
        fp = wav.fp
        raise RuntimeError("test exception")

    assert fp is not None
    assert fp.closed


def test_reader_closes_file_when_initialisation_fails(tmp_path, monkeypatch):
    path = tmp_path / "invalid.wav"
    path.write_bytes(b"not a WAV file")

    opened = []
    real_open = open

    def tracking_open(*args, **kwargs):
        fp = real_open(*args, **kwargs)
        opened.append(fp)
        return fp

    monkeypatch.setattr("wavfile.base.builtins.open", tracking_open)

    with pytest.raises(wavfile.ReadError):
        wavfile.open(path, "r")

    assert len(opened) == 1
    assert opened[0].closed


def test_writer_closes_file_when_initialisation_fails(tmp_path, monkeypatch):
    opened = []
    real_open = open

    def tracking_open(*args, **kwargs):
        fp = real_open(*args, **kwargs)
        opened.append(fp)
        return fp

    monkeypatch.setattr("wavfile.base.builtins.open", tracking_open)

    def fail_initialisation(self, *args, **kwargs):
        raise RuntimeError("Simulated initialisation failure")

    monkeypatch.setattr(wavfile.wavwrite.WavWrite, "_init_chunks", fail_initialisation)

    with pytest.raises(RuntimeError):
        wavfile.open(tmp_path / "test.wav", "w", num_channels=2)

    assert len(opened) == 1
    assert opened[0].closed


def test_owned_file_closed_when_finalisation_fails(tmp_path, monkeypatch):
    path = tmp_path / "test.wav"

    wav = wavfile.open(path, "w", num_channels=2)
    fp = wav.fp
    assert fp is not None

    def fail_finalisation():
        raise wavfile.WriteError("Simulated finalisation failure")

    monkeypatch.setattr(wav, "_finalise", fail_finalisation)

    with pytest.raises(wavfile.WriteError):
        wav.close()

    assert fp.closed


def test_writer_borrowed_file_remains_open_when_finalisation_fails(monkeypatch):
    fp = io.BytesIO()
    wav = wavfile.open(fp, mode="w", num_channels=2)

    def fail_finalisation():
        raise wavfile.WriteError("Simulated finalisation failure")

    monkeypatch.setattr(wav, "_finalise", fail_finalisation)

    with pytest.raises(wavfile.WriteError):
        wav.close()

    assert not fp.closed


def test_reader_borrowed_file_remains_open_when_initialisation_fails():
    fp = io.BytesIO(b"not a WAV file")

    with pytest.raises(wavfile.ReadError):
        wavfile.open(fp, mode="r")

    assert not fp.closed


def test_reader_except_after_close(tmp_path):
    path = tmp_path / "test.wav"
    path.write_bytes(valid_wav_file)

    with wavfile.open(path, mode="r") as fp:
        fp.read(1)

    assert fp.closed

    with pytest.raises(ValueError):
        fp.read(1)

    with pytest.raises(ValueError):
        fp.seek(0)

    with pytest.raises(ValueError):
        fp.tell()

    with pytest.raises(ValueError), fp:
        fp.seek(0)


def test_writer_except_after_close(tmp_path):
    path = tmp_path / "test.wav"

    with wavfile.open(path, mode="w", num_channels=1) as fp:
        fp.write([[0], [0]])

    assert fp.closed

    with pytest.raises(ValueError):
        fp.write([[0], [0]])

    with pytest.raises(ValueError):
        fp.seek(0)

    with pytest.raises(ValueError):
        fp.tell()

    with pytest.raises(ValueError), fp:
        fp.seek(0)
