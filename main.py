"""FastAPI application for fake app risk assessment.

This service exposes an endpoint that accepts an APK upload along with
reference information and returns extracted metadata plus a simple
"fake score" derived from text and icon similarity signals.
"""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from apk_scanner import extract_apk_data
from fake_score import calculate_fake_score
from icon_matcher import calculate_icon_similarity
from text_similarity import calculate_text_risk

app = FastAPI(title="BrandGuard Fake App Detector", version="0.1.0")

# Template renderer and static file mounting
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main HTML interface."""

    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze-apk")
async def analyze_apk(
    apk_file: UploadFile = File(..., description="APK file to analyze"),
    real_name: str = "",
    reference_icon_path: Optional[str] = None,
) -> JSONResponse:
    """Analyze an uploaded APK and return metadata and a fake score.

    Parameters
    ----------
    apk_file:
        The uploaded APK file.
    real_name:
        The official/legitimate app name that the candidate might be
        impersonating. Used for text-based risk scoring.
    reference_icon_path:
        Filesystem path to the reference icon image corresponding to the
        legitimate app. If provided and the APK contains an icon, icon-based
        similarity is computed.

    Returns
    -------
    JSONResponse
        JSON payload including extracted metadata, individual risk signals,
        and the aggregate fake score.
    """

    # Persist the uploaded APK to a temporary file so androguard can read it.
    try:
        contents = await apk_file.read()
    except Exception as exc:  # pragma: no cover - I/O issues
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded APK: {exc}")

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded APK file is empty.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".apk") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        metadata: Dict[str, Any] = extract_apk_data(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                # Not fatal if the temp file cannot be removed.
                pass

    # Extract individual fields for JSON and scoring.
    app_name = metadata.get("app_name")
    icon_bytes = metadata.get("icon_data")

    # Text-based risk (0-100). If no real_name is provided, treat as 0 risk.
    text_risk: float = 0.0
    if real_name:
        try:
            text_risk = float(calculate_text_risk(app_name, real_name))
        except RuntimeError as exc:  # thefuzz not installed
            raise HTTPException(status_code=500, detail=str(exc))

    # Icon-based risk (0-100) based on phash similarity.
    icon_risk: float = 0.0
    if icon_bytes and reference_icon_path:
        try:
            icon_risk = float(
                calculate_icon_similarity(icon_bytes=icon_bytes, reference_image_path=reference_icon_path)
            )
        except RuntimeError as exc:  # imagehash not installed
            raise HTTPException(status_code=500, detail=str(exc))

    # Aggregate fake score as the simple average of available risks.
    fake_score = calculate_fake_score([text_risk, icon_risk])

    # Prepare JSON-safe metadata (bytes must be encoded).
    icon_b64: Optional[str]
    if icon_bytes is not None:
        icon_b64 = base64.b64encode(icon_bytes).decode("ascii")
    else:
        icon_b64 = None

    response_payload = {
        "metadata": {
            "app_name": app_name,
            "package_name": metadata.get("package_name"),
            "permissions": metadata.get("permissions", []),
            "certificate_hash": metadata.get("certificate_hash"),
            "icon_data_base64": icon_b64,
        },
        "risks": {
            "text_risk": text_risk,
            "icon_risk": icon_risk,
        },
        "fake_score": fake_score,
    }

    return JSONResponse(content=response_payload)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Simple health-check endpoint."""

    return {"status": "ok", "service": "brandguard-hackathon-api"}
