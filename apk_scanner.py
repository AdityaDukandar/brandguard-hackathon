"""APK scanning utilities using androguard.

This module exposes a single helper, `extract_apk_data`, which extracts
basic metadata and signing information from an APK.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

try:  # Import androguard lazily but fail fast with a clear message if missing.
    from androguard.core.bytecodes.apk import APK
except ImportError as exc:  # pragma: no cover - environment/config error
    APK = None  # type: ignore[assignment]
    ANDROGUARD_IMPORT_ERROR = exc
else:
    ANDROGUARD_IMPORT_ERROR = None


logger = logging.getLogger(__name__)


def extract_apk_data(apk_path: str) -> Dict[str, Any]:
    """Extract key metadata from an APK using androguard.

    Parameters
    ----------
    apk_path:
        Filesystem path to the APK file.

    Returns
    -------
    dict
        A dictionary with the following keys:

        - ``app_name`` (str | None)
        - ``package_name`` (str | None)
        - ``permissions`` (list[str])
        - ``icon_data`` (bytes | None)
        - ``certificate_hash`` (str | None)

    All keys are always present. When an error occurs or a field cannot be
    determined, the corresponding value is ``None`` (or ``[]`` for
    ``permissions``). Any exceptions are logged instead of being propagated.
    """

    result: Dict[str, Any] = {
        "app_name": None,
        "package_name": None,
        "permissions": [],  # type: List[str]
        "icon_data": None,  # type: Optional[bytes]
        "certificate_hash": None,
    }

    if ANDROGUARD_IMPORT_ERROR is not None or APK is None:  # pragma: no cover
        logger.error(
            "androguard is not installed. Install it with 'pip install androguard' "
            "to enable APK parsing.",
            exc_info=ANDROGUARD_IMPORT_ERROR,
        )
        return result

    if not os.path.exists(apk_path):
        logger.warning("APK file does not exist: %s", apk_path)
        return result

    try:
        apk = APK(apk_path)
    except Exception:  # pragma: no cover - covers corrupted APK / parsing errors
        logger.exception("Failed to initialize APK object for: %s", apk_path)
        return result

    # Basic metadata
    try:
        result["app_name"] = apk.get_app_name()  # type: ignore[attr-defined]
    except Exception:
        logger.exception("Failed to extract app_name from APK: %s", apk_path)

    try:
        result["package_name"] = apk.get_package()  # type: ignore[attr-defined]
    except Exception:
        logger.exception("Failed to extract package_name from APK: %s", apk_path)

    try:
        permissions = apk.get_permissions()  # type: ignore[attr-defined]
        if permissions is None:
            permissions = []
        result["permissions"] = list(permissions)
    except Exception:
        logger.exception("Failed to extract permissions from APK: %s", apk_path)

    # Icon bytes (if present)
    try:
        icon_name = apk.get_app_icon()  # type: ignore[attr-defined]
        if icon_name:
            try:
                icon_data = apk.get_file(icon_name)  # type: ignore[attr-defined]
                result["icon_data"] = icon_data
            except Exception:
                logger.exception("Failed to read icon bytes from APK: %s", apk_path)
    except Exception:
        logger.exception("Failed to resolve app icon from APK: %s", apk_path)

    # Certificate hash (SHA-256 if possible)
    try:
        certs = apk.get_certificates()  # type: ignore[attr-defined]
        if certs:
            cert = certs[0]
            sha256 = getattr(cert, "sha256_fingerprint", None)
            if sha256 is None:
                sha256 = getattr(cert, "sha256", None)

            if sha256 is not None:
                # In some androguard versions this is bytes, in others a hex string.
                if isinstance(sha256, bytes):
                    result["certificate_hash"] = sha256.hex()
                else:
                    result["certificate_hash"] = str(sha256)
            else:
                # Fallback: hash raw DER bytes if available.
                contents = getattr(cert, "contents", None)
                if contents is not None:
                    import hashlib

                    result["certificate_hash"] = hashlib.sha256(contents).hexdigest()
    except Exception:
        logger.exception("Failed to extract certificate hash from APK: %s", apk_path)

    return result
