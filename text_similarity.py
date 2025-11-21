"""Text similarity utilities for assessing fake vs real app names.

This module exposes `calculate_text_risk`, which produces a 0-100 risk score
based on Levenshtein distance via `thefuzz`.
"""

from __future__ import annotations

from typing import Union

try:  # Import thefuzz with a clear failure mode if missing.
    from thefuzz import fuzz
except ImportError as exc:  # pragma: no cover - environment/config error
    fuzz = None  # type: ignore[assignment]
    THEFUZZ_IMPORT_ERROR = exc
else:
    THEFUZZ_IMPORT_ERROR = None


def _normalize_text(value: Union[str, None]) -> str:
    """Normalize text inputs to safe strings for comparison."""

    if value is None:
        return ""
    return str(value)


def calculate_text_risk(fake_name: Union[str, None], real_name: Union[str, None]) -> int:
    """Compute a 0-100 risk score for a fake app name vs a real name.

    The score is derived from Levenshtein-based similarity via ``thefuzz.fuzz.ratio``:

    - Identical strings → 100 (highest risk: perfect imitation).
    - Completely different strings → 0 (no textual similarity).

    Parameters
    ----------
    fake_name:
        The candidate or fake app name.
    real_name:
        The legitimate app name being impersonated.

    Returns
    -------
    int
        Risk score in the range [0, 100].
    """

    if THEFUZZ_IMPORT_ERROR is not None or fuzz is None:  # pragma: no cover
        raise RuntimeError(
            "thefuzz is not installed. Install it with 'pip install thefuzz' "
            "to enable text similarity scoring."
        ) from THEFUZZ_IMPORT_ERROR

    fake_normalized = _normalize_text(fake_name)
    real_normalized = _normalize_text(real_name)

    # If both are empty after normalization, treat as no risk.
    if not fake_normalized and not real_normalized:
        return 0

    similarity = fuzz.ratio(fake_normalized, real_normalized)

    # fuzz.ratio already returns an integer in [0, 100], where 100 means
    # identical strings. We interpret this directly as "risk".
    score = int(similarity)

    # Clamp just in case a future version returns values slightly outside bounds.
    return max(0, min(100, score))
