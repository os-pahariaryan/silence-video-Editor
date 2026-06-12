"""Tests for FFmpeg silencedetect output parser."""

from video_editor.infrastructure.ffmpeg_detector import parse_silencedetect_output


SAMPLE_STDERR = """
[silencedetect @ 0x55a] silence_start: 1.5
[silencedetect @ 0x55a] silence_end: 3.2 | silence_duration: 1.7
[silencedetect @ 0x55a] silence_start: 7.0
[silencedetect @ 0x55a] silence_end: 10.5 | silence_duration: 3.5
"""


def test_parse_multiple_segments():
    segments = parse_silencedetect_output(SAMPLE_STDERR)
    assert len(segments) == 2
    assert segments[0].start == 1.5
    assert segments[0].end == 3.2
    assert segments[1].start == 7.0
    assert segments[1].end == 10.5


def test_parse_empty_output():
    assert parse_silencedetect_output("") == []


def test_parse_unclosed_silence_ignored():
    stderr = "[silencedetect @ 0x55a] silence_start: 5.0\n"
    assert parse_silencedetect_output(stderr) == []
