"""
In-memory sliding-window rate limiter for login attempts.

Trade-offs:
- Single-process only (won't work across multiple backend replicas).
  Fine for our single-VM deployment; revisit with Redis if we ever scale out.
- Memory grows with unique keys but self-cleans as old entries slide out.
- Survives nothing — restart clears all counters, which is acceptable for
  a brute-force defense (attackers can't exploit a restart they don't know about).
"""

import threading
import time
from collections import defaultdict, deque

_WINDOW_SECONDS  = 15 * 60   # 15 minutes
_MAX_ATTEMPTS    = 5         # fail-fast after this many bad tries

_attempts: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def _trim(key: str, now: float) -> None:
    """Drop entries older than the sliding window."""
    dq = _attempts[key]
    cutoff = now - _WINDOW_SECONDS
    while dq and dq[0] < cutoff:
        dq.popleft()


def check(key: str) -> tuple[bool, int]:
    """
    Should this request be allowed?
    Returns (allowed, retry_after_seconds_if_denied).
    """
    now = time.time()
    with _lock:
        _trim(key, now)
        dq = _attempts[key]
        if len(dq) >= _MAX_ATTEMPTS:
            oldest = dq[0]
            retry_after = int(_WINDOW_SECONDS - (now - oldest)) + 1
            return False, max(retry_after, 1)
        return True, 0


def register_failure(key: str) -> None:
    """Record a failed attempt so it counts towards the limit."""
    with _lock:
        _attempts[key].append(time.time())


def clear(key: str) -> None:
    """Wipe the counter for a key (e.g. on a successful login)."""
    with _lock:
        _attempts.pop(key, None)
