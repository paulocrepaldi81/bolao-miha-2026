"""
Testes da leitura do CSV do Google Form (mata-mata) + placar efetivo (override/fallback).
Rode: cd engine && python3 -m pytest tests -q
"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import knockout as K

ROSTER = ["Ricardo Mihalik", "Paulo Crepaldi - Codex", "Tia Cleide"]
DEADLINE = datetime(2026, 6, 28, 12, 0, 0)   # R32: dom 28/06 12h

# CSV simulando a exportação do Google Forms (cabeçalho pt-BR + 'Jogo N — A × B')
CSV = (
    "Carimbo de data/hora,Seu nome e sobrenome,Seu apelido,"
    "Jogo 1 — Brasil × Senegal,Jogo 2 — França × Marrocos,Jogo 3 — Argentina × Austrália,"
    "Marcou 'Outro placar'?\n"
    # Ricardo: 1º envio (vale o último abaixo)
    "27/06/2026 10:00:00,Ricardo M,Ricardo Mihalik,1 × 0,,2 × 2,\n"
    # Ricardo: 2º envio, mais tarde e DENTRO do prazo -> vence
    "28/06/2026 11:45:03,Ricardo M,Ricardo Mihalik,3 × 0,1 × 1,,\n"
    # Paulo: envio DEPOIS do prazo -> descartado
    "28/06/2026 12:30:00,Paulo,Paulo Crepaldi - Codex,2 × 1,2 × 0,1 × 0,\n"
    # apelido desconhecido -> ignorado
    "27/06/2026 09:00:00,Zé,Apelido Inexistente,1 × 1,1 × 1,1 × 1,\n"
    # Cleide: placar com 'x' minúsculo + 'Outro placar' (sem override) + em branco
    "27/06/2026 20:00:00,Tia Cleide,Tia Cleide,2 x 1,Outro placar (digo no fim),,Jogo 2 = 5x1\n"
)


def _parse():
    return K.parse_form_csv(CSV, "R32", DEADLINE, ROSTER)


def test_vale_o_ultimo_envio_dentro_do_prazo():
    r = _parse()
    assert r["Ricardo Mihalik"]["R32-01"] == (3, 0)      # 2º envio (3x0) venceu o 1º (1x0)
    assert r["Ricardo Mihalik"]["R32-02"] == (1, 1)      # só veio no 2º envio
    assert "R32-03" not in r["Ricardo Mihalik"]          # ficou em branco no envio vencedor


def test_trava_por_prazo_descarta_envio_atrasado():
    assert "Paulo Crepaldi - Codex" not in _parse()      # enviou 12h30 > prazo 12h


def test_apelido_desconhecido_ignorado():
    assert "Apelido Inexistente" not in _parse()


def test_x_minusculo_e_outro_placar_e_branco():
    r = _parse()
    assert r["Tia Cleide"]["R32-01"] == (2, 1)           # "2 x 1" aceito
    assert "R32-02" not in r["Tia Cleide"]               # "Outro placar" = sem override (vai pro fallback)
    assert "R32-03" not in r["Tia Cleide"]               # em branco = sem override


def test_effective_picks_override_vence_fallback():
    orig = {"R32-01": [1, 2], "R32-02": [0, 0], "R32-03": [2, 1]}   # da planilha (listas, como no JSON)
    form = {"R32-01": (3, 0), "R32-02": (1, 1)}                     # atualizou 2; deixou R32-03
    eff = K.effective_picks(orig, form)
    assert eff["R32-01"] == (3, 0)   # override do Form
    assert eff["R32-02"] == (1, 1)   # override do Form
    assert eff["R32-03"] == (2, 1)   # fallback da aposta original


def test_score_knockout():
    import scoring as S
    eff = {"R32-01": (2, 1), "R32-02": (0, 0), "R16-01": (1, 1)}
    res = {
        "R32-01": {"home_score": 2, "away_score": 1, "status": "finished"},                  # exato -> 3 + 3 gols = 6
        "R32-02": {"home_score": 1, "away_score": 0, "status": "finished", "special": True},  # previu empate, deu vitória -> 0
        "R16-01": {"home_score": 1, "away_score": 1, "status": "finished"},                   # empate exato -> 3 + 2 = 5
        "QF-01":  {"home_score": 3, "away_score": 0, "status": "finished"},                   # sem palpite -> ignora
        "SF-01":  {"home_score": None, "away_score": None, "status": "scheduled"},            # não disputado -> ignora
    }
    total, by = S.score_knockout(eff, res)
    assert by["R32-01"] == 6 and by["R32-02"] == 0 and by["R16-01"] == 5
    assert "QF-01" not in by and "SF-01" not in by
    assert total == 11


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
