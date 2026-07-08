"""
load_espn_events (fetch_results.py) — cache compartilhado da ESPN DENTRO de uma rodada do robô.
Antes, fetch_results/fetch_knockout/fetch_facts cada um batia na API pro MESMO instante (9
chamadas por rodada) e podiam ver 3 "agoras" diferentes se um placar mudasse no meio da rodada.
Rode: cd engine && python3 -m pytest tests -q
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_results as FR


class _FakeResp:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(events_per_call):
    """events_per_call: lista de listas de eventos, uma por janela (WINDOWS) — cada chamada
    consome a próxima da fila, assim dá pra contar quantas vezes a rede foi realmente batida."""
    calls = []

    def _open(req, timeout=30):
        calls.append(req)
        idx = len(calls) - 1
        return _FakeResp({"events": events_per_call[idx % len(events_per_call)]})
    return _open, calls


def test_sem_cache_busca_ao_vivo_e_grava(tmp_path, monkeypatch):
    cache = tmp_path / "espn_events_cache.json"
    monkeypatch.setattr(FR, "ESPN_CACHE", str(cache))
    opener, calls = _fake_urlopen([[{"id": "1"}]])
    monkeypatch.setattr(urllib.request, "urlopen", opener)
    events = FR.load_espn_events()
    assert events == [{"id": "1"}] * len(FR.WINDOWS)   # uma chamada por janela
    assert len(calls) == len(FR.WINDOWS)
    assert cache.exists()


def test_cache_fresco_evita_bater_na_rede_de_novo(tmp_path, monkeypatch):
    cache = tmp_path / "espn_events_cache.json"
    cache.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "events": [{"id": "cacheado"}],
    }), encoding="utf-8")
    monkeypatch.setattr(FR, "ESPN_CACHE", str(cache))

    def _boom(*a, **kw):
        raise AssertionError("não deveria bater na rede com cache fresco")
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    assert FR.load_espn_events() == [{"id": "cacheado"}]


def test_cache_velho_busca_ao_vivo_de_novo(tmp_path, monkeypatch):
    cache = tmp_path / "espn_events_cache.json"
    velho = datetime.now(timezone.utc) - timedelta(seconds=999)
    cache.write_text(json.dumps({"fetched_at": velho.isoformat(), "events": [{"id": "velho"}]}),
                     encoding="utf-8")
    monkeypatch.setattr(FR, "ESPN_CACHE", str(cache))
    opener, calls = _fake_urlopen([[{"id": "fresco"}]])
    monkeypatch.setattr(urllib.request, "urlopen", opener)
    events = FR.load_espn_events()
    assert events == [{"id": "fresco"}] * len(FR.WINDOWS)
    assert len(calls) == len(FR.WINDOWS)


def test_cache_corrompido_nao_derruba_busca_ao_vivo(tmp_path, monkeypatch):
    cache = tmp_path / "espn_events_cache.json"
    cache.write_text("{ isso não é json válido", encoding="utf-8")
    monkeypatch.setattr(FR, "ESPN_CACHE", str(cache))
    opener, calls = _fake_urlopen([[{"id": "1"}]])
    monkeypatch.setattr(urllib.request, "urlopen", opener)
    events = FR.load_espn_events()
    assert len(calls) == len(FR.WINDOWS)
    assert events == [{"id": "1"}] * len(FR.WINDOWS)
