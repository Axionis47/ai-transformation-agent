"""In-process sliding window rate limiter keyed by user UID."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict


class RateLimiter:
    """Sliding window counter — max_requests per window_seconds per user."""

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


_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Return the module-level RateLimiter singleton, creating it once."""
    global _limiter
    if _limiter is None:
        max_rpm = int(os.getenv("RATE_LIMIT_RPM", "5"))
        _limiter = RateLimiter(max_requests=max_rpm, window_seconds=60)
    return _limiter
