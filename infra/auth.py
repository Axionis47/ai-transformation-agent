"""Verify Google OAuth tokens from Firebase Auth."""

from __future__ import annotations

import os
from functools import lru_cache

_FIREBASE_ENABLED = os.getenv("FIREBASE_AUTH_ENABLED", "").lower() in ("true", "1", "yes")
_API_KEY = os.getenv("API_KEY", "")


def verify_google_token(token: str) -> dict | None:
    """Verify a Firebase ID token. Returns decoded claims or None if invalid.

    Claims include: uid, email, name, picture, etc.
    When FIREBASE_AUTH_ENABLED is not set, always returns None (skipped).
    """
    if not _FIREBASE_ENABLED:
        return None

    try:
        import firebase_admin  # noqa: PLC0415
        from firebase_admin import auth as firebase_auth  # noqa: PLC0415

        _get_firebase_app()

        decoded = firebase_auth.verify_id_token(token)
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email", ""),
            "name": decoded.get("name", ""),
        }
    except Exception:
        return None


@lru_cache(maxsize=1)
def _get_firebase_app():
    """Initialize Firebase Admin SDK once via Application Default Credentials."""
    import firebase_admin  # noqa: PLC0415
    from firebase_admin import credentials  # noqa: PLC0415

    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.ApplicationDefault()
        return firebase_admin.initialize_app(
            cred,
            {"projectId": os.getenv("GCP_PROJECT_ID", "plotpointe")},
        )


def get_user_from_request(authorization: str | None) -> dict | None:
    """Extract user identity from Authorization or X-API-Key headers.

    Auth precedence (first match wins):
      1. FIREBASE_AUTH_ENABLED=true  -> require Bearer token
      2. API_KEY set                 -> require X-API-Key header
      3. Neither configured          -> open access, return anonymous

    Returns a user dict or None. None signals the caller to raise 401.
    """
    # Open access when neither auth mechanism is configured
    if not _FIREBASE_ENABLED and not _API_KEY:
        return {"email": "anonymous", "name": "Anonymous", "uid": "anonymous"}

    # Firebase Bearer token path
    if _FIREBASE_ENABLED:
        if not authorization or not authorization.startswith("Bearer "):
            return None
        token = authorization[7:]
        return verify_google_token(token)

    # API key path (Firebase disabled, but API_KEY is set)
    return None  # caller must check X-API-Key separately via _verify_api_key
