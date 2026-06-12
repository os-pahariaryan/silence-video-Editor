"""Tests for segment_builder."""

from video_editor.application.segment_builder import compute_keep_segments
from video_editor.domain.models import EditConfig, SilenceSegment


def _default_config() -> EditConfig:
    return EditConfig(
        min_silence_duration=1.0,
        silence_threshold_db=-35.0,
        padding_before=0.1,
        padding_after=0.1,
        min_segment_duration=0.05,
    )


def test_no_silence_keeps_entire_video():
    config = _default_config()
    result = compute_keep_segments([], total_duration=10.0, config=config)
    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].end == 10.0


def test_single_silence_in_middle():
    config = _default_config()
    silence = [SilenceSegment(start=4.0, end=6.0)]
    result = compute_keep_segments(silence, total_duration=10.0, config=config)
    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].end == 3.9  # 4.0 - padding_before
    assert result[1].start == 6.1  # 6.0 + padding_after
    assert result[1].end == 10.0


def test_full_silence_returns_empty():
    config = _default_config()
    silence = [SilenceSegment(start=0.0, end=10.0)]
    result = compute_keep_segments(silence, total_duration=10.0, config=config)
    assert result == []


def test_overlapping_silence_merged():
    config = _default_config()
    silence = [
        SilenceSegment(start=2.0, end=4.0),
        SilenceSegment(start=3.5, end=6.0),
    ]
    result = compute_keep_segments(silence, total_duration=10.0, config=config)
    assert len(result) == 2
    assert result[0].end == 1.9
    assert result[1].start == 6.1


def test_drops_tiny_segments():
    config = EditConfig(
        min_silence_duration=1.0,
        silence_threshold_db=-35.0,
        padding_before=0.0,
        padding_after=0.0,
        min_segment_duration=0.5,
    )
    silence = [SilenceSegment(start=0.0, end=9.5)]
    result = compute_keep_segments(silence, total_duration=10.0, config=config)
    assert len(result) == 1
    assert result[0].start == 9.5
    assert result[0].duration == 0.5


def test_zero_duration_returns_empty():
    config = _default_config()
    result = compute_keep_segments([], total_duration=0.0, config=config)
    assert result == []
