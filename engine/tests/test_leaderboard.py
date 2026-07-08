"""
Testes do leaderboard.build — o "miolo" de ranking/prêmio que faltava cobertura:
rank de competição (empate), prize_pos só entre pagantes, in_the_money (empate na borda),
Bom de Palpite (líder pagante + divide), e day_points (soma só os jogos da rodada).
Rode: cd engine && python3 -m pytest tests -q
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import leaderboard as L


def _build(specs, round_mids=frozenset()):
    """specs: dict alias -> {total, group_pts?, paid?, exact?, correct?, by_match?}.
    Constrói scored+roster mínimos e roda L.build (catálogo/resultados/facts vazios)."""
    scored, roster = [], {}
    for i, (a, d) in enumerate(specs.items()):
        scored.append({
            "alias": a, "total": d["total"], "group_pts": d.get("group_pts", d["total"]),
            "exact_scores": d.get("exact", 0), "correct_outcomes": d.get("correct", 0),
            "by_match": d.get("by_match", {}),
        })
        roster[a.lower()] = {"paid": d.get("paid", True), "order": i}
    out = L.build(scored, roster, [], {}, {}, {}, {}, round_mids)
    return {p["alias"]: p for p in out}


def test_rank_competicao_com_empate():
    r = _build({"A": {"total": 10}, "B": {"total": 8}, "C": {"total": 8}, "D": {"total": 5}})
    assert (r["A"]["rank"], r["B"]["rank"], r["C"]["rank"], r["D"]["rank"]) == (1, 2, 2, 4)


def test_in_the_money_empate_na_borda_inclui_todos():
    # 5 pagantes com empate no 4º lugar (ranks 1,2,2,4,4) → os 5 estão na grana
    r = _build({"A": {"total": 10}, "B": {"total": 8}, "C": {"total": 8},
                "D": {"total": 6}, "E": {"total": 6}})
    assert all(r[a]["in_the_money"] for a in "ABCDE")


def test_prize_pos_so_entre_pagantes_cafe_nao_ocupa_vaga():
    # café-com-leite no topo NÃO toma posição de prêmio nem entra na grana
    r = _build({"Cafe": {"total": 20, "paid": False}, "P1": {"total": 10}, "P2": {"total": 9}})
    assert r["Cafe"]["prize_pos"] is None and r["Cafe"]["in_the_money"] is False
    assert r["P1"]["prize_pos"] == 1 and r["P2"]["prize_pos"] == 2


def test_bom_palpite_e_lider_pagante_da_1a_fase():
    # café tem mais pontos de 1ª fase, mas o Bom de Palpite é o líder PAGANTE
    r = _build({"Cafe": {"total": 30, "group_pts": 30, "paid": False},
                "P1": {"total": 20, "group_pts": 20}, "P2": {"total": 18, "group_pts": 18}})
    assert r["Cafe"]["bom_palpite"] is False
    assert r["P1"]["bom_palpite"] is True and r["P1"]["bom_palpite_split"] is False


def test_bom_palpite_empate_divide():
    r = _build({"P1": {"total": 20, "group_pts": 20}, "P2": {"total": 19, "group_pts": 20},
                "P3": {"total": 5, "group_pts": 5}})
    assert r["P1"]["bom_palpite"] and r["P2"]["bom_palpite"]
    assert r["P1"]["bom_palpite_split"] and r["P2"]["bom_palpite_split"]


def test_day_points_soma_so_jogos_da_rodada():
    r = _build({"A": {"total": 10, "by_match": {"K1": 5, "L4": 3, "A1": 2}}},
               round_mids=frozenset({"K1", "L4"}))
    assert r["A"]["day_points"] == 8   # 5+3 (ignora A1, fora da rodada)


def test_phase1_rank_por_pontos_da_1a_fase():
    # rank da 1ª fase usa group_pts (não o total) e inclui todos
    r = _build({"A": {"total": 5, "group_pts": 30}, "B": {"total": 40, "group_pts": 10}})
    assert r["A"]["phase1_rank"] == 1 and r["B"]["phase1_rank"] == 2


def test_remaining_knockout_points_conta_so_slots_nao_encerrados():
    # BUG real corrigido (08/jul): antes disso era um buffer fixo (KNOCKOUT_POTENTIAL=250) que
    # NUNCA refletia o mata-mata de verdade. Slot normal aberto = 3+6=9; especial aberto = 5+6=11;
    # slot encerrado não conta mais nada (já virou pontuação real, não "potencial").
    ko_results = {
        "R32-01": {"status": "finished", "home_score": 1, "away_score": 0},   # encerrado -> não conta
        "R16-02": {"status": "scheduled", "home_score": None},               # especial (config.SPECIAL_SLOTS) aberto
        "QF-01": {"status": "scheduled", "home_score": None},                # normal aberto
    }
    got = L.remaining_knockout_points(ko_results)
    import config as C
    n_slots = len(C.KNOCKOUT_CELLS)
    # todo slot que NÃO é R32-01/R16-02/QF-01 também está "aberto" (dict não tem entrada = scheduled)
    especiais_abertos = sum(1 for slot, _, _ in C.KNOCKOUT_CELLS if slot != "R32-01" and slot in C.SPECIAL_SLOTS)
    normais_abertos = sum(1 for slot, _, _ in C.KNOCKOUT_CELLS if slot != "R32-01" and slot not in C.SPECIAL_SLOTS)
    esperado = especiais_abertos * (5 + 6) + normais_abertos * (3 + 6)
    assert got == esperado
    assert n_slots == 32   # sanity check da premissa (32 slots no chaveamento inteiro)


def test_eliminated_usa_pontos_reais_do_mata_mata_nao_buffer_fixo():
    # com o mata-mata TODO encerrado (nenhum ponto restante), quem está muito atrás do líder
    # e sem mais jogo de grupo é eliminado de verdade -- sem o antigo buffer de 250 escondendo isso.
    scored, roster = [], {}
    for i, (a, tot) in enumerate({"Lider": 300, "Ultimo": 10}.items()):
        scored.append({"alias": a, "total": tot, "group_pts": tot, "exact_scores": 0,
                      "correct_outcomes": 0, "by_match": {}})
        roster[a.lower()] = {"paid": True, "order": i}
    ko_results = {slot: {"status": "finished", "home_score": 0, "away_score": 0}
                 for slot, _, _ in __import__("config").KNOCKOUT_CELLS}
    out = {p["alias"]: p for p in L.build(scored, roster, [], {}, {"champion": "X"}, {}, {}, frozenset(),
                                          ko_results=ko_results)}
    assert out["Ultimo"]["eliminated"] is True
    assert out["Lider"]["eliminated"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
