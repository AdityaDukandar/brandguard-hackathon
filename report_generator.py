"""PDF report generation utilities for BrandGuard.

This module uses `reportlab` to generate a professional-looking takedown
letter addressed to the Google Play Legal Team.
"""

from __future__ import annotations

import datetime as _dt
import os
import textwrap
from typing import Any, Dict

try:  # Import reportlab with a clear failure mode if missing.
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
except ImportError as exc:  # pragma: no cover - environment/config error
    LETTER = None  # type: ignore[assignment]
    canvas = None  # type: ignore[assignment]
    REPORTLAB_IMPORT_ERROR = exc
else:
    REPORTLAB_IMPORT_ERROR = None

import tempfile


def _wrap_paragraph(text: str, width: int = 88) -> list[str]:
    """Simple word-wrapping helper for PDF text objects."""

    return textwrap.wrap(text, width=width) if text else [""]


def generate_takedown_pdf(apk_data: Dict[str, Any], fake_score: float) -> str:
    """Generate a takedown-request PDF letter.

    Parameters
    ----------
    apk_data:
        Dictionary containing at least ``package_name`` and optionally
        other metadata such as ``app_name`` and ``certificate_hash``.
    fake_score:
        Numeric fake score (0-100) used as evidence in the letter.

    Returns
    -------
    str
        Filesystem path to the generated PDF.
    """

    if REPORTLAB_IMPORT_ERROR is not None or LETTER is None or canvas is None:  # pragma: no cover
        raise RuntimeError(
            "reportlab is not installed. Install it with 'pip install reportlab' "
            "to enable PDF report generation."
        ) from REPORTLAB_IMPORT_ERROR

    package_name = apk_data.get("package_name") or "<unknown package>"
    app_name = apk_data.get("app_name") or "(unknown app name)"
    certificate_hash = apk_data.get("certificate_hash") or "(not available)"

    # Clamp and format the fake score for display.
    try:
        score_value = float(fake_score)
    except (TypeError, ValueError):
        score_value = 0.0
    if score_value < 0:
        score_value = 0.0
    if score_value > 100:
        score_value = 100.0

    today_str = _dt.date.today().strftime("%B %d, %Y")

    # Create a temporary PDF file.
    fd, pdf_path = tempfile.mkstemp(prefix="takedown_", suffix=".pdf")
    os.close(fd)

    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    width, height = LETTER

    margin_x = 72  # 1 inch
    top_y = height - 72

    text_obj = c.beginText()
    text_obj.setTextOrigin(margin_x, top_y)
    text_obj.setFont("Helvetica", 11)

    # Header and recipient
    for line in [
        today_str,
        "",
        "Google Play Legal Team",
        "Google LLC",
        "1600 Amphitheatre Parkway",
        "Mountain View, CA 94043",
        "",
        "Subject: Takedown Request for Infringing Application",
        "",
        "To the Google Play Legal Team:",
        "",
    ]:
        text_obj.textLine(line)

    # Body paragraphs
    intro = (
        "I am writing to formally notify you of a mobile application listed on the "
        "Google Play Store that appears to infringe on our brand rights and has "
        "a high risk of misleading users. The application identified by package "
        f"name '{package_name}' (displayed to users as '{app_name}') is not an "
        "authorized or official version of our product."
    )

    analysis = (
        "Using the BrandGuard Fake App Detector, we evaluated this application "
        f"and obtained a Fake Score of {score_value:.1f} out of 100. This score "
        "is computed from independent similarity signals (including app name and "
        "icon likeness) and indicates a strong likelihood that this app is "
        "attempting to impersonate our official brand."
    )

    request_paragraph = (
        "In light of this evidence, we respectfully request that Google Play "
        "review this application and take appropriate enforcement action, "
        "including removal from the store if your policies deem it to be "
        "infringing or misleading. We believe prompt action is necessary to "
        "protect users from potential confusion, fraud, or abuse."
    )

    evidence_paragraph = (
        "For your reference, a subset of the technical indicators supporting this "
        "request includes the following:"
    )

    closing = (
        "Thank you for your attention to this matter and for your ongoing work "
        "to keep the Google Play ecosystem safe for users and rights holders. "
        "If you require any additional information or supporting documentation, "
        "please do not hesitate to contact us."
    )

    for paragraph in [intro, "", analysis, "", request_paragraph, "", evidence_paragraph]:
        if paragraph:
            for line in _wrap_paragraph(paragraph):
                text_obj.textLine(line)
        text_obj.textLine("")

    # Bullet-style technical summary
    bullets = [
        f"• Package name under review: {package_name}",
        f"• Display name observed in metadata: {app_name}",
        f"• BrandGuard Fake Score: {score_value:.1f} / 100",
        f"• Signing certificate hash (if available): {certificate_hash}",
    ]
    for bullet in bullets:
        for line in _wrap_paragraph(bullet, width=90):
            text_obj.textLine(line)
    text_obj.textLine("")

    # Closing section
    for paragraph in [closing, "", "Sincerely,", "", "BrandGuard Enforcement Team"]:
        if paragraph:
            for line in _wrap_paragraph(paragraph):
                text_obj.textLine(line)
        else:
            text_obj.textLine("")

    c.drawText(text_obj)
    c.showPage()
    c.save()

    return pdf_path
