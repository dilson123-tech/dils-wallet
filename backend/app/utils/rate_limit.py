import time
from collections import deque
from threading import Lock
from typing import Deque, Dict, Tuple

_BUCKETS: Dict[str, Deque[float]] = {}
_LOCK = Lock()

# Eviction: sem ela, cada chave vista (ex.: login:ident:{ip}:{ident})
# ficaria em _BUCKETS para sempre. A varredura roda no máximo uma vez por
# _SWEEP_INTERVAL_SEC, dentro de _LOCK, disparada pelas próprias chamadas.
# Cada chave guarda a maior janela com que já foi consultada, para que um
# bucket ainda ativo em alguma janela nunca seja removido antes da hora.
_SWEEP_INTERVAL_SEC = 60
_WINDOWS: Dict[str, int] = {}
_LAST_SWEEP = 0.0


def _drop(key: str) -> None:
    _BUCKETS.pop(key, None)
    _WINDOWS.pop(key, None)


def _maybe_sweep(now: float) -> None:
    """Remove buckets vazios ou totalmente expirados. Chamar com _LOCK."""
    global _LAST_SWEEP
    if now - _LAST_SWEEP < _SWEEP_INTERVAL_SEC:
        return
    _LAST_SWEEP = now

    expired = [
        key
        for key, q in _BUCKETS.items()
        if not q or q[-1] <= now - _WINDOWS.get(key, 0)
    ]
    for key in expired:
        _drop(key)

    # Janelas de chaves removidas de _BUCKETS por fora (ex.: limpeza em testes).
    for key in [k for k in _WINDOWS if k not in _BUCKETS]:
        del _WINDOWS[key]


def _track_window(key: str, window_sec: int) -> None:
    if window_sec > _WINDOWS.get(key, 0):
        _WINDOWS[key] = window_sec


def rl_check(key: str, max_hits: int, window_sec: int) -> Tuple[bool, int]:
    """Retorna (allowed, retry_after_seconds)."""
    now = time.monotonic()
    if max_hits <= 0 or window_sec <= 0:
        return True, 0

    with _LOCK:
        _maybe_sweep(now)

        q = _BUCKETS.get(key)
        if q is None:
            q = deque()
            _BUCKETS[key] = q
        _track_window(key, window_sec)

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
        _maybe_sweep(now)

        q = _BUCKETS.get(key)
        if q is None:
            return True, 0
        _track_window(key, window_sec)

        cutoff = now - window_sec
        while q and q[0] <= cutoff:
            q.popleft()

        if not q:
            _drop(key)
            return True, 0

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
