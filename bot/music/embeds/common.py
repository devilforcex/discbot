"""Common embed helpers."""

from __future__ import annotations


def format_duration(milliseconds: int) -> str:
    if not milliseconds or milliseconds <= 0:
        return "0:00"
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def build_progress_bar(
    current: int,
    total: int,
    length: int = 18,
    bar_len: int | None = None,
) -> str:
    size = bar_len if bar_len is not None else length
    if total <= 0:
        return "─" * size
    ratio = max(0.0, min(1.0, current / total)) if total else 0
    dot_pos = min(size - 1, max(0, int(ratio * (size - 1))))
    bar_chars = []
    for i in range(size):
        if i == dot_pos:
            bar_chars.append("●")
        elif i < dot_pos:
            bar_chars.append("━")
        else:
            bar_chars.append("─")
    return "".join(bar_chars)
