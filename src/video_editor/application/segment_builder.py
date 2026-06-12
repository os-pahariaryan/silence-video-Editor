"""Pure logic to invert silence segments into keep segments."""

from __future__ import annotations

from video_editor.domain.models import EditConfig, KeepSegment, SilenceSegment


def compute_keep_segments(
    silence_segments: list[SilenceSegment],
    total_duration: float,
    config: EditConfig,
) -> list[KeepSegment]:
    """
    Invert silence segments into keep segments with padding applied.

    Silence segments are expanded by padding_before/after so that brief
    audio around speech boundaries is preserved. Resulting keep segments
    shorter than min_segment_duration are dropped.
    """
    if total_duration <= 0:
        return []

    if not silence_segments:
        return [KeepSegment(start=0.0, end=total_duration)]

    # Expand silence regions with padding (we keep less silence)
    expanded: list[tuple[float, float]] = []
    for seg in silence_segments:
        expanded_start = max(0.0, seg.start - config.padding_before)
        expanded_end = min(total_duration, seg.end + config.padding_after)
        expanded.append((expanded_start, expanded_end))

    expanded = _merge_overlapping(expanded)

    keep_segments: list[KeepSegment] = []
    cursor = 0.0

    for silence_start, silence_end in expanded:
        if silence_start > cursor:
            keep_segments.append(KeepSegment(start=cursor, end=silence_start))
        cursor = max(cursor, silence_end)

    if cursor < total_duration:
        keep_segments.append(KeepSegment(start=cursor, end=total_duration))

    return [
        seg
        for seg in keep_segments
        if seg.duration >= config.min_segment_duration
    ]


def _merge_overlapping(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Merge overlapping or adjacent time ranges."""
    if not ranges:
        return []

    sorted_ranges = sorted(ranges, key=lambda r: r[0])
    merged: list[tuple[float, float]] = [sorted_ranges[0]]

    for start, end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged
