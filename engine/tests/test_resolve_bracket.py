"""
Testes da auto-resolução do chaveamento (resolve_bracket.py) — a peça que hoje vai gerar QF-04
sozinha assim que as duas oitavas de hoje (Argentina×Egito, Suíça×Colômbia) terminarem. Antes
disso só a lista SPECIAL_SLOTS era validada (indiretamente, via test_knockout.py); a função
resolve() em si nunca tinha teste direto. Roda: cd engine && python3 -m pytest tests -q
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import resolve_bracket as RB


def _setup(monkeypatch, tmp_path, bracket, fixtures):
    """Isola resolve() dos arquivos reais e da rede (ESPN) — testes não tocam em produção."""
    bracket_path = tmp_path / "knockout_bracket.json"
    fix_path = tmp_path / "knockout_fixtures.json"
    bracket_path.write_text(json.dumps(bracket), encoding="utf-8")
    fix_path.write_text(json.dumps(fixtures), encoding="utf-8")
    monkeypatch.setattr(RB, "BRACKET", str(bracket_path))
    monkeypatch.setattr(RB, "FIX", str(fix_path))
    monkeypatch.setattr(RB, "_espn_kickoffs", lambda: {})


def test_so_gera_quando_os_dois_alimentadores_tem_vencedor(monkeypatch, tmp_path):
    bracket = {"R16": [{"slot": "R16-01", "home": "A", "away": "B"},
                        {"slot": "R16-02", "home": "C", "away": "D"}]}
    fixtures = {
        "R16-01": {"home": "A", "away": "B", "winner": "A"},
        "R16-02": {"home": "C", "away": "D", "winner": None},   # ainda não terminou
    }
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    _, new = RB.resolve()
    assert new == []   # QF-01 precisa dos DOIS vencedores; só tem 1


def test_gera_com_mandante_correto_e_special_flag(monkeypatch, tmp_path):
    bracket = {"R16": [{"slot": "R16-03", "home": "E", "away": "F"},
                        {"slot": "R16-04", "home": "G", "away": "H"}]}
    fixtures = {
        "R16-03": {"home": "E", "away": "F", "winner": "F"},
        "R16-04": {"home": "G", "away": "H", "winner": "G"},
    }
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    new_bracket, new = RB.resolve()
    assert new == [("QF", "QF-02", "F", "G")]   # mandante = venc(R16-03), o ÍMPAR
    assert new_bracket["QF"][0] == {"slot": "QF-02", "home": "F", "away": "G",
                                     "kickoff": None, "special": True}   # QF-02 ∈ SPECIAL_SLOTS


def test_idempotente_nunca_sobrescreve_slot_existente(monkeypatch, tmp_path):
    bracket = {"QF": [{"slot": "QF-01", "home": "França", "away": "Marrocos",
                        "kickoff": None, "special": False}]}
    fixtures = {
        "R16-01": {"home": "X", "away": "Y", "winner": "X"},   # sugeriria QF-01 = X×Y
        "R16-02": {"home": "Z", "away": "W", "winner": "Z"},
    }
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    new_bracket, new = RB.resolve()
    assert new == []   # QF-01 já existe -> não mexe, mesmo com dado novo nos alimentadores
    assert new_bracket["QF"][0]["home"] == "França"


def test_cenario_de_hoje_QF04_entra_na_lista_QF_ja_existente(monkeypatch, tmp_path):
    # Espelha o estado real: QF-01/02/03 já resolvidos; R16-07/08 (jogos de hoje) acabam de
    # terminar. QF-04 = venc(R16-07) × venc(R16-08), mandante = venc(R16-07) (ímpar), special=True.
    bracket = {
        "R16": [{"slot": f"R16-{i:02d}", "home": "x", "away": "y"} for i in range(1, 9)],
        "QF": [
            {"slot": "QF-01", "home": "França", "away": "Marrocos", "kickoff": None, "special": False},
            {"slot": "QF-02", "home": "Espanha", "away": "Bélgica", "kickoff": "2026-07-10T19:00Z", "special": True},
            {"slot": "QF-03", "home": "Noruega", "away": "Inglaterra", "kickoff": "2026-07-11T21:00Z", "special": False},
        ],
    }
    fixtures = {
        f"R16-{i:02d}": {"home": "x", "away": "y", "winner": "x"} for i in range(1, 7)
    }
    fixtures["R16-07"] = {"home": "Argentina", "away": "Egito", "winner": "Argentina"}
    fixtures["R16-08"] = {"home": "Suíça", "away": "Colômbia", "winner": "Colômbia"}
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    new_bracket, new = RB.resolve()
    assert new == [("QF", "QF-04", "Argentina", "Colômbia")]
    assert len(new_bracket["QF"]) == 4   # anexou ao array QF existente, não substituiu
    assert new_bracket["QF"][3] == {"slot": "QF-04", "home": "Argentina", "away": "Colômbia",
                                     "kickoff": None, "special": True}


def test_terceiro_lugar_vem_dos_PERDEDORES_das_semis(monkeypatch, tmp_path):
    bracket = {}
    fixtures = {
        "SF-01": {"home": "A", "away": "B", "winner": "A"},   # perdedor = B
        "SF-02": {"home": "C", "away": "D", "winner": "D"},   # perdedor = C
    }
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    new_bracket, new = RB.resolve()
    ter = [n for n in new if n[1] == "TER"]
    assert ter == [("TER", "TER", "B", "C")]
    assert new_bracket["TER"][0]["special"] is True   # TER ∈ SPECIAL_SLOTS


def test_sem_vencedores_nao_faz_nada(monkeypatch, tmp_path):
    bracket = {}
    fixtures = {"R16-01": {"home": "A", "away": "B", "winner": None}}
    _setup(monkeypatch, tmp_path, bracket, fixtures)
    new_bracket, new = RB.resolve()
    assert new == [] and new_bracket == {}
