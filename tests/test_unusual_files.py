"""
Provides test cases for unusual wav files from the fixture.
"""

import json
from pathlib import Path

import pytest
from test_module import get_file_path

import wavfile

ROOT = Path(__file__).parents[1]
FIXTURES = Path(get_file_path("fixtures/unusual"))
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text())


@pytest.mark.parametrize(
    "filename, metadata",
    MANIFEST["fixtures"].items(),
    ids=lambda item: item if isinstance(item, str) else None,
)
def test_fixture_is_present_and_matches_manifest(filename, metadata):
    path = FIXTURES / filename
    assert path.is_file()
    assert path.stat().st_size == metadata["size_bytes"]


@pytest.mark.parametrize("filename, metadata", MANIFEST["fixtures"].items())
def test_reader_behaviour(filename, metadata):
    outcome = ""
    try:
        with wavfile.open(FIXTURES / filename):
            outcome = "valid"
    except wavfile.ReadError:
        outcome = "ReadError"

    expected = metadata["expected"]
    if expected in ("valid", "ReadError"):
        assert outcome == expected
    else:
        pytest.skip(f"Resolve policy expectation: {expected}")
