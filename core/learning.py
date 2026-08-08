"""Pure helpers for grading MRQ answers in Learning mode."""

from __future__ import annotations

import json
import re


def _normalise_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def correct_option_indices(
    options: list[str],
    correct_options: str | list[int] | None,
    answer_text: str | None,
) -> list[int]:
    """Return structured correct indices, including legacy single-choice answers."""
    if correct_options:
        try:
            parsed = json.loads(correct_options) if isinstance(correct_options, str) else correct_options
            return sorted({int(i) for i in parsed if 0 <= int(i) < len(options)})
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    normalised_answer = _normalise_text(answer_text)
    if normalised_answer:
        for index, option in enumerate(options):
            if _normalise_text(option) == normalised_answer:
                return [index]
    return []


def classify_answer(
    *,
    q_type: str,
    user_answer,
    options: list[str],
    correct_options: str | list[int] | None,
    answer_text: str | None,
    skipped: bool = False,
) -> str:
    """Classify a submitted answer as correct, partial, incorrect, or skipped."""
    if skipped:
        return "skipped"

    if q_type == "free_text":
        return (
            "correct"
            if _normalise_text(user_answer) == _normalise_text(answer_text)
            else "incorrect"
        )

    correct = set(correct_option_indices(options, correct_options, answer_text))
    if isinstance(user_answer, int):
        selected = {user_answer}
    elif isinstance(user_answer, list):
        selected = {int(i) for i in user_answer}
    else:
        selected = set()

    if selected == correct and correct:
        return "correct"
    if selected & correct:
        return "partial"
    return "incorrect"
