"""
Limiter manual em memória (app/utils/rate_limit.py): semântica de
rl_check/rl_peek e remoção (eviction) de buckets expirados.

Contrato de eviction esperado:
  - chaves cujas batidas já saíram da janela são removidas de _BUCKETS
    por uma varredura periódica, disparada por chamadas posteriores
    (qualquer chave) depois de passado o intervalo de varredura (≤ 60 s);
  - chaves ainda ativas nunca são removidas, inclusive quando convivem
    janelas diferentes (a varredura não pode usar a menor janela);
  - rl_peek nunca cria chave e descarta a chave cujo deque ficou vazio;
  - _BUCKETS é sempre o mesmo objeto (nunca reatribuído).

Características já existentes (devem continuar valendo):
  - rl_check bloqueado não registra batida; retry_after ∈ [1, janela];
  - o limite é exato (max_hits permitidos, o seguinte bloqueia) e libera
    depois da janela;
  - sob concorrência, exatamente max_hits chamadas passam.

Estratégia: chamadas reais a rl_check/rl_peek com relógio falso
(monkeypatch de rate_limit.time). A base do relógio cresce a cada teste
e fica acima de qualquer time.monotonic() real, para que o estado de
varredura deixado por um teste nunca "adie" a varredura do seguinte.
Só chaves com prefixo "test-rl:" são criadas, e são limpas ao final.
"""
import itertools
import threading
from types import SimpleNamespace

import pytest

from app.utils import rate_limit
from app.utils.rate_limit import rl_check, rl_peek

PREFIX = "test-rl:"
PAST_SWEEP = 120  # folga acima do intervalo de varredura (≤ 60 s)

_BASES = itertools.count(1)


class FakeClock:
    def __init__(self, start: float):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _test_keys():
    return [k for k in rate_limit._BUCKETS if k.startswith(PREFIX)]


def _clear_test_keys():
    with rate_limit._LOCK:
        for key in _test_keys():
            rate_limit._BUCKETS.pop(key, None)


@pytest.fixture()
def clock(monkeypatch):
    _clear_test_keys()
    fake = FakeClock(start=1e9 + next(_BASES) * 1e6)
    monkeypatch.setattr(rate_limit, "time", SimpleNamespace(monotonic=fake))
    try:
        yield fake
    finally:
        _clear_test_keys()


def _trigger_sweep():
    # Chamada comum numa chave nova: é o que dispara a varredura periódica.
    rl_check(PREFIX + "trigger", 1000, 60)


def test_expired_key_is_removed_after_sweep_interval(clock):
    key = PREFIX + "expired"
    assert rl_check(key, 5, 10) == (True, 0)
    assert key in rate_limit._BUCKETS

    clock.advance(PAST_SWEEP)
    _trigger_sweep()

    assert key not in rate_limit._BUCKETS


def test_active_key_survives_sweep(clock):
    key = PREFIX + "active"
    assert rl_check(key, 5, 600) == (True, 0)

    clock.advance(PAST_SWEEP)
    _trigger_sweep()

    assert key in rate_limit._BUCKETS
    assert len(rate_limit._BUCKETS[key]) == 1


def test_mixed_windows_long_window_key_is_not_evicted_early(clock):
    short_key = PREFIX + "short"
    long_key = PREFIX + "long"
    assert rl_check(short_key, 5, 10) == (True, 0)
    assert rl_check(long_key, 1, 300) == (True, 0)

    clock.advance(PAST_SWEEP)
    _trigger_sweep()

    # Chave de janela longa segue ativa e continua bloqueando.
    assert long_key in rate_limit._BUCKETS
    allowed, retry_after = rl_check(long_key, 1, 300)
    assert allowed is False
    assert retry_after == 300 - PAST_SWEEP

    # Chave de janela curta já expirou e deve ter sido removida.
    assert short_key not in rate_limit._BUCKETS


def test_rl_peek_never_creates_key_and_drops_empty_bucket(clock):
    missing = PREFIX + "peek-missing"
    assert rl_peek(missing, 5, 60) == (True, 0)
    assert missing not in rate_limit._BUCKETS

    key = PREFIX + "peek-expired"
    assert rl_check(key, 5, 10) == (True, 0)
    clock.advance(11)

    assert rl_peek(key, 5, 10) == (True, 0)
    assert key not in rate_limit._BUCKETS


def test_blocked_rl_check_does_not_append_and_retry_after_in_range(clock):
    key = PREFIX + "blocked"
    window = 60
    assert rl_check(key, 2, window) == (True, 0)
    clock.advance(5)
    assert rl_check(key, 2, window) == (True, 0)

    for step in range(5):
        clock.advance(3)
        allowed, retry_after = rl_check(key, 2, window)
        assert allowed is False
        assert 1 <= retry_after <= window
        assert len(rate_limit._BUCKETS[key]) == 2

    # Retry-After conta a partir da 1ª batida (t0): 60 - 20 = 40.
    assert retry_after == window - (5 + 3 * 5)


def test_limit_is_exact_and_frees_after_window(clock):
    key = PREFIX + "exact"
    assert rl_check(key, 2, 10) == (True, 0)
    assert rl_check(key, 2, 10) == (True, 0)
    allowed, retry_after = rl_check(key, 2, 10)
    assert allowed is False
    assert retry_after == 10
    assert rl_peek(key, 2, 10)[0] is False

    clock.advance(10)  # batida em t0 sai da janela exatamente em t0+10
    assert rl_peek(key, 2, 10) == (True, 0)
    assert rl_check(key, 2, 10) == (True, 0)


def test_concurrent_rl_check_allows_exactly_max_hits(clock):
    key = PREFIX + "concurrent"
    max_hits = 10
    workers = 50
    barrier = threading.Barrier(workers)
    results = []
    results_lock = threading.Lock()

    def worker():
        barrier.wait()
        allowed, _ = rl_check(key, max_hits, 60)
        with results_lock:
            results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(results) == workers
    assert results.count(True) == max_hits
    assert len(rate_limit._BUCKETS[key]) == max_hits


def test_many_expired_keys_are_evicted(clock):
    total = 10_000
    for i in range(total):
        rl_check(f"{PREFIX}bulk:{i}", 5, 10)
    assert len(_test_keys()) == total
    size_before = len(rate_limit._BUCKETS)

    clock.advance(PAST_SWEEP)
    _trigger_sweep()

    assert [k for k in _test_keys() if k.startswith(PREFIX + "bulk:")] == []
    assert len(rate_limit._BUCKETS) < size_before - total + 10


def test_buckets_dict_identity_is_preserved(clock):
    buckets_id = id(rate_limit._BUCKETS)

    rl_check(PREFIX + "identity", 5, 10)
    clock.advance(PAST_SWEEP)
    _trigger_sweep()
    rl_peek(PREFIX + "identity", 5, 10)

    assert id(rate_limit._BUCKETS) == buckets_id
