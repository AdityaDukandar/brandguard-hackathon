"""Simple fake-score calculation utilities.

This module defines helpers that combine individual risk signals
(e.g., text risk, icon similarity) into a single "fake score".
"""

from __future__ import annotations

from typing import Iterable


def calculate_fake_score(risks: Iterable[float]) -> float:
    """Calculate a simple fake score as the average of risk values.

    Parameters
    ----------
    risks:
        Iterable of individual risk scores, typically in the range [0, 100]
        (e.g., text similarity risk, icon similarity percentage, etc.).

    Returns
    -------
    float
        The arithmetic mean of all provided risks, or ``0.0`` if ``risks``
        is empty. The result is clamped to the range [0.0, 100.0].
    """

    total = 0.0
    count = 0
    for value in risks:
        # Ignore non-finite or clearly invalid inputs.
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue

        if v != v:  # NaN check
            continue

        total += v
        count += 1

    if count == 0:
        return 0.0

    avg = total / count

    # Clamp to a sensible range.
    if avg < 0.0:
        return 0.0
    if avg > 100.0:
        return 100.0
    return avg
