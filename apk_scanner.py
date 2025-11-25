"""APK scanning utilities using androguard."""
from __future__ import annotations
import logging
import os
import hashlib
from typing import Any, Dict, List, Optional

# --- SMART IMPORT BLOCK (Handles both Old and New Androguard) ---
try:
    # Try New Androguard (v4+)
    from androguard.core.apk import APK
    ANDROGUARD_IMPORT_ERROR = None
except ImportError:
    try:
        # Try Old Androguard (v3)
        from androguard.core.bytecodes.apk import APK
        ANDROGUARD_IMPORT_ERROR = None
    except ImportError as exc:
        # Failed both
        APK = None
        ANDROGUARD_IMPORT_ERROR = exc
# -------------------------------------------------------------

logger = logging.getLogger(__name__)

def extract_apk_data(apk_path: str) -> Dict[str, Any]:
    # Default empty result
    result = {
        "app_name": None,
        "package_name": None,
        "permissions": [],
        "icon_data": None,
        "certificate_hash": None,
    }

    # 1. Check if Androguard loaded correctly
    if ANDROGUARD_IMPORT_ERROR or APK is None:
        logger.error("Androguard load error. Please install: pip install androguard")
        return result

    # 2. Check file existence
    if not os.path.exists(apk_path):
        return result

    try:
        # 3. Load APK
        apk = APK(apk_path)

        # 4. Extract Metadata safely
        try: result["app_name"] = apk.get_app_name()
        except: pass

        try: result["package_name"] = apk.get_package()
        except: pass

        try: 
            perms = apk.get_permissions()
            result["permissions"] = list(perms) if perms else []
        except: pass

        # 5. Extract Icon
        try:
            icon_name = apk.get_app_icon()
            if icon_name:
                result["icon_data"] = apk.get_file(icon_name)
        except: pass

        # 6. Extract Certificate (New & Old Version Compatible)
        try:
            certs = apk.get_certificates()
            if certs:
                cert = certs[0]
                # Try getting SHA256 (works on new androguard)
                sha = getattr(cert, "sha256_fingerprint", None) or getattr(cert, "sha256", None)
                
                if sha:
                    # Clean up the format
                    result["certificate_hash"] = str(sha).replace(":", "").lower()
                else:
                    # Fallback for very old androguard
                    result["certificate_hash"] = hashlib.sha256(cert.get_raw()).hexdigest()
        except: pass

    except Exception as e:
        logger.error(f"Critical Error parsing APK: {e}")

    return result