"""
_read_form_source (build_data.py) — achado real de 07/jul: uma URL de CSV mal configurada
(planilha não publicada/compartilhada) devolve 200 com a TELA DE LOGIN do Google em vez de
erro. Sem detectar isso, parse_form_csv não acha cabeçalho reconhecido e a rodada de mata-mata
fica muda em silêncio (nenhum aviso aponta a causa). Rode: cd engine && python3 -m pytest tests -q
"""
import os
import sys
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_data as BD


class _FakeResp:
    def __init__(self, url, body):
        self._url = url
        self._body = body.encode("utf-8")

    def geturl(self):
        return self._url

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(final_url, body):
    return lambda *a, **kw: _FakeResp(final_url, body)


def test_redirect_para_login_do_google_retorna_none(monkeypatch, capsys):
    monkeypatch.setattr(urllib.request, "urlopen",
                         _fake_urlopen("https://accounts.google.com/ServiceLogin?...", "qualquer coisa"))
    assert BD._read_form_source("http://exemplo.com/csv") is None
    assert "login" in capsys.readouterr().out.lower()   # avisa alto, não fica mudo


def test_html_no_lugar_do_csv_retorna_none(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen",
                         _fake_urlopen("http://exemplo.com/csv", "<!DOCTYPE html><html>erro</html>"))
    assert BD._read_form_source("http://exemplo.com/csv") is None


def test_csv_real_passa_direto(monkeypatch):
    csv_real = "Timestamp,1) Sua aposta (escolha seu APELIDO),Jogo 1 — A × B\n2026-07-07,Fulano,1 × 0\n"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen("http://exemplo.com/csv", csv_real))
    assert BD._read_form_source("http://exemplo.com/csv") == csv_real


def test_erro_de_rede_ainda_retorna_none_sem_lancar(monkeypatch):
    def _raise(*a, **kw):
        raise OSError("timeout")
    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    assert BD._read_form_source("http://exemplo.com/csv") is None


def test_arquivo_local_nao_e_afetado(tmp_path):
    f = tmp_path / "respostas.csv"
    f.write_text("Timestamp,Apelido\n", encoding="utf-8")
    assert BD._read_form_source(str(f)) == "Timestamp,Apelido\n"
