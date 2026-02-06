import time
from collections import deque
from threading import Lock
from typing import Deque, Dict, Tuple

_BUCKETS: Dict[str, Deque[float]] = {}
_LOCK = Lock()

def rl_check(key: str, max_hits: int, window_sec: int) -> Tuple[bool, int]:
    """Retorna (allowed, retry_after_seconds)."""
    now = time.monotonic()
    if max_hits <= 0 or window_sec <= 0:
        return True, 0

    with _LOCK:
        q = _BUCKETS.get(key)
        if q is None:
            q = deque()
            _BUCKETS[key] = q

        cutoff = now - window_sec
        while q and q[0] <= cutoff:
            q.popleft()

        if len(q) >= max_hits:
            retry_after = int(max(1, window_sec - (now - q[0])))
            return False, retry_after

        q.append(now)
        return True, 0


def rl_peek(key: str, max_hits: int, window_sec: int) -> Tuple[bool, int]:
    """Checa se está bloqueado SEM consumir tentativa."""
    now = time.monotonic()
    if max_hits <= 0 or window_sec <= 0:
        return True, 0

    with _LOCK:
        q = _BUCKETS.get(key)
        if q is None:
            return True, 0

        cutoff = now - window_sec
        while q and q[0] <= cutoff:
            q.popleft()

        if len(q) >= max_hits:
            retry_after = int(max(1, window_sec - (now - q[0])))
            return False, retry_after

        return True, 0

def rl_client_ip(request) -> str:
    # Railway/proxy normalmente manda X-Forwarded-For
    try:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    except Exception:
        pass

    try:
        if request.client and request.client.host:
            return str(request.client.host)
    except Exception:
        pass

    return "unknown"
