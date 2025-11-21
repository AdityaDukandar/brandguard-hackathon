"""Icon similarity engine using perceptual hashing.

This module compares app icons using the `imagehash` library and Pillow.
It exposes `calculate_icon_similarity`, which returns a similarity
percentage (0-100), where 100 means identical perceptual hashes.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Optional

from PIL import Image

try:  # Import imagehash with a clear failure mode if missing.
    import imagehash
except ImportError as exc:  # pragma: no cover - environment/config error
    imagehash = None  # type: ignore[assignment]
    IMAGEHASH_IMPORT_ERROR = exc
else:
    IMAGEHASH_IMPORT_ERROR = None


logger = logging.getLogger(__name__)


def _load_image_from_bytes(data: bytes) -> Image.Image:
    """Load a PIL Image from raw bytes.

    The image is converted to RGB to normalize color mode differences.
    """

    with BytesIO(data) as bio:
        img = Image.open(bio)
        return img.convert("RGB")


def _load_image_from_path(path: str) -> Image.Image:
    """Load a PIL Image from a filesystem path and normalize to RGB."""

    img = Image.open(path)
    return img.convert("RGB")


def calculate_icon_similarity(icon_bytes: Optional[bytes], reference_image_path: str) -> float:
    """Compare an in-memory icon image against a reference image on disk.

    Parameters
    ----------
    icon_bytes:
        Raw bytes of the candidate icon (e.g., from an APK).
    reference_image_path:
        Filesystem path to the reference icon image.

    Returns
    -------
    float
        Similarity percentage in the range [0.0, 100.0]. A value of 100.0
        represents a perfect match (phash difference of 0).

    Notes
    -----
    - Uses `imagehash.phash` for perceptual hashing.
    - If loading or hashing fails for any reason, this function logs the
      error and returns 0.0 rather than raising.
    """

    if icon_bytes is None:
        logger.warning("No icon bytes provided; returning similarity=0.0")
        return 0.0

    if IMAGEHASH_IMPORT_ERROR is not None or imagehash is None:  # pragma: no cover
        raise RuntimeError(
            "imagehash is not installed. Install it with 'pip install imagehash' "
            "to enable icon similarity scoring."
        ) from IMAGEHASH_IMPORT_ERROR

    try:
        candidate_img = _load_image_from_bytes(icon_bytes)
        reference_img = _load_image_from_path(reference_image_path)

        hash_candidate = imagehash.phash(candidate_img)
        hash_reference = imagehash.phash(reference_img)

        # Hamming distance between the hashes; 0 means identical.
        diff = hash_candidate - hash_reference

        # The number of bits in the hash matrix (e.g., 8x8=64 for default phash).
        max_diff = hash_candidate.hash.size or 1
        similarity = max(0.0, 1.0 - (diff / float(max_diff)))

        return round(similarity * 100.0, 2)
    except Exception:  # pragma: no cover - robustness for unexpected image issues
        logger.exception(
            "Failed to compute icon similarity for reference '%s'", reference_image_path
        )
        return 0.0
