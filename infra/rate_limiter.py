"""In-process sliding window rate limiter keyed by user UID."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict


class RateLimiter:
    """Sliding window counter — max_requests per window_seconds per user.

    Set max_requests=0 to disable limiting entirely (useful for tests).
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, user_uid: str) -> tuple[bool, int]:
        """Check if user can make a request.

        Returns:
            (allowed, retry_after_seconds) — retry_after is 0 when allowed.
        """
        if self._max == 0:
            return True, 0  # disabled

        now = time.time()
        with self._lock:
            # Evict timestamps outside the current window
            self._requests[user_uid] = [
                t for t in self._requests[user_uid] if now - t < self._window
            ]
            if len(self._requests[user_uid]) >= self._max:
                oldest = self._requests[user_uid][0]
                retry_after = int(self._window - (now - oldest)) + 1
                return False, retry_after
            self._requests[user_uid].append(now)
            return True, 0

    def reset(self) -> None:
        """Clear all recorded request timestamps — for test isolation only."""
        with self._lock:
            self._requests.clear()


_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Return the module-level RateLimiter singleton, creating it once.

    Rate limiting is disabled (max_requests=0) when GOOGLE_AUTH_ENABLED is
    not set — covers local dev and CI where all requests share the dev uid.
    Set RATE_LIMIT_RPM env var to override the default of 5 in production.
    """
    global _limiter
    if _limiter is None:
        auth_on = os.getenv("GOOGLE_AUTH_ENABLED", "").lower() in ("true", "1", "yes")
        max_rpm = int(os.getenv("RATE_LIMIT_RPM", "5")) if auth_on else 0
        _limiter = RateLimiter(max_requests=max_rpm, window_seconds=60)
    return _limiter


def reset_limiter() -> None:
    """Reset the singleton for test isolation. Do not call in production."""
    global _limiter
    _limiter = None
