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

# Public so callers can phrase warnings like "X attempts remaining" without
# duplicating the magic numbers.
MAX_ATTEMPTS    = 7         # fail-fast after this many bad tries
WINDOW_SECONDS  = 3 * 60    # 3-minute sliding window
WARN_AFTER      = 3         # start surfacing remaining-attempts hints from this failure on

_attempts: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def _trim(key: str, now: float) -> None:
    """Drop entries older than the sliding window."""
    dq = _attempts[key]
    cutoff = now - WINDOW_SECONDS
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
        if len(dq) >= MAX_ATTEMPTS:
            oldest = dq[0]
            retry_after = int(WINDOW_SECONDS - (now - oldest)) + 1
            return False, max(retry_after, 1)
        return True, 0


def register_failure(key: str) -> int:
    """
    Record a failed attempt so it counts towards the limit.
    Returns the number of attempts still remaining in the current window
    (0 means the next attempt will be locked out).
    """
    with _lock:
        now = time.time()
        _attempts[key].append(now)
        _trim(key, now)
        return max(0, MAX_ATTEMPTS - len(_attempts[key]))


def clear(key: str) -> None:
    """Wipe the counter for a key (e.g. on a successful login)."""
    with _lock:
        _attempts.pop(key, None)
