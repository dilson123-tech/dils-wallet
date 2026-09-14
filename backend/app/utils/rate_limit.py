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
    """
    Fonte do IP para o rate limit de login: SOMENTE request.client.host.

    Esta função deliberadamente NÃO lê X-Forwarded-For (nem qualquer
    outro header encaminhado) diretamente — usa apenas a identidade de
    cliente já resolvida e exposta pelo servidor ASGI (Uvicorn/Starlette)
    em request.client.host. Qualquer confiança em headers de proxy deve
    acontecer na camada confiável do próprio servidor ASGI (ex.: uvicorn
    com uma allowlist de proxy configurada), nunca dentro desta função.

    Sem uma allowlist de proxy confiável configurada no app (fora do
    escopo desta correção), esta função não tenta interpretar headers
    encaminhados por conta própria: um header X-Forwarded-For pode ser
    definido livremente pelo próprio cliente na requisição, e usá-lo sem
    validar que a conexão realmente veio de um proxy confiável permitiria
    contornar o limite por-IP só variando o valor do header a cada
    tentativa. Confiar em request.client.host é a opção fail-safe: mais
    conservadora atrás de proxy, nunca menos segura que o comportamento
    anterior.
    """
    try:
        if request.client and request.client.host:
            return str(request.client.host)
    except Exception:
        pass

    return "unknown"
