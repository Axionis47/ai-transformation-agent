"""Google OAuth identity — single source of truth for all endpoints.

When GOOGLE_AUTH_ENABLED=true: requires Firebase Bearer token on protected routes.
When unset (local dev): returns a fixed dev user — never anonymous.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from fastapi import HTTPException

_GOOGLE_AUTH_ENABLED = os.getenv("GOOGLE_AUTH_ENABLED", "").lower() in ("true", "1", "yes")


@dataclass
class User:
    uid: str
    email: str
    name: str


_DEV_USER = User(uid="dev", email="dev@localhost", name="Developer")


def get_current_user(authorization: str | None) -> User:
    """Verify Bearer token and return User.

    Raises HTTPException(401) when auth is enabled and the token is missing
    or invalid. In local dev (GOOGLE_AUTH_ENABLED not set) always returns
    the dev user — never anonymous, never None.
    """
    if not _GOOGLE_AUTH_ENABLED:
        return _DEV_USER

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = authorization[7:]
    claims = _verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return User(
        uid=claims["uid"],
        email=claims.get("email", ""),
        name=claims.get("name", ""),
    )


def _verify_token(token: str) -> dict | None:
    """Verify a Firebase/Google ID token. Returns decoded claims or None."""
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
